"""Page-specific metadata with approval independent of the translated body.

Legacy dedicated descriptions retain priority. Supplements fill gaps without
changing content fingerprints or withdrawing an approved translation.
"""
import json,re
from pathlib import Path

def load_descriptions(root):
 records={}
 for file in sorted((Path(root)/'content/cms/page_seo').glob('*.json')):
  item=json.loads(file.read_text())
  path=item.get('path','')
  if not isinstance(path,str) or not re.fullmatch(r'/(?:[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*)?',path) or path.startswith('/sr/') or re.search(r'/page/\d+$',path):
   raise ValueError('Invalid base SEO path in '+file.name)
  if path in records:raise ValueError('Duplicate SEO path: '+path)
  records[path]=item
 return records

def description(records,path,language,explicit=None):
 from i18n import ready
 match=re.fullmatch(r'(.+)/page/(\d+)',path)
 base=match[1] if match else path
 item=records.get(base,{})
 if explicit:
  value=explicit
 elif language=='sr':
  value=(item.get('sr') or {}).get('description') if ready(item,'page_seo') else None
 else:
  value=item.get('description')
 if value and match:
  value=value.rstrip()+(' Страна ' if language=='sr' else ' Page ')+match[2]+'.'
 return value
