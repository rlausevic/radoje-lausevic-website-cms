"""Stable content identifiers and shared catalogs for CMS project relationships."""
import hashlib,json,uuid
from pathlib import Path

GROUPS=(('journal','Journal'),('videos','Video'),('galleries','Galleries'),('bibliography','Bibliography'))

def video_path(link):
 return '/video/'+hashlib.sha256(link.strip().encode()).hexdigest()[:16]

def bibliography_id(item):
 if item.get('id'):return str(uuid.UUID(str(item['id'])))
 # Persisted by CMS synchronization; fallback also works before the first sync.
 seed=json.dumps([item.get(k) or '' for k in ['title','authors','year','reference']],ensure_ascii=False)
 return str(uuid.uuid5(uuid.NAMESPACE_URL,'radojelausevic.com/bibliography/'+seed))

def load_catalog(root):
 base=Path(root)/'content/cms'
 read=lambda name:json.loads((base/name).read_text())
 catalog={key:{} for key,_ in GROUPS}
 for path in sorted((base/'posts').glob('*.json')):
  item=json.loads(path.read_text())
  if item.get('published',True):catalog['journal'][item['path']]={'title':item['title'],'href':item['path']}
 for item in read('videos.json').get('items') or []:
  path=video_path(item['link']);catalog['videos'][path]={'title':item['title'],'href':path}
 for item in read('gallery.json').get('albums') or []:
  catalog['galleries'][item['path']]={'title':item['title'],'href':item['path']}
 for item in read('bibliography.json').get('items') or []:
  key=bibliography_id(item)
  if key in catalog['bibliography']:raise ValueError('Duplicate bibliography ID: '+key)
  title=item['title']+(' ('+str(item['year'])+')' if item.get('year') else '')
  catalog['bibliography'][key]={'title':title,'href':'/bibliography#bibliography-'+key}
 return catalog

def selected_content(project,catalog):
 related=project.get('related_content') or {};result=[]
 for key,label in GROUPS:
  values=related.get(key) or []
  if isinstance(values,str):values=[values]
  items=[catalog[key][value] for value in dict.fromkeys(values) if value in catalog[key]]
  if items:result.append((key,label,items))
 return result
