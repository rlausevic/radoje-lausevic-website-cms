"""Generate editable, persistent public addresses for new articles and galleries."""
import hashlib,json,re,unicodedata
from pathlib import Path

def slug(title):
 title=str(title).replace('Đ','D').replace('đ','d')
 title=unicodedata.normalize('NFKD',title).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',title).strip('-') or 'untitled'

def collection_records(root,folder,kind,persist=False):
 """Explicit addresses win. Only missing addresses are generated, including drafts.

 Resolve collisions against the whole collection so publishing a draft cannot
 steal an existing URL. A stable filename suffix distinguishes identical titles.
 """
 sources=sorted((Path(root)/'content/cms'/folder).glob('*.json'))
 records=[(source,json.loads(source.read_text())) for source in sources]
 used={item['path'] for _,item in records if (item.get('path') or '').strip()}
 for source,item in records:
  if not (item.get('path') or '').strip():
   candidate='/'+kind+'/'+slug(item.get('title',''))
   if candidate in used:candidate+='-'+hashlib.sha256(source.name.encode()).hexdigest()[:8]
   while candidate in used:candidate+='-2'
   item['path']=candidate;used.add(candidate)
   if persist:source.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
 return [item for _,item in records]
