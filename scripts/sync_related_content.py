"""Maintain stable IDs and generated addresses for native CMS collections."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_archives import bibliography_id
from content_paths import collection_records
from network_data import sync_network_index
from cms_data import content_topics

def sync(root=ROOT):
 root=Path(root);base=root/'content/cms'
 sync_network_index(root)
 for source in (base/'bibliography_entries').glob('*.json'):
  item=json.loads(source.read_text())
  if not item.get('id'):
   item['id']=bibliography_id(item);source.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
 for folder,kind in [('posts','post'),('gallery_entries','gallery'),('video_entries',None)]:
  if kind:collection_records(root,folder,kind,persist=True)
  for source in (base/folder).glob('*.json'):
   item=json.loads(source.read_text())
   if 'topic' in item and item['topic']!=content_topics(item):
    item['topic']=content_topics(item)
    source.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':sync()
