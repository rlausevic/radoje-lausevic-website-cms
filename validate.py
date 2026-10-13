from html.parser import HTMLParser
from pathlib import Path
import urllib.parse,json,re
root=Path(__file__).resolve().parent/'dist';errors=[];externals=set();count=0
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set();self.h1=0;self.lang=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.add(a['id'])
  if tag=='h1':self.h1+=1
  if tag=='html':self.lang=bool(a.get('lang'))
  for key in ['src','href']:
   if a.get(key):self.links.append((tag,a[key]))
for file in root.rglob('*.html'):
 count+=1;p=Parser();p.feed(file.read_text())
 if p.h1!=1:errors.append(str(file.relative_to(root))+': expected 1 h1, got '+str(p.h1))
 if not p.lang:errors.append(str(file)+': missing language')
 for tag,url in p.links:
  u=urllib.parse.urlsplit(url)
  if u.scheme in ['mailto','tel','data']:continue
  if u.netloc:externals.add(u.netloc);continue
  if url.startswith('#'):
   if u.fragment not in p.ids:errors.append(str(file)+': missing fragment '+url)
   continue
  if u.path.startswith('/'):
   dest=root/u.path.lstrip('/')
   if dest.is_dir():dest=dest/'index.html'
   if not dest.exists():errors.append(str(file.relative_to(root))+': missing '+url)
  if 'wixstatic.com' in url or 'wixsite.com' in url:errors.append(str(file)+': Wix dependency '+url)
for file in root.rglob('*'):
 if file.is_file() and file.stat().st_size>25*1024*1024:errors.append('Asset exceeds Cloudflare limit: '+str(file))
print(json.dumps({'html_pages':count,'files':sum(1 for f in root.rglob('*') if f.is_file()),'errors':errors,'external_hosts':sorted(externals)},indent=2))
raise SystemExit(bool(errors))
