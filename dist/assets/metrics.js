(() => {
 'use strict';
 const endpoint='/api/metrics';
 // Production only: preview builds must not inflate the public counters.
 if(!['www.radojelausevic.com','radojelausevic.com','radoje-lausevic-website-cms.pages.dev'].includes(location.hostname))return;
 const pending=new Map(),memory=new Map();
 function state(key){
  if(memory.has(key))return memory.get(key);
  let value;
  try{value=JSON.parse(sessionStorage.getItem('metric:'+key)||'null');}catch{}
  if(!value||!(/^[a-f0-9]{64}$/).test(value.token||''))value={token:Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join(''),sent:false};
  memory.set(key,value);save(key,value);return value;
 }
 function save(key,value){try{sessionStorage.setItem('metric:'+key,JSON.stringify(value));}catch{}}
 function display(element,data){
  if(!element||!Number.isSafeInteger(data.views)||data.views<0)return;
  const video=element.dataset.metricLabel==='page';
  element.textContent=new Intl.NumberFormat('en').format(data.views)+(video?(data.views===1?' page view':' page views'):(data.views===1?' view':' views'));
  element.hidden=false;
 }
 async function record(key,element){
  if(!key||pending.has(key))return;
  const current=state(key);
  if(current.sent&&!element)return;
  pending.set(key,true);
  try{
   const response=await fetch(current.sent?endpoint+'?key='+encodeURIComponent(key):endpoint,current.sent?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,token:current.token}),keepalive:true});
   if(!response.ok)return;
   const data=await response.json();if(!data.ok)return;
   current.sent=true;save(key,current);display(element,data);
  }catch{}finally{pending.delete(key);}
 }
 function pageView(){
  if(document.visibilityState!=='visible')return;
  const element=document.querySelector('[data-metric-view]');
  if(element)record(element.dataset.metricView,element.hasAttribute('data-metric-public')?element:null);
 }
 pageView();
 document.addEventListener('visibilitychange',pageView);
 document.addEventListener('click',event=>{
  const link=event.target.closest?.('a[data-metric-download]');
  if(link)record(link.dataset.metricDownload,null);
 });
 document.addEventListener('auxclick',event=>{
  if(event.button!==1)return;
  const link=event.target.closest?.('a[data-metric-download]');
  if(link)record(link.dataset.metricDownload,null);
 });
})();
