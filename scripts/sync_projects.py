"""Persist project addresses, topic selections and the website date order."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cms_data import project_sort_key,project_topics
from content_paths import project_paths

def sync(root=ROOT):
 source=Path(root)/'content/cms/projects.json'
 data=json.loads(source.read_text())
 before=json.dumps(data,ensure_ascii=False)
 items=project_paths(root,data.get('items') or [])
 for item in items:item['topic']=project_topics(item)
 ordered=sorted(items,key=project_sort_key,reverse=True)
 data['items']=ordered
 if json.dumps(data,ensure_ascii=False)!=before:
  source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':sync()
