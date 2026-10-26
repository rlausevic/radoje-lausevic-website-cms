"""Real archive pages, full global search index and removal/draft behavior."""
import json,math,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class Cards(HTMLParser):
 def __init__(self):super().__init__();self.paths=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'data-post' in a:self.paths.append(a['href'])
def paths(text):
 p=Cards();p.feed(text);return p.paths
class JournalPagination(unittest.TestCase):
 def test_static_pages_and_global_index(self):
  source=[json.loads(p.read_text()) for p in (ROOT/'content/cms/posts').glob('*.json')]
  published=[p for p in source if p.get('published',True)]
  index=json.loads((ROOT/'dist/blog/archive-index.json').read_text());self.assertEqual(len(index),len(published))
  found=[]
  for number in range(1,max(1,math.ceil(len(published)/12))+1):
   file=ROOT/'dist/blog'/('index.html' if number==1 else f'page/{number}/index.html')
   text=file.read_text();cards=paths(text);self.assertLessEqual(len(cards),12);found.extend(cards)
   self.assertIn('id="post-year"',text);self.assertIn('aria-label="Journal pages"',text)
   self.assertIn('href="/insights" aria-current="true"',text)
   self.assertIn('journal.js?v=',text)
  self.assertEqual(len(found),len(set(found)));self.assertEqual(set(found),{p['path'] for p in published})
  self.assertEqual(found,[p for item in index for p in paths(item['html'])])
  subprocess.run(['node','tests/journal-pagination.cjs','dist/blog/archive-index.json'],cwd=ROOT,check=True)
 def test_new_entries_drafts_and_stale_page_removal(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   folder=root/'content/cms/posts'
   for file in folder.glob('*.json'):file.unlink()
   for n in range(25):
    (folder/f'test-{n}.json').write_text(json.dumps({'title':f'Article {n}','path':f'/post/pagination-{n}','date':f'2026-01-{n+1:02}','published':True,'excerpt':'Preview','body':'<p>Full searchable body</p>','topic':'Climate and Energy Planning'}))
   (folder/'draft.json').write_text(json.dumps({'title':'Hidden draft','path':'/post/hidden-draft','date':'2099-01-01','published':False,'excerpt':'','body':''}))
   def build():subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   build();index=json.loads((root/'dist/blog/archive-index.json').read_text());self.assertEqual(len(index),25)
   self.assertEqual([len(paths((root/'dist/blog'/name).read_text())) for name in ['index.html','page/2/index.html','page/3/index.html']],[12,12,1])
   self.assertNotIn('Hidden draft',json.dumps(index));self.assertIn('full searchable body',index[-1]['search'])
   for file in list(folder.glob('test-*.json'))[1:]:file.unlink()
   build();self.assertFalse((root/'dist/blog/page/2/index.html').exists());self.assertFalse((root/'dist/blog/page/3/index.html').exists())
   for file in folder.glob('*.json'):file.unlink()
   build();self.assertEqual(json.loads((root/'dist/blog/archive-index.json').read_text()),[])
   self.assertIn('0 articles',(root/'dist/blog/index.html').read_text())
if __name__=='__main__':unittest.main()
