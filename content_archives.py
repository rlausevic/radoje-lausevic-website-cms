"""Canonical file collections with separate archive settings and stable ordering."""
import hashlib,json,uuid
from pathlib import Path

ARCHIVES={'videos':('video_entries','items'),'gallery':('gallery_entries','albums'),'bibliography':('bibliography_entries','items')}

def video_path(link):
 return '/video/'+hashlib.sha256(link.strip().encode()).hexdigest()[:16]

def bibliography_id(item):
 if item.get('id'):return str(uuid.UUID(str(item['id'])))
 seed=json.dumps([item.get(k) or '' for k in ['title','authors','year','reference']],ensure_ascii=False)
 return str(uuid.uuid5(uuid.NAMESPACE_URL,'radojelausevic.com/bibliography/'+seed))

def entry_key(name,item):
 if name=='videos':return item['link'].strip()
 if name=='gallery':return item['path']
 return bibliography_id(item)

def read_archive(root,name):
 folder,key=ARCHIVES[name];base=Path(root)/'content/cms';data=json.loads((base/(name+'.json')).read_text())
 source=base/folder
 if source.exists():
  entries=[json.loads(path.read_text()) for path in sorted(source.glob('*.json'))]
  ordering={row['item']:i for i,row in enumerate(data.get('entry_order') or []) if row.get('item')}
  entries.sort(key=lambda item:ordering.get(entry_key(name,item),len(ordering)))
  data[key]=entries
 return data

def write_archive(root,name,data):
 """Persist edits without keeping a second, embedded version of any entry."""
 folder,key=ARCHIVES[name];base=Path(root)/'content/cms';source=base/folder;source.mkdir(parents=True,exist_ok=True)
 metadata=dict(data);entries=metadata.pop(key,[]) or [];metadata['entry_order']=[{'item':entry_key(name,item),'title':item['title']} for item in entries]
 keep=set()
 for item in entries:
  identifier=entry_key(name,item)
  filename=(identifier if name=='bibliography' else hashlib.sha256(identifier.encode()).hexdigest()[:24])+'.json'
  if filename in keep:raise ValueError('Duplicate archive entry: '+identifier)
  keep.add(filename);(source/filename).write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
 for path in source.glob('*.json'):
  if path.name not in keep:path.unlink()
 (base/(name+'.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
