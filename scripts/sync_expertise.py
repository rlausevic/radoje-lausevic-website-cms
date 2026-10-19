"""Keep all CMS expertise dropdowns in sync with the single Expertise source."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sync():
 about=json.loads((ROOT/'content/cms/expertise.json').read_text())
 values=list(dict.fromkeys(item['title'].strip() for item in about.get('services',[]) if item.get('title','').strip()))
 path=ROOT/'.pages.yml';config=json.loads(path.read_text())
 schemas={item['name']:item for item in config['content']}
 for name,list_name in [('projects','items'),('videos','items'),('gallery','albums'),('posts',None)]:
  fields=schemas[name]['fields']
  if list_name:fields=next(field for field in fields if field['name']==list_name)['fields']
  next(field for field in fields if field['name']=='topic')['options']['values']=values
 experiences=json.loads((ROOT/'content/cms/experience.json').read_text()).get('items') or []
 about_schema=next(item for item in config['content'] if item['name']=='about')
 next(field for field in about_schema['fields'] if field['name']=='career_highlights')['options']['values']=[item['title'] for item in experiences]
 text=json.dumps(config,ensure_ascii=False,indent=2)+'\n'
 if path.read_text()!=text:path.write_text(text)
if __name__=='__main__':sync()
