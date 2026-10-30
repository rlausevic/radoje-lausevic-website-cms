import json,unittest,subprocess,sys,tempfile
from pathlib import Path
from metrics import Metrics
ROOT=Path(__file__).resolve().parent
class MetricsTests(unittest.TestCase):
 def test_build_coverage(self):
  subprocess.run([sys.executable,'build.py'],cwd=ROOT,check=True,capture_output=True)
  entries=json.loads((ROOT/'dist/_metrics/catalog.json').read_text())
  published=[json.loads(p.read_text()) for p in (ROOT/'content/cms/posts').glob('*.json') if json.loads(p.read_text()).get('published',True)]
  self.assertEqual(sum(v['kind']=='post' for v in entries.values()),len(published))
  for key,item in entries.items():
   if item['kind'] not in {'post','video','gallery','project'}:continue
   html=(ROOT/'dist'/item['path'].lstrip('/')/'index.html').read_text()
   self.assertIn('data-metric-view="'+key+'"',html)
   self.assertEqual('data-metric-public' in html,item['public'])
  for path in ['blog','video','galleries','projects','about']:
   self.assertNotIn('data-metric-view=',(ROOT/'dist'/path/'index.html').read_text())
 def test_identity_survives_title_and_url_edit(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);source=root/'content/cms/posts/entry.json';source.parent.mkdir(parents=True)
   source.write_text(json.dumps({'title':'Before','path':'/post/before'}))
   old=Metrics(root).page('/post/before','Before')
   source.write_text(json.dumps({'title':'After','path':'/post/after'}))
   self.assertEqual(old,Metrics(root).page('/post/after','After'))
if __name__=='__main__':unittest.main()
