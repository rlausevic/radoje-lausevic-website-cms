"""Check shared CMS sources, archive routes, search and removable video content."""
import json,re,hashlib,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from content_archives import ARCHIVES,read_archive,write_archive
ROOT=Path(__file__).resolve().parent
class VideoCMS(unittest.TestCase):
 def test_multiple_topics_previews_details_filter_and_sync(self):
  from content_archives import video_path
  from scripts.sync_related_content import sync
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   def field():
    config=json.loads((root/'.pages.yml').read_text())
    return next(x for x in next(x for x in config['content'] if x['name']=='video_entries')['fields'] if x['name']=='topic')
   self.assertTrue(field()['options']['multiple']);topics=field()['options']['values'][:2]
   folder=root/'content/cms/video_entries';sample=read_archive(root,'videos')['items'][0]
   item=dict(sample,title='Multiple video topics fixture',date='2099-01-02',link='https://example.org/multiple-video-topics',topic=topics,body='<p>Unique video topics body</p>')
   source=folder/'multiple-topics-test.json';source.write_text(json.dumps(item))
   legacy=folder/'legacy-topic-test.json';legacy.write_text(json.dumps(dict(item,title='Legacy video topic',date='2097-01-02',link='https://example.org/legacy-video-topic',topic=topics[0])))
   optional=folder/'no-topic-test.json';no_topic=dict(item,title='No topic video',date='2098-01-02',link='https://example.org/no-video-topic');no_topic.pop('topic');optional.write_text(json.dumps(no_topic))
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   for name in ['index.html','insights/index.html','video/index.html']:
    text=(root/'dist'/name).read_text();self.assertIn('data-categories="'+'|'.join(topics)+'"',text)
    for topic in topics:self.assertIn('<span class="post-topic">'+topic+'</span>',text)
   detail=(root/'dist'/video_path(item['link']).strip('/')/'index.html').read_text()
   self.assertIn(' · VIDEO · '+' · '.join(topics),detail);self.assertIn('href="'+item['link']+'"',detail)
   meta=re.search(r'<p class="article-meta">(.*?)</p>',(root/'dist'/video_path(no_topic['link']).strip('/')/'index.html').read_text())[1]
   self.assertEqual(re.sub(r'<[^>]+>','',meta),'Jan 02, 2098 · VIDEO')
   index=json.loads((root/'dist/video/archive-index.json').read_text());entry=next(x for x in index if video_path(item['link']) in x['html'])
   self.assertEqual(entry['topic'],topics)
   for topic in topics:self.assertIn(topic.lower(),entry['search'])
   subprocess.run(['node','-e',r"""
const fs=require('fs'),assert=require('assert');
const {selectEntries}=require('./dist/assets/journal.js');
const entries=JSON.parse(fs.readFileSync('dist/video/archive-index.json','utf8'));
const fixture=entries.find(x=>x.search.includes('unique video topics body'));
for(const category of fixture.topic){
 const result=selectEntries(entries,{category,year:'2099',search:'unique video topics body',page:1});
 assert.equal(result.total,1);assert.equal(result.items[0],fixture);
}
assert.equal(selectEntries(entries,{category:'Missing topic',search:'unique video topics body'}).total,0);
"""],cwd=root,check=True)
   sync(root);self.assertEqual(json.loads(source.read_text()),item)
   self.assertEqual(json.loads(legacy.read_text())['topic'],[topics[0]])
   self.assertNotIn('topic',json.loads(optional.read_text()))
   before={p.name:p.read_bytes() for p in folder.glob('*.json')};sync(root)
   self.assertEqual({p.name:p.read_bytes() for p in folder.glob('*.json')},before)
   subprocess.run([sys.executable,'scripts/sync_expertise.py'],cwd=root,check=True)
   self.assertTrue(field()['options']['multiple'])
 def test_shared_sources_and_video_routes(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   def read(name):return read_archive(root,Path(name).stem) if Path(name).stem in ARCHIVES else json.loads((root/'content/cms'/name).read_text())
   def save(name,data):
    if Path(name).stem in ARCHIVES:write_archive(root,Path(name).stem,data)
    else:(root/'content/cms'/name).write_text(json.dumps(data))
   def build(ok=True):
    result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True)
    self.assertEqual(result.returncode==0,ok,result.stderr)
   services=read('expertise.json');services['services'].reverse();services['services'][0].update(title='Shared expertise',motto='Shared motto',summary='Homepage expertise excerpt',description='<p>Expertise full text</p>')
   save('expertise.json',services);about=read('about.json');about['recommendations'].reverse();about['recommendations'][0].update(author='Shared recommendation author',summary='Homepage recommendation excerpt',body='<p>Recommendation full text</p>');save('about.json',about)
   archive=read('videos.json');archive['items'].reverse();archive['items'][0].update(title='Shared video title',date='2099-01-01',excerpt='Homepage video excerpt',body='<p>Unique searchable detail</p>');save('videos.json',archive);build()
   home=(root/'dist/index.html').read_text();page=(root/'dist/about/index.html').read_text();videos=(root/'dist/video/index.html').read_text()
   for value in ['Shared expertise','Shared motto','Homepage expertise excerpt','Shared recommendation author','Homepage recommendation excerpt','Shared video title','Homepage video excerpt']:self.assertIn(value,home)
   self.assertEqual(home.count('data-video '),1);self.assertEqual(home.count('<blockquote>'),2)
   expected=['/video/'+hashlib.sha256(item['link'].encode()).hexdigest()[:16] for item in sorted(archive['items'],key=lambda item:item['date'],reverse=True)]
   self.assertEqual(re.findall(r'href="(/video/[a-f0-9]+)">Read more',videos),expected[:12])
   index=json.loads((root/'dist/video/archive-index.json').read_text())
   self.assertEqual([path for item in index for path in re.findall(r'href="(/video/[a-f0-9]+)">Read more',item['html'])],expected)
   self.assertEqual(re.findall(r'href="(/video/[a-f0-9]+)">Read more',home),expected[:1])
   insights=(root/'dist/insights/index.html').read_text()
   self.assertEqual(re.findall(r'href="(/video/[a-f0-9]+)">Read more',insights),expected[:3])

   self.assertIn('Expertise full text',(root/'dist/expertise/index.html').read_text());self.assertIn('Recommendation full text',page)
   self.assertIn('Unique searchable detail'.lower(),videos);self.assertIn(str(len(archive['items']))+' videos',videos)
   self.assertNotIn('Unique searchable detail',home)
   self.assertIn("/blog",home);self.assertIn('href="/video"',home)
   routes=set(p.parent.name for p in (root/'dist/video').glob('*/index.html'));self.assertEqual(len(routes),len(archive['items']))
   archive['items']=archive['items'][:1];save('videos.json',archive);build();self.assertEqual(len(list((root/'dist/video').glob('*/index.html'))),1)
   self.assertIn('1 video',(root/'dist/video/index.html').read_text())
   archive['items']=[];save('videos.json',archive);build();self.assertFalse(list((root/'dist/video').glob('*/index.html')))
   self.assertIn('0 videos',(root/'dist/video/index.html').read_text())
   self.assertIn('No videos found',(root/'dist/video/index.html').read_text())
   archive['items']=[{'title':'Invalid','date':'2026-01-01','link':'javascript:alert(1)'}];save('videos.json',archive);build(ok=False)
 def test_search_counter_and_no_results(self):
  script="""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const nodes={
 '#video-search':{value:'',addEventListener:(event,fn)=>{nodes.run=fn;}},
 '#video-result-count':{},'#no-videos':{}
};
const cards=[{dataset:{search:'aquarium conservation unique detailed text'},hidden:false},{dataset:{search:'water security'},hidden:false}];
vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{
 document:{querySelector:selector=>nodes[selector]||null,querySelectorAll:selector=>selector==='[data-video]'?cards:[]},
 location:{search:''},URLSearchParams
});
assert.equal(nodes['#video-result-count'].textContent,'2 videos');
nodes['#video-search'].value='  UNIQUE DETAILED  ';nodes.run();
assert.equal(nodes['#video-result-count'].textContent,'1 video');assert.equal(cards[1].hidden,true);
nodes['#video-search'].value='unmatched';nodes.run();assert.equal(nodes['#no-videos'].hidden,false);
nodes['#video-search'].value='';nodes.run();assert.equal(nodes['#video-result-count'].textContent,'2 videos');assert.equal(nodes['#no-videos'].hidden,true);
"""
  subprocess.run(['node','-e',script],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
