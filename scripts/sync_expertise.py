"""Keep the Projects CMS dropdown in sync with About / My services."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sync():
 about=json.loads((ROOT/'content/cms/about.json').read_text())
 values=list(dict.fromkeys(item['title'].strip() for item in about.get('services',[]) if item.get('title','').strip()))
 path=ROOT/'.pages.yml';config=json.loads(path.read_text())
 projects=next(item for item in config['content'] if item['name']=='projects')
 fields=next(field for field in projects['fields'] if field['name']=='items')['fields']
 topic=next(field for field in fields if field['name']=='topic')
 topic['options']['values']=values
 text=json.dumps(config,ensure_ascii=False,indent=2)+'\n'
 if path.read_text()!=text:path.write_text(text)
if __name__=='__main__':sync()
