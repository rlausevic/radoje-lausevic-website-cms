"""Build an allow-list of counters; no visitor data lives in Git or the CMS."""
import hashlib,json
from pathlib import Path
from content_paths import collection_records

class Metrics:
 def __init__(self,root):
  self.catalog={};self.seeds={}
  root=Path(root)
  for folder,kind in [('posts','post'),('gallery_entries','gallery')]:
   files=sorted((root/'content/cms'/folder).glob('*.json'))
   for source,item in zip(files,collection_records(root,folder,kind)):
    self.seeds[item['path']]=kind+':'+source.name
  from content_archives import video_path
  for source in sorted((root/'content/cms/video_entries').glob('*.json')):
   item=json.loads(source.read_text());self.seeds[video_path(item['link'])]='video:'+source.name
 def register(self,kind,identity,title,path,public=False):
  key=hashlib.sha256((kind+':'+identity).encode()).hexdigest()[:32]
  self.catalog[key]={'kind':kind,'title':title,'path':path,'public':public}
  return key
 def page(self,path,title):
  kind=path.strip('/').split('/')[0]
  parts=path.strip('/').split('/')
  if kind not in {'post','gallery','video','project'} or len(parts)<2:return None
  if kind!='post' and (len(parts)!=2 or parts[1]=='page'):return None
  return self.register(kind,self.seeds.get(path,path),title,path,kind!='project')
 def write(self,dist):
  path=Path(dist)/'_metrics/catalog.json';path.parent.mkdir(exist_ok=True)
  path.write_text(json.dumps(self.catalog,ensure_ascii=False,separators=(',',':')))
