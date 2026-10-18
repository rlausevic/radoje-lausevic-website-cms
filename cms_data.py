"""Read Pages CMS content and normalize it for the existing static templates."""
from pathlib import Path
from html.parser import HTMLParser
import json,html,re,datetime,copy,shutil
class CleanHTML(HTMLParser):
 allowed={'p','h2','h3','h4','strong','b','em','i','u','s','ul','ol','li','blockquote','br','hr','a','img','figure','figcaption','table','thead','tbody','tr','th','td','pre','code','sub','sup'}
 void={'img','br','hr'}
 def __init__(self):super().__init__(convert_charrefs=True);self.out=[];self.text=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in {'script','style','iframe','object'}:self.skip+=1;return
  if self.skip:return
  if tag=='h1':tag='h2'
  if tag not in self.allowed:return
  attrs=dict(attrs);clean={}
  if tag in {'a','img'}:
   key='href' if tag=='a' else 'src';u=attrs.get(key,'').strip()
   if u.startswith(('/', 'https://','http://','mailto:','tel:','#')) and not u.startswith('//'):clean[key]=u
   if tag=='img':clean.update({'alt':attrs.get('alt',''),'loading':'lazy','decoding':'async'})
   if tag=='a' and attrs.get('target')=='_blank':clean.update({'target':'_blank','rel':'noopener noreferrer'})
  if tag in {'td','th'}:
   for key in ['colspan','rowspan']:
    if attrs.get(key,'').isdigit():clean[key]=attrs[key]
  self.out.append('<'+tag+''.join(' '+k+'="'+html.escape(v,quote=True)+'"' for k,v in clean.items())+'>')
 def handle_endtag(self,tag):
  if tag in {'script','style','iframe','object'}:
   self.skip=max(0,self.skip-1);return
  if self.skip:return
  if tag=='h1':tag='h2'
  if tag in self.allowed and tag not in self.void:self.out.append('</'+tag+'>')
 def handle_data(self,data):
  if not self.skip:self.out.append(html.escape(data));self.text.append(data)
def body(value):
 p=CleanHTML();p.feed(value or '');return {'type':'html','html':''.join(p.out),'text':' '.join(' '.join(p.text).split())}
def text(tag,value):return {'type':tag,'text':value,'html':html.escape(value)}
def load_cms(root,original):
 base=root/'content/cms'
 if not base.exists():return original
 def read(path):return json.loads((base/path).read_text())
 model=copy.deepcopy(original);model['site']=read('settings.json');model['home']=read('home.json')
 a=read('about.json');model['pages']['/about']['blocks']=[body(a['body'])];model['about']=a
 model['expertise']=read('expertise.json') if (base/'expertise.json').exists() else {'services':a.get('services') or []}
 def ordered_entries(name):
  source=base/(name+'.json')
  if source.exists():items=read(name+'.json').get('items') or []
  else:items=[json.loads(f.read_text()) for f in sorted((base/name).glob('*.json'),key=lambda f:(json.loads(f.read_text()).get('order',0),f.name))]
  # List position is the canonical order; ignore any legacy order value.
  return [dict(item,order=index) for index,item in enumerate(items,1)]
 model['experience_entries']=ordered_entries('experience');model['project_entries']=ordered_entries('projects')
 network=read('network.json');blocks=[]
 for p in model['experience_entries']:
  blocks +=[text('h2',p['title']),text('p',p['period']),body(p.get('body') or '')]
 blocks +=[text('h2','My Professional Network'),body(network['body'])]
 model['pages']['/work-experience']={'blocks':blocks,'links':[{'text':'Get full list','href':network['document']}]}
 blocks=[]
 for p in model['project_entries']:
  blocks +=[{'type':'image','src':p.get('image') or model['site']['landscape'],'alt':p.get('image_alt') or p['title']},text('h2',p['title']),text('p',p['period']),body(p.get('body') or '')]
 model['pages']['/projects']={'blocks':blocks,'links':[]}
 model['project_summaries']={p['title']:p.get('summary') or '' for p in model['project_entries']}
 r=read('resume.json');resume_links=[]
 # Pages CMS omits optional fields after Remove; documents may be strings or lists.
 for key in ['brief_cv','europass_cv','assortis_cv','bibliography_file']:
  files=r.get(key) or []
  if isinstance(files,str):files=[files]
  resume_links.extend({'text':'Download','href':url} for url in files if url)
 model['pages']['/resume']={'blocks':[text('h2','Education'),body(r.get('education') or ''),text('h2','Selected Publications'),body(r.get('publications') or '')],'links':resume_links}
 g=read('gallery.json');blocks=[]
 for item in g['items']:blocks +=[{'type':'image','src':item['image'],'alt':item['title']},text('p',item['caption'])]
 blocks +=[text('h2','Flowers of My Mediterranean Garden'),body(g['body'])];model['pages']['/galleries']={'blocks':blocks,'links':[]}
 posts=[];paths=set()
 for f in (base/'posts').glob('*.json'):
  p=json.loads(f.read_text())
  if not p.get('published',True):continue
  path=p.get('path','')
  if not re.fullmatch(r'/post/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+',path):raise ValueError(f'{f.name}: address must use /post/your-article-name with letters, digits and hyphens')
  if path in paths:raise ValueError('Two articles have the same address: '+path)
  paths.add(path)
  p['cover']=p.get('cover') or '';p['categories']=p.get('categories') or [];p['excerpt']=p.get('excerpt') or '';
  d=datetime.date.fromisoformat(p['date'][:10]);b=body(p.get('body',''));p.update({'date':d.strftime('%b %d, %Y'),'date_iso':d.isoformat(),'blocks':[b]});posts.append(p)
 posts.sort(key=lambda p:(p['date_iso'],p['title']),reverse=True);model['posts']=posts
 # Removed/draft articles must not remain published in the generated directory.
 if (root/'dist/post').exists():shutil.rmtree(root/'dist/post')
 return model
