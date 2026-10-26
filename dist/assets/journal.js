/* Shared Journal, Video and Galleries pagination; CMS records and detail URLs stay intact. */
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
 const stateURL = (state, base = '/blog/') => {
  const params = new URLSearchParams();
  if (state.search) params.set('search', state.search);
  if (state.category) params.set('category', state.category);
  if (state.year) params.set('year', state.year);
  if (state.page > 1) params.set('page', state.page);
  return base + (params.size ? '?' + params : '');
 };
 if (typeof module !== 'undefined') module.exports = {normalize, selectEntries, pageNumbers, stateURL};
 if (typeof document === 'undefined') return;
 const stored = key => {try { return sessionStorage.getItem(key); } catch { return null; }};
 const save = (key, value) => {try { sessionStorage.setItem(key, value); } catch { /* Storage may be disabled. */ }};
 const isArchivePath = (path, base) => path === base || path === base.slice(0,-1) || (path.startsWith(base+'page/') && /^\d+\/?$/.test(path.slice((base+'page/').length)));
 const safeReturn = base => {
  try {
   const url = new URL(stored('archive-return:'+base) || (base==='/blog/' ? stored('journal-return') : '') || '', location.origin);
   return url.origin === location.origin && isArchivePath(url.pathname,base) ? url.pathname + url.search : null;
  } catch { return null; }
 };
 document.querySelectorAll('[data-archive-back]').forEach(link => {
  const back = safeReturn(link.dataset.archiveBack); if (back) link.href = back;
 });
 const root = document.querySelector('[data-paginated-archive]');
 if (!root) return;
 const base=root.dataset.base, prefix=root.dataset.prefix;
 const singular=root.dataset.singular, plural=root.dataset.plural;
 const input = document.querySelector('#'+prefix+'-search'), topic = document.querySelector('#'+prefix+'-category'), year = document.querySelector('#'+prefix+'-year');
 const grid = root.querySelector('[data-archive-results]'), count = root.querySelector('[data-archive-count]'), empty = root.querySelector('[data-archive-empty]');
 const nav = root.querySelector('[data-archive-pagination]'), error = root.querySelector('[data-archive-error]');
 const size = Number(root.dataset.pageSize), total = Number(root.dataset.total), initialPage = Number(root.dataset.page);
 const validOption = (select, value) => [...select.options].some(option => option.value === value) ? value : '';
 const readURL = () => {
  const params = new URLSearchParams(location.search), pathPage = location.pathname.startsWith(base+'page/') ? location.pathname.slice((base+'page/').length).match(/^(\d+)\/?$/) : null;
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
    node.href = stateURL({...state, page},base); node.dataset.journalPage = String(page);
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
  const url = stateURL(state,base);
  if (location.pathname + location.search !== url) history[mode === 'push' ? 'pushState' : 'replaceState'](null, '', url);
 }
 function restoreScroll() {
  const back = performance.getEntriesByType('navigation')[0]?.type === 'back_forward';
  let fromArticle = false;
  try { const path=new URL(document.referrer).pathname; fromArticle=path.startsWith(root.dataset.detailPrefix)&&!isArchivePath(path,base); } catch { /* Direct visit. */ }
  if (!back && !fromArticle) return;
  const value = Number(stored('archive-scroll:'+base+location.pathname+location.search));
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
   count.textContent = result.total ? `Showing ${start}–${end} of ${result.total} ${result.total===1?singular:plural}` : '0 '+plural;
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
 root.querySelector('[data-archive-retry]').addEventListener('click', () => {if (pending) apply(pending.state,pending.mode,pending.scroll,pending.restore);});
 grid.addEventListener('click', event => {
  const link=event.target.closest('a');
  if (!link || !link.getAttribute('href')?.startsWith(root.dataset.detailPrefix)) return;
  save('archive-return:'+base,location.pathname+location.search);
  save('archive-scroll:'+base+location.pathname+location.search,String(scrollY));
 });
 window.addEventListener('pagehide', () => save('archive-scroll:'+base+location.pathname+location.search,String(scrollY)));
 window.addEventListener('popstate', () => {clearTimeout(debounce); const state=readURL(); setControls(state); apply(state,null,false,true);});
 window.addEventListener('pageshow', event => {if (event.persisted) restoreScroll();});
 const initial = readURL(); setControls(initial);
 if (initial.search || initial.category || initial.year || initial.page !== initialPage) apply(initial,'replace',false,true);
 else {navigation(initial,Math.max(1,Math.ceil(total/size))); restoreScroll();}
})();
