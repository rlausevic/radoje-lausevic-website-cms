/* In-page Network, Recommendations and grouped Bibliography archives. */
(() => {
 const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/gi,'d').toLowerCase();
 function paginate(entries,state,size,page=1) {
  const terms=normalize(state.search).trim().split(/\s+/).filter(Boolean);
  const matches=entries.filter(e=>(!state.category||e.category===state.category)&&(!state.year||e.years.includes(state.year))&&terms.every(t=>normalize(e.search).includes(t)));
  const pages=Math.max(1,Math.ceil(matches.length/size));
  page=Math.max(1,Math.min(pages,Number.isSafeInteger(Number(page))?Number(page):1));
  return {matches,items:matches.slice((page-1)*size,page*size),page,pages,total:matches.length};
 }
 function pageNumbers(page,total) {return total<=7?Array.from({length:total},(_,i)=>i+1):[...new Set([1,total,page-1,page,page+1].filter(n=>n>=1&&n<=total))].sort((a,b)=>a-b);}
 if(typeof module!=='undefined')module.exports={normalize,paginate,pageNumbers};
 if(typeof document==='undefined')return;
 document.querySelectorAll('[data-section-archive]').forEach(root=>{
  const prefix=root.dataset.prefix,size=Number(root.dataset.pageSize),label=root.dataset.label;
  const input=root.querySelector('[data-section-search]'),year=root.querySelector('[data-section-year]'),category=root.querySelector('[data-section-category]');
  const total=root.querySelector('[data-section-total]'),empty=root.querySelector('[data-section-empty]');
  const groups=[...root.querySelectorAll('[data-section-group]')].map(node=>({node,key:node.dataset.group,entries:[...node.querySelectorAll('[data-section-entry]')].map(card=>({card,search:card.dataset.search||'',years:(card.dataset.years||'undated').split('|'),category:card.dataset.categories||''})),count:node.querySelector('[data-section-count]'),nav:node.querySelector('[data-section-pagination]')}));
  groups.forEach(g=>g.node.append(g.nav));
  const key=name=>prefix==='bibliography'?name:prefix+'_'+name;
  const pageKey=group=>key(group.key==='all'?'page':group.key+'_page');
  const valid=(select,value)=>select&&[...select.options].some(o=>o.value===value)?value:'';
  let state,pages={},timer,keepHash=false;
  function readURL() {
   const params=new URLSearchParams(location.search);
   state={search:params.get(key('search'))||'',year:valid(year,params.get(key('year'))||''),category:valid(category,params.get(key('category'))||'')};
   pages=Object.fromEntries(groups.map(g=>[g.key,Number(params.get(pageKey(g))||1)]));
   input.value=state.search;year.value=state.year;if(category)category.value=state.category;
  }
  function urlFor(group,page) {
   const u=new URL(location.href);
   if(!keepHash&&groups.some(g=>g.entries.some(e=>'#'+encodeURIComponent(e.card.id)===u.hash||'#'+e.card.id===u.hash)))u.hash='';
   for(const [name,value] of Object.entries(state)){if(value)u.searchParams.set(key(name),value);else u.searchParams.delete(key(name));}
   for(const g of groups){const n=g===group?page:pages[g.key];if(n>1)u.searchParams.set(pageKey(g),n);else u.searchParams.delete(pageKey(g));}
   return u.pathname+u.search+u.hash;
  }
  function navigate(g,result) {
   g.nav.replaceChildren();g.nav.hidden=result.pages<=1;
   if(result.pages<=1)return;
   function add(n,text,disabled=false){
    const a=document.createElement(disabled?'span':'a');a.textContent=text;
    if(disabled)a.setAttribute('aria-disabled','true');
    else {a.href=urlFor(g,n);a.dataset.sectionPage=String(n);if(/^\d+$/.test(text)){a.setAttribute('aria-label','Page '+n);if(n===result.page)a.setAttribute('aria-current','page');}}
    g.nav.append(a);
   }
   add(result.page-1,'Previous',result.page===1);let previous=0;
   for(const n of pageNumbers(result.page,result.pages)){if(previous&&n>previous+1){const gap=document.createElement('span');gap.textContent='…';gap.setAttribute('aria-hidden','true');g.nav.append(gap);}add(n,String(n));previous=n;}
   add(result.page+1,'Next',result.page===result.pages);
  }
  function apply(mode=null,focusGroup=null) {
   const results=groups.map(g=>paginate(g.entries,state,size,pages[g.key]));
   let matched=0,visible=0;
   results.forEach((result,i)=>{const g=groups[i];pages[g.key]=result.page;matched+=result.total;visible+=result.items.length;});
   results.forEach((result,i)=>{
    const g=groups[i],shown=new Set(result.items);
    g.entries.forEach(e=>{e.card.hidden=!shown.has(e);});
    g.node.hidden=!!(state.search||state.year||state.category)&&result.total===0;
    const start=(result.page-1)*size+1,end=start+result.items.length-1;
    const unit=(g.node.dataset.label||label).replace(/s$/,result.total===1?'':'s');
    g.count.textContent=result.total?`Showing ${start}–${end} of ${result.total} ${unit}`:'0 '+(g.node.dataset.label||label);
    navigate(g,result);
   });
   if(total)total.textContent=`Showing ${visible} of ${matched} ${label.replace(/s$/,matched===1?'':'s')}`;
   empty.hidden=matched>0;
   if(mode){const url=urlFor(null,1);if(url!==location.pathname+location.search+location.hash)history[mode==='push'?'pushState':'replaceState'](null,'',url);}
   if(focusGroup){focusGroup.count.focus({preventScroll:true});focusGroup.node.scrollIntoView({block:'start',behavior:'instant'});}
  }
  function revealHash() {
   let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
   const g=groups.find(g=>g.entries.some(e=>e.card.id===id));if(!g)return;
   clearTimeout(timer);state={search:'',year:'',category:''};input.value='';year.value='';if(category)category.value='';
   const entry=g.entries.find(e=>e.card.id===id);pages[g.key]=Math.floor(g.entries.indexOf(entry)/size)+1;keepHash=true;apply('replace');keepHash=false;
   if(entry.card.tagName==='DETAILS')entry.card.open=true;
   requestAnimationFrame(()=>entry.card.scrollIntoView({block:'start'}));
  }
  function filter(mode){state={search:input.value.trim(),year:year.value,category:category?.value||''};groups.forEach(g=>pages[g.key]=1);apply(mode);}
  input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>filter('replace'),150);});
  input.addEventListener('search',()=>{clearTimeout(timer);filter('replace');});
  for(const select of [year,category].filter(Boolean))select.addEventListener('change',()=>{clearTimeout(timer);filter('push');});
  groups.forEach(g=>g.nav.addEventListener('click',event=>{
   const a=event.target.closest('a[data-section-page]');if(!a||event.ctrlKey||event.metaKey||event.altKey||event.shiftKey||event.button>0)return;
   event.preventDefault();clearTimeout(timer);pages[g.key]=Number(a.dataset.sectionPage);apply('push',g);
  }));
  window.addEventListener('popstate',()=>{clearTimeout(timer);readURL();apply();revealHash();});
  window.addEventListener('hashchange',revealHash);
  // Clicking the same hash twice must also reveal a filtered-out target.
  document.addEventListener('click',event=>{const a=event.target.closest('a');if(a?.hash&&a.origin===location.origin&&a.pathname===location.pathname&&a.hash===location.hash)revealHash();});
  readURL();apply();revealHash();
 });
})();
