"""Single-record translations, explicit editorial approval, and locale-safe URLs."""
import copy,hashlib,html,json,os,re
from datetime import date
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,urlunsplit
ROOT=Path(__file__).resolve().parent
FIELDS=json.loads((ROOT/'i18n-fields.json').read_text())
LANG=os.environ.get('SITE_LANGUAGE','en')
SR=LANG=='sr'
SYSTEM_PAGES={'/projects','/blog','/video','/galleries','/insights','/contact'}
PAGE_FILES={'/':'home','/about':'about','/expertise':'expertise','/resume':'resume','/work-experience':'network','/bibliography':'settings','/blog':'journal'}

def content_date(value,language=LANG):
 """Format shared card dates without changing the source or machine-readable date."""
 day=date.fromisoformat(value)
 if language=='sr':
  months=('јануар','фебруар','март','април','мај','јун','јул','август','септембар','октобар','новембар','децембар')
  return f'{day.day}. {months[day.month-1]} {day.year}.'
 return day.strftime('%b %d, %Y')

def source_text(item,key):
 return {field:item.get(field) or '' for field in FIELDS[key]+['seo_description']}
def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def source_hash(item,key):return digest(source_text(item,key))
def translated_text(item,key):
 sr=item.get('sr') or {}
 return {f:sr.get(f) or '' for f in FIELDS[key]+['seo_description']}
def translation_hash(item,key):return digest(translated_text(item,key))
OPTIONAL_FIELDS={'about.recommendations':'author','experience.items':'title','network.items':'name'}
def legacy_optional_field_ready(item,key):
 # Preserve verified old approvals only while the newly translatable field is empty.
 # Adding that translation requires new source fingerprints and editorial approval.
 field=OPTIONAL_FIELDS.get(key)
 if not field:return False
 sr=item.get('sr') or {}
 if sr.get(field):return False
 fields=[f for f in FIELDS[key]+['seo_description'] if f!=field]
 return bool(sr.get('approved') is True and
  sr.get('source_hash')==digest({f:item.get(f) or '' for f in fields}) and
  sr.get('approved_hash')==digest({f:sr.get(f) or '' for f in fields}) and complete(item,key))

def complete(item,key):
 sr=item.get('sr') or {}
 # Optional attribution/title/name fields may retain their English original.
 # SEO is optional, with translated summary fallback.
 return all(isinstance(sr.get(f),str) and bool(sr[f].strip()) for f in FIELDS[key] if item.get(f) and f!=OPTIONAL_FIELDS.get(key))
def ready(item,key):
 sr=item.get('sr') or {}
 return legacy_optional_field_ready(item,key) or bool(sr.get('approved') is True and sr.get('source_hash')==source_hash(item,key) and sr.get('approved_hash')==translation_hash(item,key) and complete(item,key))
def sync_record(item,key):
 if not item.get('sr'):return
 sr=item['sr'];current=source_hash(item,key)
 if sr.pop('refresh_source',False):
  sr.update(source_hash=current,approved=False,approved_hash='',status='Оригинал је потврђен — прегледајте и одобрите превод')
  return
 if legacy_optional_field_ready(item,key):return
 if sr.get('source_hash')!=current:
  sr['approved']=False;sr['approved_hash']=''
  sr['status']='Потребно ажурирање — енглески оригинал је промењен' if sr.get('source_hash') else 'Нацрт — потребна провера'
  # Keep the old baseline on stale drafts; only a deliberate rebase/AI preparation updates it.
  if not sr.get('source_hash'):sr['source_hash']=current
 elif sr.get('approved_hash') and sr['approved_hash']!=translation_hash(item,key):
  sr.update(approved=False,approved_hash='',status='Нацрт је измењен — потребна поновна провера')
 elif sr.get('approved') and complete(item,key):
  sr['approved_hash']=translation_hash(item,key);sr['status']='Одобрено за објављивање'
 else:
  sr['approved']=False;sr['approved_hash']='';sr['status']='Нацрт — потребна провера' if complete(item,key) else 'Нацрт — допуните превод свих енглеских поља'

def walk(data,key):
 if not isinstance(data,dict):return
 if key in FIELDS:yield data,key
 for name,value in data.items():
  if name=='sr':continue
  child=key+'.'+name
  if isinstance(value,list):
   for item in value:yield from walk(item,child)
  elif isinstance(value,dict):yield from walk(value,child)

def file_key(path):
 path=Path(path)
 return path.parent.name if path.parent.name in {'posts','video_entries','gallery_entries','bibliography_entries'} else path.stem

def localize(data,key):
 data=copy.deepcopy(data)
 for item,kind in walk(data,key):
  if ready(item,kind):
   item['_source_title']=item.get('title','')
   translated=translated_text(item,kind)
   optional=OPTIONAL_FIELDS.get(kind)
   if optional and not translated.get(optional):translated.pop(optional,None)
   item.update(translated);item['_translated']=True
 return data

def read_json(path):
 data=json.loads(Path(path).read_text())
 return localize(data,file_key(path)) if SR and 'content/cms/' in str(path) else data

def all_records(root=ROOT):
 for path in sorted((Path(root)/'content/cms').rglob('*.json')):
  data=json.loads(path.read_text())
  yield path,data,list(walk(data,file_key(path)))

def route_records(root=ROOT):
 from content_paths import collection_records,project_paths
 from content_archives import video_path
 root=Path(root);base=root/'content/cms';out={}
 for route,name in PAGE_FILES.items():out[route]=(json.loads((base/(name+'.json')).read_text()),name)
 data=json.loads((base/'projects.json').read_text())
 for item in project_paths(root,data.get('items') or []):out[item['path']]=(item,'projects.items')
 for folder,kind in [('posts','post'),('gallery_entries','gallery')]:
  for item in collection_records(root,folder,kind):
   if item.get('published',True):out[item['path']]=(item,folder)
 for path in (base/'video_entries').glob('*.json'):
  item=json.loads(path.read_text());out[video_path(item['link'])]=(item,'video_entries')
 return out

class Locale:
 def __init__(self,root=ROOT):self.records=route_records(root)
 def translated(self,path):
  item,key=self.records.get(path,({},None))
  return bool(key and ready(item,key))
 def available(self,path):
  base=re.sub(r'/page/\d+$','',path)
  return base in SYSTEM_PAGES or self.translated(path)
 def seo(self,path,default):
  item,key=self.records.get(path,({},None))
  data=((item.get('sr') or {}) if key and ready(item,key) else {}) if SR else item
  return data.get('seo_description') or default
 def badge(self,item):
  return '<span class="language-original" lang="sr-Cyrl">Енглески оригинал</span>' if SR and not item.get('_translated') else ''
 def target(self,url):
  parts=urlsplit(url)
  if parts.netloc or not parts.path.startswith('/') or parts.path.startswith(('/assets/','/media/','/api/','/sr/','/_metrics/')):return url
  path=parts.path.rstrip('/') or '/'
  if path.endswith('/archive-index.json') and path.rsplit('/',1)[0] in SYSTEM_PAGES:return urlunsplit(('', '', '/sr'+parts.path,parts.query,parts.fragment))
  # Keep untranslated cards and relationships honest: go directly to the original.
  if not self.available(path):return url
  return urlunsplit(('', '', '/sr'+parts.path,parts.query,parts.fragment))
 def transform(self,document):
  """Translate interface text and localize eligible links without touching rich-text prose."""
  if not SR:return document
  ui=json.loads((ROOT/'i18n-ui.json').read_text())
  class Parser(HTMLParser):
   def __init__(self):super().__init__(convert_charrefs=True);self.out=[];self.skip=0;self.stack=[];self.prose=0;self.editorial=0
   def handle_starttag(parser,tag,attrs):
    a=dict(attrs)
    prose=bool(set((a.get('class') or '').split()) & {'post-excerpt'})
    if tag not in {'meta','link','img','br','hr','input','source','wbr'}:
     parser.stack.append((tag,prose));parser.prose+=int(prose)
    if tag in {'script','style'}:parser.skip+=1
    if tag=='html':a['lang']='sr-Cyrl'
    for name in ['href','data-base','data-index','data-detail-prefix','data-archive-back']:
     if a.get(name):a[name]=self.target(a[name])
    for name in ['aria-label','placeholder','data-singular','data-plural','data-label']:
     if a.get(name):a[name]=ui.get(a[name],a[name])
    parser.out.append('<'+tag+''.join(' '+k+('="'+html.escape(v,quote=True)+'"' if v is not None else '') for k,v in a.items())+'>')
   def handle_startendtag(parser,tag,attrs):parser.handle_starttag(tag,attrs)
   def handle_endtag(parser,tag):
    if tag in {'script','style'}:parser.skip=max(0,parser.skip-1)
    if parser.stack and parser.stack[-1][0]==tag:
     parser.prose-=int(parser.stack.pop()[1])
    parser.out.append('</'+tag+'>')
   def handle_data(parser,data):
    stripped=data.strip();value=ui.get(stripped,stripped) if not parser.skip and not parser.prose and not parser.editorial else stripped
    if not parser.skip and not parser.prose and not parser.editorial:
     value=re.sub(r'^Showing (\d+(?:[–−-]\d+)?) of (\d+) (.+)$',lambda m:'Приказано '+m[1]+' од '+m[2]+' '+ui.get(m[3],m[3]),value)
     if value.startswith('Search ') and value.endswith('…'):value=ui.get(value[:-1],value[:-1])+'…'
    result=data.replace(stripped,value,1) if stripped else data
    parser.out.append(result if parser.skip else html.escape(result,quote=False))
   def handle_entityref(parser,name):parser.out.append('&'+name+';')
   def handle_charref(parser,name):parser.out.append('&#'+name+';')
   def handle_comment(parser,text):
    if text=='cms:start':parser.editorial+=1
    elif text=='cms:end':parser.editorial=max(0,parser.editorial-1)
    parser.out.append('<!--'+text+'-->')
   def handle_decl(parser,decl):parser.out.append('<!'+decl+'>')
  p=Parser();p.feed(document);return ''.join(p.out)
