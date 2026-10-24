"""CMS relationship choices, stable bibliography targets and reciprocal gallery links."""
import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from related_content import bibliography_id,load_catalog,selected_content
ROOT=Path(__file__).resolve().parent

class RelatedContent(unittest.TestCase):
 def test_stable_identifiers_and_removed_selections(self):
  item={'title':'Original title','year':'2026','authors':'Author'};item['id']=bibliography_id(item)
  renamed=dict(item,title='Renamed title',year='2027')
  self.assertEqual(bibliography_id(item),bibliography_id(renamed))
  catalog={key:{} for key in ['journal','videos','galleries','bibliography']}
  catalog['journal']['/post/valid']={'title':'Valid','href':'/post/valid'}
  related={'related_content':{'journal':['/post/valid','/post/missing','/post/valid']}}
  self.assertEqual(selected_content(related,catalog),[('journal','Journal',[catalog['journal']['/post/valid']])])
  self.assertEqual(selected_content({},catalog),[])
 def test_cms_roundtrip_and_generated_links(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   def read(name):return json.loads((root/'content/cms'/name).read_text())
   def save(name,data):(root/'content/cms'/name).write_text(json.dumps(data))
   # This test covers relationships; production image rendering is verified by the full build.
   gallery=read('gallery.json')
   for album in gallery['albums']:album['photos']=[]
   save('gallery.json',gallery)
   catalog=load_catalog(root);projects=read('projects.json')
   for project in projects['items']:project.pop('related_content',None)
   selected={key:[next(iter(values))] for key,values in catalog.items()}
   project=projects['items'][0];project['related_content']=selected;save('projects.json',projects)
   bib=read('bibliography.json');saved=copy.deepcopy(bib);bib['items'].reverse();bib['items'][0]['title']='Updated bibliography title';save('bibliography.json',bib)
   subprocess.run([sys.executable,'scripts/sync_related_content.py'],cwd=root,check=True,capture_output=True)
   cfg=json.loads((root/'.pages.yml').read_text());schema=next(c for c in cfg['content'] if c['name']=='projects')['fields'][0]['fields']
   self.assertEqual(schema[-1]['name'],'related_content')
   catalog=load_catalog(root)
   for field in schema[-1]['fields']:
    self.assertTrue(field['options']['multiple'])
    self.assertEqual({x['name'] for x in field['options']['values']},set(catalog[field['name']]))
   def build():subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   build();detail=(root/'dist'/project['path'].strip('/')/'index.html').read_text()
   self.assertIn('<h2>Related content:</h2>',detail)
   for key,values in selected.items():
    for value in values:self.assertIn('href="'+catalog[key][value]['href']+'"',detail)
   self.assertLess(detail.index('Selected results:'),detail.index('Related content:'))
   album=(root/'dist'/selected['galleries'][0].strip('/')/'index.html').read_text()
   self.assertIn('Related project',album);self.assertIn('href="'+project['path']+'"',album)
   bibliography=(root/'dist/bibliography/index.html').read_text()
   for item in bib['items']:self.assertIn('id="bibliography-'+bibliography_id(item)+'"',bibliography)
   self.assertEqual({x['id'] for x in saved['items']},{x['id'] for x in read('bibliography.json')['items']})
   unrelated=projects['items'][1]
   self.assertNotIn('Related content:',(root/'dist'/unrelated['path'].strip('/')/'index.html').read_text())
   # Stale selections never generate broken links or empty sections after content removal.
   project['related_content']={key:['removed'] for key in selected};save('projects.json',projects);build()
   detail=(root/'dist'/project['path'].strip('/')/'index.html').read_text()
   self.assertNotIn('Related content:',detail)
   album=(root/'dist'/selected['galleries'][0].strip('/')/'index.html').read_text();self.assertNotIn('Related project',album)
if __name__=='__main__':unittest.main()
