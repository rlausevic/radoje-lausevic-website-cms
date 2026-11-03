"""One editable network list, with a generated read-only Pages CMS reference index."""
import datetime,json,re,uuid
from pathlib import Path

def date_key(item):
 try:return datetime.date.fromisoformat(str(item.get('date') or '')[:10])
 except ValueError:return datetime.date.min

def dated(items):
 return sorted(items,key=date_key,reverse=True)

def network_records(root,persist=False):
 source=Path(root)/'content/cms/network.json';data=json.loads(source.read_text());items=data.get('items') or []
 seen=set();changed=False
 for index,item in enumerate(items):
  if not item.get('id'):
   item['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,'radojelausevic.com/network/'+str(index)+'/'+item.get('name','')));changed=True
  # UUIDs make references independent of title, date, position and external URL.
  item['id']=str(uuid.UUID(item['id']))
  if item['id'] in seen:raise ValueError('Duplicate network ID: '+item['id'])
  seen.add(item['id'])
 if persist and changed:source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return dated(items)

def safe_network_link(value):
 value=str(value or '').strip()
 if re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',value):return 'mailto:'+value
 if value.startswith(('https://','http://','mailto:')):return value
 return ''

def sync_network_index(root):
 root=Path(root);folder=root/'content/cms/network_references';folder.mkdir(exist_ok=True)
 keep=set()
 for item in network_records(root,persist=True):
  filename=item['id']+'.json';keep.add(filename)
  # Derived lookup only. The original content remains in network.json.
  text=json.dumps({'id':item['id'],'name':item.get('name','')},ensure_ascii=False,indent=2)+'\n'
  path=folder/filename
  if not path.exists() or path.read_text()!=text:path.write_text(text)
 for path in folder.glob('*.json'):
  if path.name not in keep:path.unlink()
