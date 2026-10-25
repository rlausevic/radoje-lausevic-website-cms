"""Keep the CMS project list in the same date order as the website."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cms_data import project_sort_key

def sync(root=ROOT):
 source=Path(root)/'content/cms/projects.json'
 data=json.loads(source.read_text())
 items=data.get('items') or []
 ordered=sorted(items,key=project_sort_key,reverse=True)
 if ordered!=items:
  data['items']=ordered
  source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':sync()
