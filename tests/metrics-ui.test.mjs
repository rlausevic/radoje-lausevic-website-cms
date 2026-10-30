import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
const code=readFileSync(new URL('../dist/assets/metrics.js',import.meta.url),'utf8');
async function mount({storage=new Map(),ok=true,privatePage=false,hidden=false,downloads=false,host='www.radojelausevic.com'}={}){
 const element={dataset:{metricView:'a'.repeat(32),metricLabel:'page'},hasAttribute:()=>!privatePage,hidden:true,textContent:''},calls=[],listeners={};
 const document={visibilityState:hidden?'hidden':'visible',querySelector:()=>downloads?null:element,addEventListener:(name,fn)=>listeners[name]=fn};
 const sessionStorage={getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)};
 vm.runInNewContext(code,{document,sessionStorage,location:{hostname:host},crypto:webcrypto,Intl,fetch:async(url,options)=>{calls.push({url,options});return {ok,json:async()=>({ok:true,views:23})};}});
 await new Promise(resolve=>setImmediate(resolve));return {element,calls,listeners,document,storage};
}
test('counter reveals successful response; refresh reads without increment',async()=>{
 const first=await mount();assert.equal(first.calls[0].options.method,'POST');assert.equal(first.element.textContent,'23 page views');assert.equal(first.element.hidden,false);
 const second=await mount({storage:first.storage});assert(second.calls[0].url.includes('?key='));assert(!second.calls[0].options.method);
});
test('failure is invisible and retry keeps same token',async()=>{
 const first=await mount({ok:false});assert.equal(first.element.hidden,true);
 const second=await mount({storage:first.storage});assert.equal(first.calls[0].options.body,second.calls[0].options.body);
});
test('private pages do not reveal counts; hidden tabs wait; previews do nothing',async()=>{
 assert.equal((await mount({privatePage:true})).element.hidden,true);
 const hidden=await mount({hidden:true});assert.equal(hidden.calls.length,0);hidden.document.visibilityState='visible';hidden.listeners.visibilitychange();await new Promise(r=>setImmediate(r));assert.equal(hidden.calls.length,1);
 assert.equal((await mount({host:'preview.pages.dev'})).calls.length,0);
});
test('download clicks do not block navigation and are deduplicated in session',async()=>{
 const app=await mount({downloads:true});const event={target:{closest:()=>({dataset:{metricDownload:'b'.repeat(32)}})}};
 app.listeners.click(event);await new Promise(r=>setImmediate(r));app.listeners.click(event);await new Promise(r=>setImmediate(r));assert.equal(app.calls.length,1);
});
