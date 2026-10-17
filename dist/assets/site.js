'use strict';
const toggle=document.querySelector('.menu-toggle');
const nav=document.querySelector('#primary-nav');
if(toggle&&nav){toggle.addEventListener('click',()=>{const open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'Close ×':'Menu ☰';});document.addEventListener('keydown',e=>{if(e.key==='Escape'){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');toggle.textContent='Menu ☰';}});}
const search=document.querySelector('#post-search'),category=document.querySelector('#post-category');
if(search&&category){const cards=[...document.querySelectorAll('[data-post]')];const filter=()=>{const q=search.value.trim().toLowerCase(),c=category.value;let n=0;cards.forEach(card=>{const matches=(!q||card.dataset.search.includes(q))&&(!c||card.dataset.categories.split('|').includes(c));card.hidden=!matches;if(matches)n++;});document.querySelector('#result-count').textContent=n+' '+(n===1?'article':'articles');document.querySelector('#no-results').hidden=n>0;};search.addEventListener('input',filter);category.addEventListener('change',filter);const params=new URLSearchParams(location.search);const cat=params.get('category');const query=params.get('search');if(query)search.value=query;if(cat&&[...category.options].some(o=>o.value===cat)){category.value=cat;}filter();}
const dialog=document.querySelector('#gallery-dialog');
if(dialog){document.querySelectorAll('[data-gallery]').forEach(btn=>btn.addEventListener('click',()=>{const image=dialog.querySelector('img');image.src=btn.dataset.src;image.alt=btn.dataset.caption;dialog.querySelector('p').textContent=btn.dataset.caption;dialog.showModal();}));dialog.querySelector('button').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});}
const form=document.querySelector('#contact-form');
if(form){form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;const values=new FormData(form);const subject=String(values.get('subject')||'Website inquiry');const body='Name: '+values.get('name')+'\nEmail: '+values.get('email')+'\n\n'+values.get('message');location.href='mailto:'+encodeURIComponent(form.dataset.email)+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);document.querySelector('#contact-status').textContent='Your email application should open with the message prepared. Please send it there. If it does not open, email '+form.dataset.email+' directly.';});}

// Search the video archive, including detailed descriptions.
const videoSearch=document.querySelector('#video-search');
if(videoSearch){
 const videoCards=[...document.querySelectorAll('[data-video]')];
 const videoCount=document.querySelector('#video-result-count');
 const videoEmpty=document.querySelector('#no-videos');
 const filterVideos=()=>{
  const query=videoSearch.value.trim().toLowerCase();let matched=0;
  videoCards.forEach(card=>{const visible=!query||card.dataset.search.includes(query);card.hidden=!visible;if(visible)matched++;});
  videoCount.textContent=matched+' '+(matched===1?'video':'videos');
  videoEmpty.hidden=matched>0;
 };
 const query=new URLSearchParams(location.search).get('search');if(query)videoSearch.value=query;
 videoSearch.addEventListener('input',filterVideos);filterVideos();
}
