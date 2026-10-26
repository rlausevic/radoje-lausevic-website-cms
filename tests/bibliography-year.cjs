const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const search={value:'',addEventListener:(name,fn)=>{search.run=fn;}};
const category={value:'',options:['','Publications','Articles'].map(value=>({value})),addEventListener:(name,fn)=>{category.run=fn;}};
const year={value:'',options:['','1993','1994','2024','undated'].map(value=>({value})),addEventListener:(name,fn)=>{year.run=fn;}};
const count={},empty={},cards=[
 {dataset:{search:'Water 1993/94',categories:'Publications',years:'1993|1994'}},
 {dataset:{search:'Other 2024',categories:'Articles',years:'2024'}},
 {dataset:{search:'Undated manual',categories:'Publications',years:'undated'}}
];
const groups=[{querySelectorAll:()=>[cards[0],cards[2]]},{querySelectorAll:()=>[cards[1]]}];
const nodes={'#bibliography-search':search,'#bibliography-category':category,'#bibliography-year':year,'#bibliography-result-count':count,'#no-bibliography':empty};
let url;
vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{document:{querySelector:s=>nodes[s]||null,querySelectorAll:s=>s==='[data-bibliography]'?cards:s==='[data-archive-group]'?groups:[]},location:{search:'?year=1994',pathname:'/bibliography/',hash:'#citation'},history:{replaceState:(a,b,value)=>{url=value;}},URLSearchParams});
assert.equal(count.textContent,'1 bibliography item');assert.equal(cards[0].hidden,false);assert.equal(groups[1].hidden,true);
year.value='2024';year.run();assert.equal(cards[1].hidden,false);
category.value='Publications';category.run();assert.equal(empty.hidden,false);assert.equal(count.textContent,'0 bibliography items');
year.value='undated';year.run();assert.equal(cards[2].hidden,false);assert.ok(url.includes('year=undated'));assert.ok(url.endsWith('#citation'));
search.value='missing';search.run();assert.equal(empty.hidden,false);
search.value='';category.value='';year.value='';year.run();assert.equal(count.textContent,'3 bibliography items');assert.equal(empty.hidden,true);
console.log('Bibliography year/range/category/search tests passed.');
