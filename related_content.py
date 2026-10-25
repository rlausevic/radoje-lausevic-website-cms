"""Stable content identifiers and shared catalogs for CMS project relationships."""
import json
from content_archives import video_path,bibliography_id,read_archive
from pathlib import Path

GROUPS=(('journal','Journal'),('videos','Video'),('galleries','Galleries'),('bibliography','Bibliography'))

def load_catalog(root):
 base=Path(root)/'content/cms'
 read=lambda name:json.loads((base/name).read_text())
 catalog={key:{} for key,_ in GROUPS}
 for path in sorted((base/'posts').glob('*.json')):
  item=json.loads(path.read_text())
  if item.get('published',True):catalog['journal'][item['path']]={'title':item['title'],'href':item['path']}
 for item in read_archive(root,'videos').get('items') or []:
  path=video_path(item['link']);catalog['videos'][item['link'].strip()]={'title':item['title'],'href':path}
 for item in read_archive(root,'gallery').get('albums') or []:
  catalog['galleries'][item['path']]={'title':item['title'],'href':item['path']}
 for item in read_archive(root,'bibliography').get('items') or []:
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
  items=[]
  for value in dict.fromkeys(values):
   item=catalog[key].get(value)
   # Existing project references used the public Video path; continue accepting them.
   if item is None and key=='videos':item=next((entry for entry in catalog[key].values() if entry['href']==value),None)
   if item and item not in items:items.append(item)
  if items:result.append((key,label,items))
 return result
