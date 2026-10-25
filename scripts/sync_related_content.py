"""Maintain stable IDs and drag-and-drop order for native CMS collections."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_archives import ARCHIVES,bibliography_id,entry_key,read_archive

def sync(root=ROOT):
 root=Path(root);base=root/'content/cms'
 for source in (base/'bibliography_entries').glob('*.json'):
  item=json.loads(source.read_text())
  if not item.get('id'):
   item['id']=bibliography_id(item);source.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
 for name,(_,key) in ARCHIVES.items():
  source=base/(name+'.json');data=read_archive(root,name);entries=data.pop(key,[]) or []
  data['entry_order']=[{'item':entry_key(name,item),'title':item['title']} for item in entries]
  text=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
  if source.read_text()!=text:source.write_text(text)
if __name__=='__main__':sync()
