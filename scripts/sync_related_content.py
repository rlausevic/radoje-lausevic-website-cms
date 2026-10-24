"""Refresh project dropdowns and persist stable bibliography identifiers."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from related_content import bibliography_id,load_catalog,GROUPS

def sync(root=ROOT):
 root=Path(root);source=root/'content/cms/bibliography.json';data=json.loads(source.read_text());changed=False
 for item in data.get('items') or []:
  if not item.get('id'):item['id']=bibliography_id(item);changed=True
 if changed:source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 catalog=load_catalog(root);path=root/'.pages.yml';config=json.loads(path.read_text())
 projects=next(item for item in config['content'] if item['name']=='projects')
 fields=next(item for item in projects['fields'][0]['fields'] if item['name']=='related_content')['fields']
 for key,_ in GROUPS:
  field=next(item for item in fields if item['name']==key)
  field['options']['values']=[{'name':value,'label':item['title']} for value,item in catalog[key].items()]
 text=json.dumps(config,ensure_ascii=False,indent=2)+'\n'
 if path.read_text()!=text:path.write_text(text)
if __name__=='__main__':sync()
