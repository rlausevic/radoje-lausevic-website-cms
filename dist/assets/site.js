'use strict';
const toggle=document.querySelector('.menu-toggle');
const nav=document.querySelector('#primary-nav');
const insightsToggle=document.querySelector('.insights-toggle');
const insightsMenu=document.querySelector('#insights-menu');
function closeInsights(){
 if(!insightsToggle||!insightsMenu)return;
 insightsMenu.hidden=true;insightsToggle.setAttribute('aria-expanded','false');insightsToggle.setAttribute('aria-label','Open Insights submenu');
}
function closeNavigation(){
 if(!toggle||!nav)return;
 nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');toggle.textContent='Menu ☰';closeInsights();
}
if(toggle&&nav){
 toggle.addEventListener('click',()=>{const open=!nav.classList.contains('open');if(open){nav.classList.add('open');toggle.setAttribute('aria-expanded','true');toggle.textContent='Close ×';}else closeNavigation();});
 nav.addEventListener('click',event=>{if(event.target.closest('a'))closeNavigation();});
}
if(insightsToggle&&insightsMenu){
 const openInsights=()=>{insightsMenu.hidden=false;insightsToggle.setAttribute('aria-expanded','true');insightsToggle.setAttribute('aria-label','Close Insights submenu');};
 insightsToggle.addEventListener('click',()=>{if(insightsMenu.hidden)openInsights();else closeInsights();});
 insightsToggle.addEventListener('keydown',event=>{if(event.key==='ArrowDown'){event.preventDefault();openInsights();insightsMenu.querySelector('a')?.focus();}});
 document.addEventListener('click',event=>{if(!event.target.closest('.nav-insights'))closeInsights();});
 document.addEventListener('focusin',event=>{if(!event.target.closest('.nav-insights'))closeInsights();});
}
if(toggle&&nav)document.addEventListener('keydown',event=>{
 if(event.key!=='Escape')return;
 const mobileOpen=nav.classList.contains('open'),submenuOpen=insightsMenu&&!insightsMenu.hidden;
 if(!mobileOpen&&!submenuOpen)return;
 event.preventDefault();closeNavigation();if(mobileOpen)toggle.focus();else insightsToggle.focus();
});
// Preserve incoming links to the former About expertise sections.
if(String(location.pathname||'').replace(/\/$/,'')==='/about'&&/^#expertise-\d+$/.test(location.hash))location.replace('/expertise'+location.hash);
const dialog=document.querySelector('#gallery-dialog');
if(dialog){
 const photos=[...document.querySelectorAll('[data-gallery]')];
 const image=dialog.querySelector('img'),caption=dialog.querySelector('#gallery-caption');
 const counter=dialog.querySelector('[data-gallery-counter]');
 const previous=dialog.querySelector('[data-gallery-previous]'),next=dialog.querySelector('[data-gallery-next]');
 const stage=dialog.querySelector('.gallery-stage');
 let current=0,swipe=null;
 const showPhoto=index=>{
  if(!photos.length)return;
  current=(index+photos.length)%photos.length;
  const photo=photos[current];
  image.src=photo.dataset.src;image.alt=photo.dataset.caption||'';
  caption.textContent=photo.dataset.caption||'';counter.textContent=`${current+1} / ${photos.length}`;
  previous.disabled=next.disabled=photos.length<2;
 };
 photos.forEach((photo,index)=>photo.addEventListener('click',()=>{showPhoto(index);dialog.showModal();}));
 previous.addEventListener('click',()=>showPhoto(current-1));
 next.addEventListener('click',()=>showPhoto(current+1));
 dialog.querySelector('[data-gallery-close]').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
 dialog.addEventListener('keydown',event=>{
  if(!dialog.open||event.altKey||event.ctrlKey||event.metaKey)return;
  if(event.key==='ArrowLeft'||event.key==='ArrowRight'){
   event.preventDefault();showPhoto(current+(event.key==='ArrowLeft'?-1:1));
  }
 });
 stage.addEventListener('pointerdown',event=>{
  if(event.pointerType!=='touch'||!event.isPrimary){swipe=null;return;}
  swipe={id:event.pointerId,x:event.clientX,y:event.clientY};
  stage.setPointerCapture(event.pointerId);
 });
 stage.addEventListener('pointerup',event=>{
  if(!swipe||event.pointerId!==swipe.id)return;
  const dx=event.clientX-swipe.x,dy=event.clientY-swipe.y;swipe=null;
  if(Math.abs(dx)>=48&&Math.abs(dx)>Math.abs(dy)*1.25)showPhoto(current+(dx<0?1:-1));
 });
 stage.addEventListener('pointercancel',()=>{swipe=null;});
 dialog.addEventListener('close',()=>{swipe=null;});
}
// One search engine for Journal, Video and Bibliography.
function setupArchiveSearch({input,category,cards,count,empty,singular,plural,groups}){
 const search=document.querySelector(input);if(!search)return;
 const categorySelect=category?document.querySelector(category):null;
 const entries=[...document.querySelectorAll(cards)];
 const resultCount=document.querySelector(count),noResults=document.querySelector(empty);
 const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'d').toLowerCase();
 const index=entries.map(card=>({card,text:normalize(card.dataset.search)}));
 const filter=()=>{
  const terms=normalize(search.value.trim()).split(/\s+/).filter(Boolean),selected=categorySelect?categorySelect.value:'';
  let matched=0;
  index.forEach(({card,text})=>{
   const visible=terms.every(term=>text.includes(term))&&(!selected||(card.dataset.categories||'').split('|').includes(selected));
   card.hidden=!visible;if(visible)matched++;
  });
  resultCount.textContent=matched+' '+(matched===1?singular:plural);noResults.hidden=matched>0;
  if(groups)document.querySelectorAll(groups).forEach(group=>{
   group.hidden=(terms.length>0||!!selected)&&![...group.querySelectorAll(cards)].some(card=>!card.hidden);
  });
 };
 const params=new URLSearchParams(location.search),query=params.get('search'),selected=params.get('category');
 if(query)search.value=query;
 if(categorySelect&&selected&&[...categorySelect.options].some(option=>option.value===selected))categorySelect.value=selected;
 search.addEventListener('input',filter);search.addEventListener('search',filter);
 if(categorySelect)categorySelect.addEventListener('change',filter);
 filter();
}
setupArchiveSearch({input:'#post-search',category:'#post-category',cards:'[data-post]',count:'#result-count',empty:'#no-results',singular:'article',plural:'articles'});
setupArchiveSearch({input:'#video-search',category:'#video-category',cards:'[data-video]',count:'#video-result-count',empty:'#no-videos',singular:'video',plural:'videos'});
setupArchiveSearch({input:'#bibliography-search',category:'#bibliography-category',cards:'[data-bibliography]',count:'#bibliography-result-count',empty:'#no-bibliography',singular:'bibliography item',plural:'bibliography items',groups:'[data-archive-group]'});
setupArchiveSearch({input:'#project-search',category:'#project-category',cards:'[data-project]',count:'#project-result-count',empty:'#no-projects',singular:'project',plural:'projects'});

// Deep links from Home and the former About sections reveal the full service.
const expertiseCards=document.querySelectorAll('.expertise-card');
if(expertiseCards.length){
 const revealExpertise=()=>{
  const card=[...expertiseCards].find(item=>'#'+item.id===location.hash);
  if(card){card.open=true;card.scrollIntoView({block:'start'});}
 };
 revealExpertise();window.addEventListener('hashchange',revealExpertise);
}

setupArchiveSearch({input:'#gallery-search',category:'#gallery-category',cards:'[data-album]',count:'#gallery-result-count',empty:'#no-galleries',singular:'gallery',plural:'galleries'});
