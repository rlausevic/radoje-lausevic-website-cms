'use strict';
(() => {
 const form=document.querySelector('#contact-form');if(!form)return;
 const fields=form.querySelector('fieldset'),button=form.querySelector('button[type=submit]'),status=document.querySelector('#contact-status');
 const recipient=form.dataset.email,unavailable='Direct messaging is temporarily unavailable. Please email '+recipient+'.';
 const uncertain='We couldn’t confirm that your message was sent. Please try again or email '+recipient+'.';
 let busy=false,token='',widget;
 const announce=(message,error=false)=>{status.textContent=message;status.dataset.state=error?'error':'success';};
 const controls=()=>{button.disabled=busy||!token;button.textContent=busy?'Sending…':'Send message';form.setAttribute('aria-busy',String(busy));};
 const resetChallenge=()=>{token='';if(widget!==undefined&&window.turnstile)window.turnstile.reset(widget);controls();};
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(busy||!form.reportValidity())return;
  if(!token){announce('Please complete the security check before sending.',true);return;}
  busy=true;controls();announce('Sending your message…');
  const values=new FormData(form),controller=new AbortController(),timer=setTimeout(()=>controller.abort(),20000);
  const payload=Object.fromEntries(['name','email','subject','message','website'].map(key=>[key,String(values.get(key)||'')]));payload.token=token;
  try{
   const response=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(payload),signal:controller.signal});
   const result=await response.json();
   if(!response.ok||result.ok!==true)throw new Error(typeof result.message==='string'?result.message:uncertain);
   form.reset();announce('Thank you. Your message has been submitted.');
  }catch(error){announce(error.name==='AbortError'?uncertain:(error instanceof SyntaxError||error instanceof TypeError?uncertain:error.message||uncertain),true);}
  finally{clearTimeout(timer);busy=false;resetChallenge();status.focus();}
 });
 async function initialize(){
  try{
   const response=await fetch('/api/contact-config',{headers:{Accept:'application/json'},signal:AbortSignal.timeout(8000)});
   if(!response.ok)throw new Error('config');const config=await response.json();
   if(!config.enabled||!config.siteKey)throw new Error('unavailable');
   await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error('timeout')),12000);
    window.contactTurnstileReady=()=>{clearTimeout(timer);resolve();};
    const script=document.createElement('script');script.src='https://challenges.cloudflare.com/turnstile/v0/api.js?onload=contactTurnstileReady&render=explicit';script.async=true;script.defer=true;script.onerror=()=>{clearTimeout(timer);reject(new Error('load'));};document.head.appendChild(script);
   });
   widget=window.turnstile.render('#contact-security',{sitekey:config.siteKey,action:'contact',callback:value=>{token=value;controls();},'expired-callback':()=>{token='';controls();},'error-callback':()=>{token='';controls();announce('The security check could not load. Please retry or email '+recipient+'.',true);}});
   fields.disabled=false;announce('Complete the fields and security check to send your message.');controls();
  }catch{announce(unavailable,true);fields.disabled=true;button.disabled=true;}
 }
 initialize();
})();
