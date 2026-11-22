"""Generate persistent public addresses for new projects, articles and galleries."""
import hashlib,json,re,unicodedata
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

def project_url(url,redirects,domain='https://www.radojelausevic.com'):
 """Resolve retired local project URLs, preserving locale, query and fragment."""
 parts=urlsplit(url)
 if parts.netloc and parts.hostname not in {urlsplit(domain).hostname,'radojelausevic.com'}:return url
 if parts.scheme and parts.scheme not in {'http','https'}:return url
 prefix='/sr' if parts.path.startswith('/sr/project/') else ''
 path=parts.path[len(prefix):].rstrip('/')
 if path not in redirects:return url
 return urlunsplit((parts.scheme,parts.netloc,prefix+redirects[path],parts.query,parts.fragment))

def slug(title,preserve_case=False):
 title=str(title).replace('Đ','D').replace('đ','d')
 title=unicodedata.normalize('NFKD',title).encode('ascii','ignore').decode()
 if not preserve_case:title=title.lower()
 return re.sub(r'[^A-Za-z0-9]+','-',title).strip('-') or 'untitled'

def project_paths(root,items):
 """Fill only blank project addresses, reserving existing and retired URLs."""
 redirects=Path(root)/'content/project-redirects.json'
 used=set(json.loads(redirects.read_text())) if redirects.exists() else set()
 used.update(item['path'] for item in items if (item.get('path') or '').strip())
 for item in items:
  if (item.get('path') or '').strip():continue
  base='/project/'+slug(item.get('title',''),preserve_case=True)
  candidate=base;number=2
  while candidate in used:
   candidate=base+'-'+str(number);number+=1
  item['path']=candidate;used.add(candidate)
 return items

def collection_records(root,folder,kind,persist=False,localized=False):
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
 from i18n import localize,SR
 return [localize(item,folder) if localized and SR else item for _,item in records]
