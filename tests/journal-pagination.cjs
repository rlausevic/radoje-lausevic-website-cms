const assert = require('node:assert/strict');
const fs = require('node:fs');
const {selectEntries, normalize, pageNumbers, stateURL} = require('../dist/assets/journal.js');
const entries = Array.from({length:40},(_,i)=>({year:String(2026-Math.floor(i/10)),topic:i%2?'Blue':'Climate',search:`Article ${i} Laušević bodyneedle-${i}`,html:`<a>${i}</a>`}));
const state = {search:'',category:'',year:'',page:1};
assert.deepEqual(selectEntries(entries,state).items,entries.slice(0,12));
assert.deepEqual(selectEntries(entries,{...state,page:4}).items,entries.slice(36));
assert.equal(selectEntries(entries,{...state,page:999}).page,4);
for (const page of [0,-1,NaN,Infinity,1.5]) assert.equal(selectEntries(entries,{...state,page}).page,1);
// Match a body-only term outside the first page and fold Serbian diacritics.
assert.equal(selectEntries(entries,{...state,search:'lausevic bodyneedle-39'}).items[0],entries[39]);
const filtered = selectEntries(entries,{...state,category:'Blue',year:'2024'});
assert.equal(filtered.total,5); assert.equal(filtered.pages,1);
assert.ok(filtered.items.every(x=>x.year==='2024'&&x.topic==='Blue'));
assert.equal(selectEntries(entries,{...state,search:'missing'}).total,0);
assert.equal(selectEntries([],state).pages,1);
assert.equal(normalize('Đurović LAUŠEVIĆ'),'durovic lausevic');
assert.deepEqual(pageNumbers(50,100),[1,49,50,51,100]);
const url=stateURL({...state,search:'Blue Pass & skills',category:'Blue',year:'2024',page:2});
const parsed=new URL(url,'https://example.org');
assert.equal(parsed.searchParams.get('search'),'Blue Pass & skills');
assert.equal(parsed.searchParams.get('page'),'2');
assert.equal(stateURL(state),'/blog/');
for(const base of ['/video/','/galleries/']) {
 const url=stateURL({...state,year:'2026',page:2},base);assert.ok(url.startsWith(base+'?'));assert.ok(url.includes('page=2'));
}
// Exercise the real generated global index as well as synthetic records.
if (process.argv[2]) {
 const real=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
 assert.equal(selectEntries(real,state).items.length,Math.min(12,real.length));
 for(const entry of real){
  const result=selectEntries(real,{...state,category:entry.topic,year:entry.year});
  assert.ok(result.total>0);
 }
}
console.log('Journal pagination/search tests passed.');
