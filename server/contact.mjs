// Shared by Pages Functions and Workers. Recipients never come from browser input.
const PUBLIC_CONTACT = 'radoje.lausevic@gmail.com';
export const SENDER = 'website@radojelausevic.com';
const HOSTS = new Set(['radojelausevic.com', 'www.radojelausevic.com', 'radoje-lausevic-website-cms.pages.dev']);
const TEST_KEYS = /^(?:1x|2x|3x)0{10}/;
const recent = new Map();
const failure = 'We couldn’t confirm that your message was sent. Please try again or email '+PUBLIC_CONTACT+'.';
function json(value, status=200, extra={}) {
 return new Response(JSON.stringify(value), {status, headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...extra}});
}
export function configured(env) {
 return !!(typeof env.CONTACT_RECIPIENT==='string' && /^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$/.test(env.CONTACT_RECIPIENT) && env.EMAIL?.send && env.TURNSTILE_SITE_KEY && env.TURNSTILE_SECRET_KEY && !TEST_KEYS.test(env.TURNSTILE_SITE_KEY) && !TEST_KEYS.test(env.TURNSTILE_SECRET_KEY));
}
export function contactConfig(request, env) {
 if(request.method!=='GET')return json({ok:false},405,{Allow:'GET'});
 const enabled=HOSTS.has(new URL(request.url).hostname)&&configured(env);
 const result={enabled,siteKey:enabled?env.TURNSTILE_SITE_KEY:null};
 if(new URL(request.url).searchParams.get('diagnostics')==='1')result.checks={
  version:'contact-config-1',
  allowedHost:HOSTS.has(new URL(request.url).hostname),
  emailBinding:typeof env.EMAIL?.send==='function',
  recipient:typeof env.CONTACT_RECIPIENT==='string' && /^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$/.test(env.CONTACT_RECIPIENT),
  siteKey:!!env.TURNSTILE_SITE_KEY,
  secretKey:!!env.TURNSTILE_SECRET_KEY,
  liveKeys:!TEST_KEYS.test(env.TURNSTILE_SITE_KEY||'')&&!TEST_KEYS.test(env.TURNSTILE_SECRET_KEY||'')
 };
 return json(result);
}
async function limitedBody(request) {
 const reader=request.body?.getReader();if(!reader)throw new Error('body');
 let total=0,chunks=[];
 try {while(true){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>20000){await reader.cancel();throw new Error('size');}chunks.push(value);}} finally{reader.releaseLock();}
 const bytes=new Uint8Array(total);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
 return JSON.parse(new TextDecoder().decode(bytes));
}
async function allowedRate(ip, env) {
 if(env.CONTACT_RATE_LIMITER)return (await env.CONTACT_RATE_LIMITER.limit({key:'contact:'+ip})).success;
 // Secondary, best-effort protection on Pages; Turnstile is always required.
 const now=Date.now(),key=ip||'unknown';
 for(const [id,item] of recent)if(now-item.start>60000)recent.delete(id);
 let item=recent.get(key);if(!item){if(recent.size>=1000)return false;item={start:now,count:0};recent.set(key,item);}
 return ++item.count<=5;
}
export async function contact(request, env, fetcher=fetch) {
 if(request.method!=='POST')return json({ok:false,message:'Use the contact form to send a message.'},405,{Allow:'POST'});
 const url=new URL(request.url);
 if(!HOSTS.has(url.hostname)||request.headers.get('Origin')!==url.origin)return json({ok:false,message:'Please send your message from the Contact page.'},403);
 if(!configured(env))return json({ok:false,message:'Direct messaging is temporarily unavailable. Please email '+PUBLIC_CONTACT+'.'},503);
 if(!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json'))return json({ok:false,message:'Invalid message format.'},415);
 const length=Number(request.headers.get('Content-Length')||0);if(length>20000)return json({ok:false,message:'Your message is too long.'},413);
 const ip=request.headers.get('CF-Connecting-IP')||'';
 try{if(!await allowedRate(ip,env))return json({ok:false,message:'Too many attempts. Please wait a minute before trying again.'},429,{'Retry-After':'60'});}catch{return json({ok:false,message:failure},503);}
 let data;try{data=await limitedBody(request);}catch(e){return json({ok:false,message:e.message==='size'?'Your message is too long.':'Please check the message fields.'},e.message==='size'?413:400);}
 if(!data||typeof data!=='object'||Array.isArray(data))return json({ok:false,message:'Please check the message fields.'},400);
 const read=(key,max)=>typeof data[key]==='string'&&data[key].trim().length<=max?data[key].trim():'';
 const name=read('name',150),email=read('email',200),subject=read('subject',200),message=read('message',4000),token=read('token',2048);
 if(!name||!subject||!message||!email||!token||/[\r\n\x00-\x1f\x7f]/.test(name+email+subject)||message.includes('\0')||!/^[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+$/.test(email)||data.website)return json({ok:false,message:'Please check all fields and complete the security check.'},400);
 let verification;
 try{
  const result=await fetcher('https://challenges.cloudflare.com/turnstile/v0/siteverify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({secret:env.TURNSTILE_SECRET_KEY,response:token,...(ip?{remoteip:ip}:{})}),signal:AbortSignal.timeout(8000)});
  if(!result.ok)throw new Error('verification');verification=await result.json();
 }catch{return json({ok:false,message:'The security check is temporarily unavailable. Please try again.'},503);}
 if(verification.success!==true||verification.hostname!==url.hostname||verification.action!=='contact')return json({ok:false,message:'The security check expired or failed. Please complete it again.'},400);
 try{
  const sent=await env.EMAIL.send({from:{email:SENDER,name:'Radoje Laušević website'},to:env.CONTACT_RECIPIENT,replyTo:email,subject:'Website inquiry: '+subject,text:'Name: '+name+'\nEmail: '+email+'\nSubject: '+subject+'\n\n'+message});
  if(!sent?.messageId)throw new Error('not_accepted');
  return json({ok:true,message:'Thank you. Your message has been submitted.'});
 }catch{return json({ok:false,message:failure},502);}
}
