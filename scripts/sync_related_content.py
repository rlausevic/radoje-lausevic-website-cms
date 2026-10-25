"""Maintain stable IDs and generated addresses for native CMS collections."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_archives import bibliography_id
from content_paths import collection_records

def sync(root=ROOT):
 root=Path(root);base=root/'content/cms'
 for source in (base/'bibliography_entries').glob('*.json'):
  item=json.loads(source.read_text())
  if not item.get('id'):
   item['id']=bibliography_id(item);source.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
 collection_records(root,'posts','post',persist=True)
 collection_records(root,'gallery_entries','gallery',persist=True)
if __name__=='__main__':sync()
