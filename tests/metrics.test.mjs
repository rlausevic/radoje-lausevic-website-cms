import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {metrics} from '../server/metrics.mjs';
const origin='https://www.radojelausevic.com',key='a'.repeat(32),privateKey='b'.repeat(32);
const catalog={[key]:{kind:'post',title:'A post',path:'/post/example',public:true},[privateKey]:{kind:'project',title:'A project',path:'/project/example',public:false}};
function setup(){
 const db=new DatabaseSync(':memory:');db.exec(readFileSync(new URL('../migrations/0001_metrics.sql',import.meta.url),'utf8'));
 const prepare=(sql,args=[])=>({bind(...values){return prepare(sql,values);},async first(){return db.prepare(sql).get(...args);},async all(){return {results:db.prepare(sql).all(...args)};},run(){if(sql.startsWith('SELECT'))return {results:db.prepare(sql).all(...args)};db.prepare(sql).run(...args);return {results:[]};}});
 const env={METRICS_DB:{prepare,async batch(statements){db.exec('BEGIN');try{const result=statements.map(s=>s.run());db.exec('COMMIT');return result;}catch(e){db.exec('ROLLBACK');throw e;}}},ASSETS:{fetch:async()=>Response.json(catalog)},METRICS_RATE_LIMITER:{limit:async()=>({success:true})}};
 return {db,env};
}
function req(payload={key,token:'1'.repeat(64)},headers={}){return new Request(origin+'/api/metrics',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json','User-Agent':'Test browser',...headers},body:JSON.stringify(payload)});}
test('atomic per-item session count, retries and new sessions; persists across handlers',async()=>{
 const {db,env}=setup();
 assert.equal((await (await metrics(req(),env)).json()).views,1);
 assert.equal((await (await metrics(req(),env)).json()).views,1);
 assert.equal((await (await metrics(req({key,token:'2'.repeat(64)}),env)).json()).views,2);
 assert.equal((await (await metrics(new Request(origin+'/api/metrics?key='+key),env)).json()).views,2);
 assert.equal(db.prepare('SELECT count(*) n FROM metrics_receipts').get().n,2);
 assert.equal((await (await metrics(new Request(origin+'/api/metrics?status=1'),env)).json()).enabled,true);
 db.close();
});
test('private events count but no public read or total leaks',async()=>{
 const {db,env}=setup();
 assert.deepEqual(await (await metrics(req({key:privateKey,token:'1'.repeat(64)}),env)).json(),{ok:true});
 assert.equal((await metrics(new Request(origin+'/api/metrics?key='+privateKey),env)).status,404);
 assert.equal(db.prepare('SELECT total FROM metrics_totals WHERE key=?').get(privateKey).total,1);db.close();
});
test('rejects forged origins, previews, unknown keys, bots, invalid payloads and rate limits',async()=>{
 const {db,env}=setup();
 assert.equal((await metrics(req(undefined,{Origin:'https://evil.example'}),env)).status,403);
 assert.equal((await metrics(new Request('https://preview.pages.dev/api/metrics?key='+key),env)).status,403);
 assert.equal((await metrics(req({key:'c'.repeat(32),token:'1'.repeat(64)}),env)).status,404);
 assert.equal((await metrics(req(undefined,{'User-Agent':'Googlebot'}),env)).status,403);
 for(const payload of [null,{}, {key,token:'wrong'},{key:'../../bad',token:'1'.repeat(64)}])assert.equal((await metrics(req(payload),env)).status,400);
 assert.equal((await metrics(req(undefined,{'Content-Length':'2000'}),env)).status,413);
 assert.equal((await metrics(req(),{...env,METRICS_RATE_LIMITER:{limit:async()=>({success:false})}})).status,429);
 assert.equal(db.prepare('SELECT count(*) n FROM metrics_totals').get().n,0);db.close();
});
test('missing binding/schema and storage errors fail closed, never show zero success',async()=>{
 assert.equal((await metrics(req(),{})).status,503);
 const {db,env}=setup();db.exec('DROP TABLE metrics_totals');
 const result=await metrics(req(),env);assert.equal(result.status,503);assert.deepEqual(await result.json(),{enabled:false});db.close();
});
test('receipt expiry cleanup keeps permanent counts and updates title without reset',async()=>{
 const {db,env}=setup();await metrics(req(),env);
 db.prepare('UPDATE metrics_receipts SET created_at=0').run();
 await metrics(req({key,token:'2'.repeat(64)}),env);
 assert.equal(db.prepare('SELECT total FROM metrics_totals').get().total,2);
 assert.equal(db.prepare('SELECT count(*) n FROM metrics_receipts').get().n,1);db.close();
});
