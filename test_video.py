"""Check shared CMS sources, archive routes, search and removable video content."""
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class VideoCMS(unittest.TestCase):
 def test_shared_sources_and_video_routes(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   def read(name):return json.loads((root/'content/cms'/name).read_text())
   def save(name,data):(root/'content/cms'/name).write_text(json.dumps(data))
   def build(ok=True):
    result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True)
    self.assertEqual(result.returncode==0,ok,result.stderr)
   services=read('expertise.json');services['services'].reverse();services['services'][0].update(title='Shared expertise',motto='Shared motto',summary='Homepage expertise excerpt',description='<p>Expertise full text</p>')
   save('expertise.json',services);about=read('about.json');about['recommendations'].reverse();about['recommendations'][0].update(author='Shared recommendation author',summary='Homepage recommendation excerpt',body='<p>Recommendation full text</p>');save('about.json',about)
   archive=read('videos.json');archive['items'].reverse();archive['items'][0].update(title='Shared video title',excerpt='Homepage video excerpt',body='<p>Unique searchable detail</p>');save('videos.json',archive);build()
   home=(root/'dist/index.html').read_text();page=(root/'dist/about/index.html').read_text();videos=(root/'dist/video/index.html').read_text()
   for value in ['Shared expertise','Shared motto','Homepage expertise excerpt','Shared recommendation author','Homepage recommendation excerpt','Shared video title','Homepage video excerpt']:self.assertIn(value,home)
   self.assertEqual(home.count('data-video '),3);self.assertEqual(home.count('<blockquote>'),2)
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
