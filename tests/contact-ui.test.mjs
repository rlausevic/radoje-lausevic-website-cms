import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs';
const source=fs.readFileSync('dist/assets/contact.js','utf8');
async function setup(mode){
 const fields={disabled:true},button={disabled:true},status={dataset:{},focus(){this.focused=true;}};
 const values={name:'Visitor',email:'visitor@example.org',subject:'Test',message:'Keep this text',website:''};
 let submit,callback,reset=false,pendingResolve,calls=0;
 const form={dataset:{email:'radoje.lausevic@gmail.com'},querySelector:s=>s==='fieldset'?fields:button,setAttribute(){},addEventListener:(event,fn)=>submit=fn,reportValidity:()=>true,reset(){reset=true;values.message='';}};
 const window={turnstile:{render:(selector,options)=>{callback=options.callback;return 'widget';},reset(){}}};
 const fetch=async url=>{
  if(url.endsWith('-config'))return new Response(JSON.stringify({enabled:mode!=='disabled',siteKey:'public'}));
  calls++;
  if(mode==='network')throw new TypeError('Failed to fetch');
  if(mode==='pending')await new Promise(resolve=>pendingResolve=resolve);
  return new Response(JSON.stringify(mode==='success'?{ok:true}:{ok:false,message:'Delivery failed. Please retry.'}),{status:mode==='success'?200:502});
 };
 vm.runInNewContext(source,{document:{querySelector:s=>s==='#contact-form'?form:status,createElement:()=>({}),head:{appendChild:()=>queueMicrotask(()=>window.contactTurnstileReady())}},window,fetch,FormData:class{get(key){return values[key];}},setTimeout,clearTimeout,AbortController,AbortSignal,TypeError,SyntaxError,Error});
 await new Promise(resolve=>setImmediate(resolve));
 return {fields,button,status,values,submit:()=>submit({preventDefault(){}}),verify:()=>callback('verified'),release:()=>pendingResolve(),calls:()=>calls,reset:()=>reset};
}
test('success is announced only after acceptance and clears the form',async()=>{const ui=await setup('success');ui.verify();await ui.submit();assert(ui.reset());assert.equal(ui.status.dataset.state,'success');assert.equal(ui.values.message,'');});
test('provider rejection and network failure retain input and never claim success',async()=>{for(const mode of ['failure','network']){const ui=await setup(mode);ui.verify();await ui.submit();assert(!ui.reset());assert.equal(ui.values.message,'Keep this text');assert.equal(ui.status.dataset.state,'error');assert(ui.status.focused);}});
test('double clicks cannot make parallel requests',async()=>{const ui=await setup('pending');ui.verify();const first=ui.submit();await new Promise(resolve=>setImmediate(resolve));await ui.submit();assert.equal(ui.calls(),1);assert(ui.button.disabled);ui.release();await first;});
test('unconfigured service stays disabled with a usable fallback address',async()=>{const ui=await setup('disabled');assert(ui.fields.disabled);assert(ui.button.disabled);assert(ui.status.textContent.includes('radoje.lausevic@gmail.com'));assert.equal(ui.calls(),0);});
