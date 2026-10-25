"""Generated addresses, persistent slugs and unified CMS configuration."""
import json,re,tempfile,unittest
from pathlib import Path
from content_paths import collection_records
from content_archives import read_archive,write_archive
ROOT=Path(__file__).resolve().parent
class ContentPaths(unittest.TestCase):
 def test_generated_paths_are_unique_persistent_and_editable(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);folder=root/'content/cms/posts';folder.mkdir(parents=True)
   def save(name,**data):(folder/(name+'.json')).write_text(json.dumps(data))
   save('existing',title='Original title',path='/post/already-shared')
   save('a',title='Blue skills & growth!',path=None,published=False)
   save('b',title='Blue skills & growth!')
   initial=collection_records(root,'posts','post');paths=[x['path'] for x in initial]
   self.assertEqual(len(paths),len(set(paths)));self.assertIn('/post/blue-skills-growth',paths)
   collection_records(root,'posts','post',persist=True)
   self.assertEqual(paths,[x['path'] for x in collection_records(root,'posts','post')])
   data=json.loads((folder/'a.json').read_text());old=data['path'];data['title']='Completely new title';save('a',**data)
   self.assertEqual(next(x for x in collection_records(root,'posts','post') if x['title']==data['title'])['path'],old)
   data['path']='/post/manually-chosen';save('a',**data)
   self.assertIn('/post/manually-chosen',[x['path'] for x in collection_records(root,'posts','post')])
   gallery=root/'content/cms/gallery_entries';gallery.mkdir();(gallery/'a.json').write_text(json.dumps({'title':'Laušević – Field stories'}))
   self.assertEqual(collection_records(root,'gallery_entries','gallery')[0]['path'],'/gallery/lausevic-field-stories')
 def test_unified_forms_and_single_header_source(self):
  config=json.loads((ROOT/'.pages.yml').read_text());schemas={x['name']:x for x in config['content']}
  for name in ['videos','gallery','bibliography']:self.assertNotIn(name,schemas)
  for name in ['posts','video_entries','gallery_entries','bibliography_entries']:
   schema=schemas[name];self.assertEqual(schema['type'],'collection')
   self.assertEqual(schema['view']['default'],{'sort':'year' if name=='bibliography_entries' else 'date','order':'desc'})
  for name in ['posts','gallery_entries']:
   address=next(x for x in schemas[name]['fields'] if x['name']=='path')
   self.assertFalse(address.get('required',False));self.assertIsNotNone(re.fullmatch(address['pattern']['regex'],''))
  headers=next(x for x in schemas['settings']['fields'] if x['name']=='archive_pages')
  self.assertEqual({x['name'] for x in headers['fields']},{'videos','gallery','bibliography'})
  for name in ['videos','gallery','bibliography']:
   data=json.loads((ROOT/'content/cms'/ (name+'.json')).read_text());self.assertNotIn('heading',data)
   site=json.loads((ROOT/'content/cms/settings.json').read_text())
   self.assertEqual(read_archive(ROOT,name)['heading'],site['archive_pages'][name]['heading'])
if __name__=='__main__':unittest.main()
