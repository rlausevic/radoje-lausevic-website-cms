"""Gallery migration, shared previews, CMS topic synchronization and combined filters."""
import copy,html,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class Archives(unittest.TestCase):
 def test_gallery_roundtrip_and_topics(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   def read(p):return json.loads((root/p).read_text())
   def save(p,d):(root/p).write_text(json.dumps(d))
   data=read('content/cms/gallery.json');original=copy.deepcopy(data['albums'][0]);data['albums']=[original];data.update(label='Archive CMS label',heading='Archive CMS heading',lead='Archive CMS introduction')
   for index,date in enumerate(['2026-01-01','2026-03-01','2026-02-01']):
    album=copy.deepcopy(original);album.update(path=f'/gallery/roundtrip-{index}',title=f'Gallery {index}',date=date,topic='Shared topic',summary=f'Preview {index}',body=f'<p>Full gallery {index} hiddenneedle</p>');data['albums'].append(album)
   save('content/cms/gallery.json',data)
   expertise=read('content/cms/expertise.json');expertise['services'][0]['title']='Shared topic';save('content/cms/expertise.json',expertise)
   post_file=next((root/'content/cms/posts').glob('*.json'));post=json.loads(post_file.read_text());post['topic']='Shared topic';post_file.write_text(json.dumps(post))
   videos=read('content/cms/videos.json');videos['items'][0]['topic']='Shared topic';save('content/cms/videos.json',videos)
   subprocess.run([sys.executable,'scripts/sync_expertise.py'],cwd=root,check=True,capture_output=True)
   schema=read('.pages.yml');by={x['name']:x for x in schema['content']}
   for name,list_name in [('projects','items'),('posts',None),('videos','items'),('gallery','albums')]:
    fields=by[name]['fields']
    if list_name:fields=next(x for x in fields if x['name']==list_name)['fields']
    self.assertIn('Shared topic',next(x for x in fields if x['name']=='topic')['options']['values'])
   self.assertEqual(by['posts']['fields'][1]['name'],'topic')
   def build():subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   build()
   for route in ['index.html','insights/index.html']:
    page=(root/'dist'/route).read_text();indices=[1] if route=='index.html' else [1,2,0]
    self.assertEqual(page.count('data-album '),len(indices))
    self.assertEqual([page.index(f'>Gallery {i}</h3>') for i in indices],sorted(page.index(f'>Gallery {i}</h3>') for i in indices))
    self.assertNotIn(original['path'],page)
   archive=(root/'dist/galleries/index.html').read_text();self.assertEqual(archive.count('data-album '),4)
   for v in ['Archive CMS label','Archive CMS heading','Archive CMS introduction','hiddenneedle','Shared topic']:self.assertIn(v,archive)
   album=(root/'dist/gallery/flowers-of-my-mediterranean-garden/index.html').read_text()
   for photo in original['photos']:self.assertIn(html.escape(photo['caption'],quote=True),album)
   class GalleryMarkup(HTMLParser):
    def __init__(self):super().__init__();self.previews=[];self.enlarged=[]
    def handle_starttag(self,tag,attrs):
     attrs=dict(attrs)
     if tag=='button' and 'data-gallery' in attrs:self.enlarged.append(attrs['data-src'])
     if tag=='img' and attrs.get('src','').startswith('/media/gallery/'):
      self.previews.append(attrs['src']);self.assert_srcset=attrs.get('srcset')
   markup=GalleryMarkup();markup.feed(album)
   self.assertEqual(len(markup.previews),len(original['photos']))
   self.assertEqual(len(markup.enlarged),len(original['photos']))
   self.assertTrue(markup.assert_srcset)
   self.assertTrue(set(markup.previews).isdisjoint(markup.enlarged))
   for url in markup.previews+markup.enlarged:self.assertTrue((root/'dist'/url.lstrip('/')).is_file())
   for route in ['index.html','insights/index.html','galleries/index.html']:
    page=(root/'dist'/route).read_text();self.assertIn('/media/gallery/',page);self.assertIn('srcset=',page)
   self.assertEqual(album.count('data-gallery '),len(original['photos']))
   for route,selector in [('blog','post-category'),('video','video-category'),('galleries','gallery-category')]:
    page=(root/'dist'/route/'index.html').read_text();self.assertIn(f'id="{selector}"',page);self.assertIn('data-categories="Shared topic"',page)
   data['albums']=[original];save('content/cms/gallery.json',data);build();self.assertFalse((root/'dist/gallery/roundtrip-0').exists())
   data['albums']=[];save('content/cms/gallery.json',data);build();self.assertIn('0 galleries',(root/'dist/galleries/index.html').read_text())
 def test_combined_search_for_all_archives(self):
  subprocess.run(['node','-e',r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
for(const [prefix,attr,count,empty] of [['post','post','#result-count','#no-results'],['video','video','#video-result-count','#no-videos'],['gallery','album','#gallery-result-count','#no-galleries']]){
 const input={value:'',addEventListener:(event,fn)=>input.run=fn};
 const category={value:'',options:[{value:''},{value:'Blue economy'}],addEventListener:(event,fn)=>category.run=fn};
 const nodes={[`#${prefix}-search`]:input,[`#${prefix}-category`]:category,[count]:{},[empty]:{}};
 const cards=[{dataset:{search:'Školski detailed needle',categories:'Blue economy'}},{dataset:{search:'Skolski needle',categories:'Governance'}}];
 vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{document:{querySelector:s=>nodes[s]||null,querySelectorAll:s=>s===`[data-${attr}]`?cards:[]},location:{search:'?search=skolski%20needle&category=Blue%20economy'},URLSearchParams});
 assert.equal(cards[0].hidden,false);assert.equal(cards[1].hidden,true);
 input.value='unmatched';input.run();assert.equal(nodes[empty].hidden,false);
 input.value='';category.value='';category.run();assert.equal(cards[0].hidden,false);assert.equal(cards[1].hidden,false);assert.equal(nodes[empty].hidden,true);
}
"""],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
