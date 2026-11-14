"""End-to-end generation for project selection and shared network PDF replacement."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from network_data import network_document
ROOT=Path(__file__).resolve().parent
class Editing(unittest.TestCase):
 def test_multi_topic_generation_and_shared_pdf_replacement(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   config=json.loads((root/'.pages.yml').read_text());schemas={x['name']:x for x in config['content']}
   fields={x['name']:x for x in schemas['projects']['fields'][0]['fields']}
   self.assertTrue(fields['topic']['options']['multiple']);self.assertFalse(fields['path'].get('required',False))
   options=next(x for x in schemas['network']['fields'] if x['name']=='document')['options']
   self.assertTrue(options['multiple']);self.assertEqual(options['extensions'],['pdf'])
   source=root/'content/cms/projects.json';data=json.loads(source.read_text());paths=[p['path'] for p in data['items']]
   topics=fields['topic']['options']['values'][:2]
   data['items'].append({'title':'REDEEM-TEST','topic':topics,'summary':'Unique multi topic fixture','assignment_ongoing':True})
   # A legacy scalar selection must also survive the synchronization migration.
   data['items'][0]['topic']=topics[0];source.write_text(json.dumps(data))
   subprocess.run([sys.executable,'scripts/sync_projects.py'],cwd=root,check=True)
   saved=json.loads(source.read_text());new=next(p for p in saved['items'] if p['title']=='REDEEM-TEST')
   self.assertEqual(new['path'],'/project/REDEEM-TEST')
   self.assertTrue(all(isinstance(p['topic'],list) for p in saved['items']))
   self.assertTrue(set(paths)<={p['path'] for p in saved['items']})
   before=source.read_bytes();subprocess.run([sys.executable,'scripts/sync_projects.py'],cwd=root,check=True)
   self.assertEqual(source.read_bytes(),before)
   network=root/'content/cms/network.json';n=json.loads(network.read_text());original=n['document'][0] if isinstance(n['document'],list) else n['document']
   replacement='/assets/network-replacement-test.pdf'
   shutil.copyfile(root/'dist'/original.lstrip('/'),root/'dist'/replacement.lstrip('/'))
   for document,expected in [(original,original),([original,replacement],replacement),(None,None)]:
    if document is None:n.pop('document',None)
    else:n['document']=document
    network.write_text(json.dumps(n));subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
    for page in ['about','work-experience']:
     html=(root/'dist'/page/'index.html').read_text()
     links=re.findall(r'<a class="button" href="([^"]+)" download>Download the full network list ↓</a>',html)
     self.assertEqual(links,[expected] if expected else [])
     if isinstance(document,list):self.assertNotIn('href="'+str(document)+'"',html)
   index=json.loads((root/'dist/projects/archive-index.json').read_text())
   entry=next(x for x in index if 'Unique multi topic fixture' in x['html'])
   self.assertEqual(entry['topic'],topics)
   self.assertIn('data-categories="'+'|'.join(topics)+'"',entry['html'])
   self.assertTrue(all(t.lower() in entry['search'] for t in topics))
   expertise=(root/'dist/expertise/index.html').read_text()
   for topic in topics:
    section=next(s for s in expertise.split('<details class="expertise-card"') if '<h2>'+topic+'</h2>' in s)
    self.assertIn('href="/project/REDEEM-TEST"',section)
 def test_pdf_selection_ignores_other_formats(self):
  self.assertEqual(network_document(['/assets/old.pdf','/assets/new.PDF','/assets/readme.docx']),'/assets/new.PDF')
  for value in [None,[],['/assets/readme.docx']]:self.assertEqual(network_document(value),'')
if __name__=='__main__':unittest.main()
