/* Journal pagination and global search; no changes to CMS records or article URLs. */
(() => {
 const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase();
 const pageNumbers = (current, total) => total <= 7 ? Array.from({length: total}, (_, i) => i + 1) : [...new Set([1, total, current - 1, current, current + 1].filter(n => n >= 1 && n <= total))].sort((a,b) => a-b);
 function selectEntries(entries, state, size = 12) {
  const terms = normalize(state.search).trim().split(/\s+/).filter(Boolean);
  const matching = entries.filter(entry => (!state.category || entry.topic === state.category) && (!state.year || entry.year === state.year) && terms.every(term => normalize(entry.search).includes(term)));
  const pages = Math.max(1, Math.ceil(matching.length / size));
  const parsed = Number(state.page);
  const page = Math.min(pages, Number.isSafeInteger(parsed) && parsed > 0 ? parsed : 1);
  return {items: matching.slice((page-1)*size, page*size), total: matching.length, page, pages};
 }
 const stateURL = state => {
  const params = new URLSearchParams();
  if (state.search) params.set('search', state.search);
  if (state.category) params.set('category', state.category);
  if (state.year) params.set('year', state.year);
  if (state.page > 1) params.set('page', state.page);
  return '/blog/' + (params.size ? '?' + params : '');
 };
 if (typeof module !== 'undefined') module.exports = {normalize, selectEntries, pageNumbers, stateURL};
 if (typeof document === 'undefined') return;
 const stored = key => {try { return sessionStorage.getItem(key); } catch { return null; }};
 const save = (key, value) => {try { sessionStorage.setItem(key, value); } catch { /* Storage may be disabled. */ }};
 const safeReturn = () => {
  try {
   const url = new URL(stored('journal-return') || '', location.origin);
   return url.origin === location.origin && /^\/blog(?:\/page\/\d+)?\/?$/.test(url.pathname) ? url.pathname + url.search : null;
  } catch { return null; }
 };
 document.querySelectorAll('[data-journal-back]').forEach(link => {
  const back = safeReturn(); if (back) link.href = back;
 });
 const root = document.querySelector('#journal-archive');
 if (!root) return;
 const input = document.querySelector('#post-search'), topic = document.querySelector('#post-category'), year = document.querySelector('#post-year');
 const grid = document.querySelector('#post-results'), count = document.querySelector('#result-count'), empty = document.querySelector('#no-results');
 const nav = document.querySelector('#journal-pagination'), error = document.querySelector('#journal-error');
 const size = Number(root.dataset.pageSize), total = Number(root.dataset.total), initialPage = Number(root.dataset.page);
 const validOption = (select, value) => [...select.options].some(option => option.value === value) ? value : '';
 const readURL = () => {
  const params = new URLSearchParams(location.search), pathPage = location.pathname.match(/^\/blog\/page\/(\d+)\/?$/);
  return {search: params.get('search') || '', category: validOption(topic, params.get('category') || ''), year: validOption(year, params.get('year') || ''), page: Number(params.get('page') || pathPage?.[1] || 1)};
 };
 const readControls = page => ({search: input.value.trim(), category: topic.value, year: year.value, page});
 const setControls = state => {input.value = state.search; topic.value = state.category; year.value = state.year;};
 let indexPromise, revision = 0, pending, debounce;
 const load = () => {
  if (!indexPromise) indexPromise = fetch(root.dataset.index, {cache:'no-cache'}).then(response => {
   if (!response.ok) throw new Error('Archive unavailable');
   return response.json();
  }).then(entries => {
   if (!Array.isArray(entries) || entries.some(entry => typeof entry.html !== 'string' || typeof entry.search !== 'string')) throw new Error('Invalid archive');
   return entries;
  }).catch(reason => {indexPromise = null; throw reason;});
  return indexPromise;
 };
 function navigation(state, pages) {
  nav.replaceChildren();
  if (pages <= 1) return;
  const add = (page, label, disabled = false) => {
   const node = document.createElement(disabled ? 'span' : 'a'); node.textContent = label;
   if (disabled) node.setAttribute('aria-disabled','true');
   else {
    node.href = stateURL({...state, page}); node.dataset.journalPage = String(page);
    if (/^\d+$/.test(label)) {
     node.setAttribute('aria-label','Page '+page);
     if (page === state.page) node.setAttribute('aria-current','page');
    }
   }
   nav.append(node);
  };
  add(state.page-1, 'Previous', state.page === 1);
  let previous = 0;
  for (const number of pageNumbers(state.page, pages)) {
   if (previous && number > previous+1) {const gap = document.createElement('span'); gap.textContent='…'; gap.setAttribute('aria-hidden','true'); nav.append(gap);}
   add(number, String(number)); previous = number;
  }
  add(state.page+1, 'Next', state.page === pages);
 }
 function updateURL(state, mode) {
  if (!mode) return;
  const url = stateURL(state);
  if (location.pathname + location.search !== url) history[mode === 'push' ? 'pushState' : 'replaceState'](null, '', url);
 }
 function restoreScroll() {
  const back = performance.getEntriesByType('navigation')[0]?.type === 'back_forward';
  let fromArticle = false;
  try { fromArticle = new URL(document.referrer).pathname.startsWith('/post/'); } catch { /* Direct visit. */ }
  if (!back && !fromArticle) return;
  const value = Number(stored('journal-scroll:' + location.pathname + location.search));
  if (Number.isFinite(value) && value >= 0) requestAnimationFrame(() => window.scrollTo({top:value, behavior:'instant'}));
 }
 async function apply(state, mode, scroll = false, restore = false) {
  const current = ++revision; pending = {state, mode, scroll, restore};
  error.hidden = true; grid.setAttribute('aria-busy','true');
  try {
   const result = selectEntries(await load(), state, size);
   if (current !== revision) return;
   state = {...state, page:result.page};
   const fragment = document.createDocumentFragment();
   for (const entry of result.items) {
    // HTML comes exclusively from the same escaped server renderer as static pages.
    const template = document.createElement('template'); template.innerHTML = entry.html;
    fragment.append(template.content);
   }
   grid.replaceChildren(fragment);
   const start = (result.page-1)*size+1, end = start+result.items.length-1;
   count.textContent = result.total ? `Showing ${start}–${end} of ${result.total} ${result.total===1?'article':'articles'}` : '0 articles';
   empty.hidden = result.total > 0;
   navigation(state,result.pages); updateURL(state,mode);
   if (scroll) {
    count.focus({preventScroll:true});
    window.scrollTo({top:Math.max(0,root.getBoundingClientRect().top+scrollY-110),behavior:'instant'});
   }
   if (restore) restoreScroll();
  } catch {
   if (current === revision) error.hidden = false;
  } finally { if (current === revision) grid.removeAttribute('aria-busy'); }
 }
 input.addEventListener('input', () => {clearTimeout(debounce); debounce = setTimeout(() => apply(readControls(1),'replace'),150);});
 input.addEventListener('search', () => {clearTimeout(debounce); apply(readControls(1),'replace');});
 for (const select of [topic,year]) select.addEventListener('change', () => {clearTimeout(debounce); apply(readControls(1),'push');});
 nav.addEventListener('click', event => {
  const link = event.target.closest('a[data-journal-page]');
  if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button > 0) return;
  event.preventDefault(); clearTimeout(debounce);
  apply(readControls(Number(link.dataset.journalPage)),'push',true);
 });
 document.querySelector('#journal-retry').addEventListener('click', () => {if (pending) apply(pending.state,pending.mode,pending.scroll,pending.restore);});
 grid.addEventListener('click', event => {
  if (!event.target.closest('[data-post]')) return;
  save('journal-return',location.pathname+location.search);
  save('journal-scroll:'+location.pathname+location.search,String(scrollY));
 });
 window.addEventListener('pagehide', () => save('journal-scroll:'+location.pathname+location.search,String(scrollY)));
 window.addEventListener('popstate', () => {clearTimeout(debounce); const state=readURL(); setControls(state); apply(state,null,false,true);});
 window.addEventListener('pageshow', event => {if (event.persisted) restoreScroll();});
 const initial = readURL(); setControls(initial);
 if (initial.search || initial.category || initial.year || initial.page !== initialPage) apply(initial,'replace',false,true);
 else {navigation(initial,Math.max(1,Math.ceil(total/size))); restoreScroll();}
})();
