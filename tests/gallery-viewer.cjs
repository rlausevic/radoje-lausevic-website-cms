'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('dist/assets/site.js','utf8');
function fixture(count){
 const node=()=>({hidden:false,focus(options){this.focused=options;},events:{},addEventListener(name,fn){this.events[name]=fn;},fire(name,event={}){this.events[name]?.(event);}});
 const photos=Array.from({length:count},(_,i)=>Object.assign(node(),{dataset:{src:`/photo-${i}.webp`,caption:`Photo ${i}`}}));
 const image={},caption={},counter={},previous=node(),next=node(),close=node(),stage=node(),dialog=node();
 stage.setPointerCapture=id=>stage.captured=id;
 Object.assign(dialog,{open:false,showModal(){this.open=true;},close(){this.open=false;this.fire('close');}});
 const nodes={'img':image,'#gallery-caption':caption,'[data-gallery-counter]':counter,'[data-gallery-previous]':previous,'[data-gallery-next]':next,'[data-gallery-close]':close,'.gallery-stage':stage};
 dialog.querySelector=s=>nodes[s];
 const reveal=node(),more=node(),visibleCount=node();
 reveal.hidden=true;reveal.querySelector=s=>s==='[data-gallery-more]'?more:visibleCount;
 const window={scrollX:0,scrollY:520,scrollTo(position){this.restored=position;}};
 vm.runInNewContext(source,{document:{querySelector:s=>s==='#gallery-dialog'?dialog:s==='[data-gallery-reveal]'&&count>12?reveal:null,querySelectorAll:s=>s==='[data-gallery]'?photos:[]},window,location:{pathname:'',search:''},URLSearchParams});
 return {photos,image,caption,counter,previous,next,close,stage,dialog,reveal,more,visibleCount,window};
}
const f=fixture(3);f.photos[1].fire('click');
assert.equal(f.dialog.open,true);assert.equal(f.counter.textContent,'2 / 3');assert.equal(f.image.src,'/photo-1.webp');
f.next.fire('click');assert.equal(f.counter.textContent,'3 / 3');assert.equal(f.caption.textContent,'Photo 2');assert.equal(f.image.alt,'Photo 2');
f.next.fire('click');assert.equal(f.counter.textContent,'1 / 3');
f.previous.fire('click');assert.equal(f.counter.textContent,'3 / 3');
let prevented=false;f.dialog.fire('keydown',{key:'ArrowRight',preventDefault(){prevented=true;}});assert.equal(prevented,true);assert.equal(f.counter.textContent,'1 / 3');
f.dialog.fire('keydown',{key:'ArrowLeft',preventDefault(){}});assert.equal(f.counter.textContent,'3 / 3');
f.dialog.fire('keydown',{key:'ArrowRight',ctrlKey:true});assert.equal(f.counter.textContent,'3 / 3');
function swipe(x,y,options={}){
 f.stage.fire('pointerdown',{pointerType:'touch',isPrimary:true,pointerId:1,clientX:100,clientY:100,...options});
 f.stage.fire('pointerup',{pointerId:1,clientX:100+x,clientY:100+y});
}
swipe(-80,5);assert.equal(f.counter.textContent,'1 / 3');
swipe(80,5);assert.equal(f.counter.textContent,'3 / 3');
swipe(-80,100);assert.equal(f.counter.textContent,'3 / 3');
swipe(-20,0);assert.equal(f.counter.textContent,'3 / 3');
swipe(-80,0,{isPrimary:false});assert.equal(f.counter.textContent,'3 / 3');
swipe(-80,0,{pointerType:'mouse'});assert.equal(f.counter.textContent,'3 / 3');
f.stage.fire('pointerdown',{pointerType:'touch',isPrimary:true,pointerId:2,clientX:100,clientY:100});f.stage.fire('pointercancel');f.stage.fire('pointerup',{pointerId:2,clientX:0,clientY:100});assert.equal(f.counter.textContent,'3 / 3');
f.close.fire('click');assert.equal(f.dialog.open,false);
f.photos[0].fire('click');assert.equal(f.counter.textContent,'1 / 3');f.dialog.fire('click',{target:f.image});assert.equal(f.dialog.open,true);f.dialog.fire('click',{target:f.dialog});assert.equal(f.dialog.open,false);
const single=fixture(1);single.photos[0].fire('click');assert.equal(single.counter.textContent,'1 / 1');assert.equal(single.previous.disabled,true);assert.equal(single.next.disabled,true);
assert.doesNotThrow(()=>fixture(0));
console.log('Gallery viewer: navigation, wrapping, captions, counter, swipes and single-photo cases passed.');

for(const count of [0,1,12,13,24,25,33,44]){
 const g=fixture(count);
 assert.equal(g.photos.filter(p=>!p.hidden).length,Math.min(count,12));
 if(count<=12){assert.equal(g.reveal.hidden,true);continue;}
 assert.equal(g.visibleCount.textContent,`Showing 12 of ${count} photos`);
 // Cross the initial thumbnail boundary while the grid remains at 12.
 g.photos[11].fire('click');g.next.fire('click');
 assert.equal(g.counter.textContent,`13 / ${count}`);
 assert.equal(g.photos[12].hidden,true);
 g.previous.fire('click');assert.equal(g.counter.textContent,`12 / ${count}`);
 g.close.fire('click');assert.equal(g.photos[11].focused.preventScroll,true);
 assert.equal(g.window.restored.top,520);
 let shown=12;
 while(shown<count){
  const firstNew=shown;g.more.fire('click');shown=Math.min(shown+12,count);
  assert.equal(g.photos.filter(p=>!p.hidden).length,shown);
  assert.equal(g.visibleCount.textContent,`Showing ${shown} of ${count} photos`);
  assert.equal(g.photos[firstNew].focused.preventScroll,true);
  assert.equal(g.more.hidden,shown===count);
 }
 g.photos[count-1].fire('click');g.next.fire('click');assert.equal(g.counter.textContent,`1 / ${count}`);
}
console.log('Gallery reveal: 12-photo batches, hidden-photo viewer navigation, final batch and focus/scroll restoration passed.');
