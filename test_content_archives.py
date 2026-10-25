"""Native media references, single-source collection edits and preserved list order."""
import json,shutil,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
from content_archives import ARCHIVES,entry_key,read_archive,write_archive,video_path
from related_content import load_catalog,selected_content
ROOT=Path(__file__).resolve().parent
class ContentArchives(unittest.TestCase):
 def test_native_references_and_direct_collection_edits(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   config=json.loads((root/'.pages.yml').read_text());schemas={c['name']:c for c in config['content']}
   fields=schemas['projects']['fields'][0]['fields'][-1]['fields']
   for f in fields:
    self.assertEqual(f['type'],'reference');self.assertTrue(f['options']['multiple']);self.assertNotIn('values',f['options'])
    self.assertEqual(schemas[f['options']['collection']]['type'],'collection')
   for name,(folder,key) in ARCHIVES.items():
    self.assertNotIn(key,json.loads((root/'content/cms'/ (name+'.json')).read_text()))
    source=next((root/'content/cms'/folder).glob('*.json'));item=json.loads(source.read_text())
    old_key=entry_key(name,item);item['title']='Directly edited '+name;source.write_text(json.dumps(item))
    related_key={'videos':'videos','gallery':'galleries','bibliography':'bibliography'}[name]
    selected={'related_content':{related_key:[old_key]}}
    self.assertEqual(selected_content(selected,load_catalog(root))[0][2][0]['title'].split(' (')[0],item['title'])
    item['title']='New '+name
    if name=='videos':item['link']='https://www.youtube.com/watch?v=new-reference'
    elif name=='gallery':item['path']='/gallery/new-reference'
    else:item['id']=str(uuid.uuid4())
    new_source=source.parent/'new-reference.json';new_source.write_text(json.dumps(item))
    self.assertIn(entry_key(name,item),load_catalog(root)[related_key])
    new_source.unlink();self.assertNotIn(entry_key(name,item),load_catalog(root)[related_key])
   before=(root/'.pages.yml').read_bytes();subprocess.run([sys.executable,'scripts/sync_related_content.py'],cwd=root,check=True,capture_output=True)
   self.assertEqual(before,(root/'.pages.yml').read_bytes())
 def test_drag_order_and_video_reference_compatibility(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   bibliography=read_archive(root,'bibliography');ids=[entry_key('bibliography',x) for x in bibliography['items']]
   path=root/'content/cms/bibliography.json';settings=json.loads(path.read_text());settings['entry_order'].reverse();path.write_text(json.dumps(settings))
   self.assertEqual([entry_key('bibliography',x) for x in read_archive(root,'bibliography')['items']],list(reversed(ids)))
   subprocess.run([sys.executable,'scripts/sync_related_content.py'],cwd=root,check=True,capture_output=True)
   self.assertEqual([entry_key('bibliography',x) for x in read_archive(root,'bibliography')['items']],list(reversed(ids)))
   video=read_archive(root,'videos')['items'][0];catalog=load_catalog(root)
   old=selected_content({'related_content':{'videos':[video_path(video['link'])]}},catalog)
   new=selected_content({'related_content':{'videos':[video['link']]}},catalog)
   self.assertEqual(old,new)
   # Deleting the final entry leaves an empty archive; it never revives the old list.
   for name,(_,key) in ARCHIVES.items():
    data=read_archive(root,name);data[key]=[];write_archive(root,name,data)
    self.assertEqual(read_archive(root,name)[key],[])
if __name__=='__main__':unittest.main()
