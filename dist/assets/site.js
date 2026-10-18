'use strict';
const toggle=document.querySelector('.menu-toggle');
const nav=document.querySelector('#primary-nav');
if(toggle&&nav){toggle.addEventListener('click',()=>{const open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'Close ×':'Menu ☰';});document.addEventListener('keydown',e=>{if(e.key==='Escape'){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');toggle.textContent='Menu ☰';}});}
const dialog=document.querySelector('#gallery-dialog');
if(dialog){document.querySelectorAll('[data-gallery]').forEach(btn=>btn.addEventListener('click',()=>{const image=dialog.querySelector('img');image.src=btn.dataset.src;image.alt=btn.dataset.caption;dialog.querySelector('p').textContent=btn.dataset.caption;dialog.showModal();}));dialog.querySelector('button').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});}
const form=document.querySelector('#contact-form');
if(form){form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;const values=new FormData(form);const subject=String(values.get('subject')||'Website inquiry');const body='Name: '+values.get('name')+'\nEmail: '+values.get('email')+'\n\n'+values.get('message');location.href='mailto:'+encodeURIComponent(form.dataset.email)+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);document.querySelector('#contact-status').textContent='Your email application should open with the message prepared. Please send it there. If it does not open, email '+form.dataset.email+' directly.';});}


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
setupArchiveSearch({input:'#video-search',cards:'[data-video]',count:'#video-result-count',empty:'#no-videos',singular:'video',plural:'videos'});
setupArchiveSearch({input:'#bibliography-search',category:'#bibliography-category',cards:'[data-bibliography]',count:'#bibliography-result-count',empty:'#no-bibliography',singular:'bibliography item',plural:'bibliography items',groups:'[data-archive-group]'});
setupArchiveSearch({input:'#project-search',category:'#project-category',cards:'[data-project]',count:'#project-result-count',empty:'#no-projects',singular:'project',plural:'projects'});
