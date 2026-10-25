"""Journal uses expertise topics, with no obsolete theme metadata."""
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class JournalTopics(unittest.TestCase):
 def test_topic_search_cards_metadata_and_legacy_routes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   schema=json.loads((root/'.pages.yml').read_text());fields=next(x for x in schema['content'] if x['name']=='posts')['fields']
   self.assertNotIn('categories',[x['name'] for x in fields]);self.assertIn('topic',[x['name'] for x in fields])
   for p in (root/'content/cms/posts').glob('*.json'):self.assertNotIn('categories',json.loads(p.read_text()))
   gallery=root/'content/cms/gallery.json';g=json.loads(gallery.read_text())
   for album in g['albums']:album['photos']=[]
   gallery.write_text(json.dumps(g))
   path='/post/topic-check';topic='Environmental Research and Policy'
   item={'title':'Unique title','excerpt':'Unique excerpt','body':'<p>Unique body</p><a href="/blog/categories/old-theme">Continue</a>','topic':topic,'path':path,'date':'2099-01-02','published':True,'cover':'','categories':['ObsoleteSentinel']}
   (root/'content/cms/posts/topic-check.json').write_text(json.dumps(item))
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   archive=(root/'dist/blog/index.html').read_text()
   class Cards(HTMLParser):
    def __init__(self):super().__init__();self.cards=[]
    def handle_starttag(self,tag,attrs):
     a=dict(attrs)
     if 'data-post' in a:self.cards.append(a)
   parser=Cards();parser.feed(archive);card=next(x for x in parser.cards if x.get('href')==path)
   self.assertEqual(card['data-categories'],topic)
   for text in ['unique title','unique excerpt','unique body',topic.lower()]:self.assertIn(text,card['data-search'])
   for text in ['obsoletesentinel','2099','jan 02']:self.assertNotIn(text,card['data-search'])
   detail=(root/'dist/post/topic-check/index.html').read_text()
   self.assertIn('Jan 02, 2099 · '+topic,detail);self.assertNotIn('ObsoleteSentinel',detail)
   self.assertIn('href="/blog">Continue</a>',detail)
   for name in ['index.html','insights/index.html','blog/index.html']:
    html=(root/'dist'/name).read_text();self.assertIn('Read more',html);self.assertNotIn('Read article',html)
   self.assertIn('/blog/categories/* /blog 301',(root/'dist/_redirects').read_text())
   # An omitted optional topic does not leave an empty separator in the metadata.
   item.pop('topic');(root/'content/cms/posts/topic-check.json').write_text(json.dumps(item))
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   detail=(root/'dist/post/topic-check/index.html').read_text();self.assertIn('Jan 02, 2099</p>',detail)
if __name__=='__main__':unittest.main()
