const HOSTS=new Set(['www.radojelausevic.com','radojelausevic.com','radoje-lausevic-website-cms.pages.dev']);
const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const digest=async value=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),b=>b.toString(16).padStart(2,'0')).join('');
// Best-effort isolate limit on Pages; use METRICS_RATE_LIMITER when available.
const rates=new Map();
async function allowedRate(request,env){
 const ip=request.headers.get('CF-Connecting-IP')||'unknown';
 if(env.METRICS_RATE_LIMITER)return (await env.METRICS_RATE_LIMITER.limit({key:ip})).success;
 const now=Date.now();
 for(const [key,row] of rates)if(now-row.at>60000)rates.delete(key);
 if(!rates.has(ip)){if(rates.size>=2000)return false;rates.set(ip,{at:now,count:0});}
 return ++rates.get(ip).count<=60;
}
async function readBody(request){
 const reader=request.body?.getReader();if(!reader)throw Error('body');
 let size=0,parts=[];
 try{while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>1024){await reader.cancel();throw Error('size');}parts.push(value);}}finally{reader.releaseLock();}
 const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
 return JSON.parse(new TextDecoder().decode(bytes));
}
export async function metrics(request,env){
 const url=new URL(request.url);
 if(!HOSTS.has(url.hostname))return json({enabled:false},403);
 if(!['GET','POST'].includes(request.method))return json({ok:false},405);
 if(!env.METRICS_DB||!env.ASSETS)return json({enabled:false},503);
 try{
  if(request.method==='GET'&&url.searchParams.get('status')==='1'){
   await env.METRICS_DB.prepare('SELECT key FROM metrics_totals LIMIT 1').all();
   return json({enabled:true});
  }
  if(request.method==='POST'){
   if(request.headers.get('Origin')!==url.origin)return json({ok:false},403);
   if(!request.headers.get('Content-Type')?.startsWith('application/json'))return json({ok:false},415);
   if(Number(request.headers.get('Content-Length')||0)>1024)return json({ok:false},413);
   if(/bot|crawler|spider|headless|preview/i.test(request.headers.get('User-Agent')||''))return json({ok:false},403);
  }
  if(!await allowedRate(request,env))return json({ok:false},429);
  let payload;
  try{payload=request.method==='POST'?await readBody(request):{key:url.searchParams.get('key')};}catch{return json({ok:false},400);}
  if(!payload||!(/^[a-f0-9]{32}$/).test(payload.key||''))return json({ok:false},400);
  // Read the generated deployment-local allow-list, never a client-provided URL.
  const catalogResponse=await env.ASSETS.fetch(new Request(new URL('/_metrics/catalog.json',url)));
  if(!catalogResponse.ok)return json({enabled:false},503);
  const catalog=await catalogResponse.json(),entry=catalog[payload.key];
  if(!entry)return json({ok:false},404);
  if(request.method==='GET'&&!entry.public)return json({ok:false},404);
  if(request.method==='POST'){
   if(typeof payload.token!=='string'||!(/^[a-f0-9]{64}$/).test(payload.token))return json({ok:false},400);
   const receipt=await digest(payload.key+':'+payload.token);
   const now=Math.floor(Date.now()/1000);
   const batch=[
    env.METRICS_DB.prepare('INSERT INTO metrics_totals(key,kind,title,path) VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET title=excluded.title,path=excluded.path').bind(payload.key,entry.kind,entry.title,entry.path),
    env.METRICS_DB.prepare('INSERT OR IGNORE INTO metrics_receipts(key,receipt,created_at) VALUES(?,?,?)').bind(payload.key,receipt,now),
    // Small bounded cleanup; aggregate counts are permanent.
    env.METRICS_DB.prepare('DELETE FROM metrics_receipts WHERE rowid IN (SELECT rowid FROM metrics_receipts WHERE created_at < ? LIMIT 100)').bind(now-30*86400),
   ];
   if(entry.public)batch.push(env.METRICS_DB.prepare('SELECT total FROM metrics_totals WHERE key=?').bind(payload.key));
   const result=await env.METRICS_DB.batch(batch);
   return json(entry.public?{ok:true,views:result[result.length-1].results[0].total}:{ok:true});
  }
  const row=await env.METRICS_DB.prepare('SELECT total FROM metrics_totals WHERE key=?').bind(payload.key).first();
  return json({ok:true,views:row?.total||0});
 }catch{
  // Metrics must never break navigation or expose database errors.
  return json({enabled:false},503);
 }
}
