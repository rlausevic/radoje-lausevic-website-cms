"""Explicit, repeatable migration to acronym URLs; normal Save keeps URLs stable."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_paths import slug,project_url

def migrate(root=ROOT):
 root=Path(root);source=root/'content/cms/projects.json'
 data=json.loads(source.read_text());items=data.get('items',[])
 changes={item['path']:'/project/'+slug(item['title'],preserve_case=True) for item in items}
 if len(set(changes.values()))!=len(items):raise ValueError('Project acronym addresses collide; resolve explicitly before migrating.')
 redirects_file=root/'content/project-redirects.json'
 previous=json.loads(redirects_file.read_text()) if redirects_file.exists() else {}
 if set(changes.values()) & set(previous):raise ValueError('A new acronym URL conflicts with a retired address.')
 redirects={old:changes.get(target,target) for old,target in previous.items()}
 redirects.update({old:new for old,new in changes.items() if old!=new})
 for item in items:
  item.setdefault('metrics_id',item['path'])
  item['path']=changes[item['path']]
 source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 def rewrite(value,key=''):
  if key=='metrics_id':return value
  if isinstance(value,dict):return {k:rewrite(v,k) for k,v in value.items()}
  if isinstance(value,list):return [rewrite(v) for v in value]
  if not isinstance(value,str):return value
  updated=project_url(value,redirects)
  if updated!=value:return updated
  return re.sub(r'''(href\s*=\s*["'])([^"']+)(["'])''',lambda m:m[1]+project_url(m[2],redirects)+m[3],value)
 changed=[]
 for file in (root/'content/cms').rglob('*.json'):
  original=json.loads(file.read_text());updated=rewrite(original)
  if updated!=original:
   file.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n');changed.append(str(file.relative_to(root)))
 redirects_file.write_text(json.dumps(dict(sorted(redirects.items())),ensure_ascii=False,indent=2)+'\n')
 return changes,changed

if __name__=='__main__':
 changes,files=migrate()
 print(json.dumps({'addresses':changes,'linked_files':files},ensure_ascii=False,indent=2))
