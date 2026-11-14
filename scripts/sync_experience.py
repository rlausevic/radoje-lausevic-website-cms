"""Persist the same work-experience order and period labels used by the site."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experience_data import experience_period,experience_sort_key

def sync(root=ROOT):
 source=Path(root)/'content/cms/experience.json'
 data=json.loads(source.read_text());before=json.dumps(data,ensure_ascii=False)
 items=data.get('items') or []
 for item in items:item['period']=experience_period(item)
 data['items']=sorted(items,key=experience_sort_key,reverse=True)
 if json.dumps(data,ensure_ascii=False)!=before:
  source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':sync()
