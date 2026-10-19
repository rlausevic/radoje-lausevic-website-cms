import {test} from 'node:test';
import assert from 'node:assert/strict';
import {contact,contactConfig,SENDER,configured} from '../server/contact.mjs';
import worker from '../worker/index.mjs';
const origin='https://radojelausevic.com';
const payload={name:'Test Sender',email:'visitor@example.org',subject:'Collaboration',message:'A website inquiry.',token:'test-token',website:''};
function request(data=payload,extra={}){return new Request(origin+'/api/contact',{method:'POST',headers:{Origin:origin,'Content-Type':'application/json','CF-Connecting-IP':'192.0.2.1',...extra},body:JSON.stringify(data)});}
function environment(overrides={}){return {CONTACT_RECIPIENT:'owner@example.org',TURNSTILE_SITE_KEY:'production-sitekey',TURNSTILE_SECRET_KEY:'secret',CONTACT_RATE_LIMITER:{limit:async()=>({success:true})},EMAIL:{send:async()=>({messageId:'accepted-id'})},...overrides};}
const verified=async()=>new Response(JSON.stringify({success:true,hostname:'radojelausevic.com',action:'contact'}));
test('disabled until email and live Turnstile are configured; only public key exposed',async()=>{
 const env=environment();assert(configured(env));
 assert(!configured({...env,TURNSTILE_SITE_KEY:'1x00000000000000000000AA'}));
 assert(!configured({...env,EMAIL:null}));
 const result=await contactConfig(new Request(origin+'/api/contact-config'),env).json();assert.deepEqual(result,{enabled:true,siteKey:'production-sitekey'});assert(!JSON.stringify(result).includes('secret'));
 assert.equal((await contact(request(),{})).status,503);
});
test('mail accepted before success; fixed recipient and sender, reply goes to visitor',async()=>{
 let sent;
 const env=environment({EMAIL:{send:async value=>{sent=value;return {messageId:'accepted'};}}});
 const res=await contact(request({...payload,to:'attacker@example.org',from:'forged@example.org'}),env,verified);
 assert.equal(res.status,200);assert.equal((await res.json()).ok,true);assert.equal(sent.to,env.CONTACT_RECIPIENT);assert.equal(sent.from.email,SENDER);assert.equal(sent.replyTo,payload.email);assert(sent.text.includes(payload.message));
});
test('rejects cross-origin, wrong method, malformed and oversized requests',async()=>{
 const env=environment();let sent=false;env.EMAIL.send=async()=>{sent=true;};
 assert.equal((await contact(request(payload,{Origin:'https://evil.example'}),env)).status,403);
 assert.equal((await contact(new Request(origin+'/api/contact'),env)).status,405);
 assert.equal((await contact(request(payload,{'Content-Type':'text/plain'}),env)).status,415);
 assert.equal((await contact(request({...payload,message:'x'.repeat(21000)}),env)).status,413);
 for(const data of [null,[],{...payload,subject:'Subject\r\nBcc: victim@example.org'},{...payload,website:'spam'},{...payload,email:'not an email'},{...payload,message:'x'.repeat(4001)},{...payload,token:''}])assert.equal((await contact(request(data),env)).status,400);
 assert.equal(sent,false);
});
test('rate limiting stops a submission before validation or email sending',async()=>{
 const res=await contact(request(),environment({CONTACT_RATE_LIMITER:{limit:async()=>({success:false})}}),()=>{throw new Error('must not verify');});assert.equal(res.status,429);assert.equal(res.headers.get('Retry-After'),'60');
});
test('requires successful, host-bound, action-bound token validation',async()=>{
 const env=environment({EMAIL:{send:()=>{throw new Error('must not send');}}});
 for(const result of [{success:false},{success:true,hostname:'evil.example',action:'contact'},{success:true,hostname:'radojelausevic.com',action:'login'}])assert.equal((await contact(request(),env,async()=>new Response(JSON.stringify(result)))).status,400);
 assert.equal((await contact(request(),env,async()=>{throw new Error('network');})).status,503);
});
test('provider errors or missing acceptance ID never produce a success response',async()=>{
 for(const send of [async()=>{throw new Error('internal credential detail');},async()=>undefined]){
  const res=await contact(request(),environment({EMAIL:{send}}),verified);assert.equal(res.status,502);const result=await res.json();assert.equal(result.ok,false);assert(!result.message.includes('credential'));
 }
});
test('Worker serves APIs first and retains static asset fallback',async()=>{
 const env={ASSETS:{fetch:async()=>new Response('static')}};
 assert.deepEqual(await (await worker.fetch(new Request(origin+'/api/contact-config'),env)).json(),{enabled:false,siteKey:null});
 assert.equal(await (await worker.fetch(new Request(origin+'/about'),env)).text(),'static');
 assert.equal((await worker.fetch(new Request(origin+'/api/unknown'),env)).status,404);
});
