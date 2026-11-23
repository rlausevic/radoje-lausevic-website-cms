"""Shared CMS/site work-experience ordering and month-precision migration."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from cms_data import load_cms
from experience_data import experience_period,experience_sort_key
from scripts.sync_experience import sync
ROOT=Path(__file__).resolve().parent
class Experience(unittest.TestCase):
 def test_serbian_periods_keep_shared_dates_and_english_sync(self):
  months='јануар фебруар март април мај јун јул август септембар октобар новембар децембар'.split()
  for month,name in enumerate(months,1):
   self.assertEqual(experience_period({'start':f'2026-{month:02d}','ongoing':True},'sr'),f'{name} 2026 – данас')
  for item,expected in [({'start':'2001-01','end':'2005-11'},'јануар 2001 – новембар 2005'),({'ongoing':True},'У току'),({'start':'2001-01'},'Од јануар 2001'),({'end':'2005-11'},'До новембар 2005'),({},'')]:
   self.assertEqual(experience_period(item,'sr'),expected)
 def test_stable_order_and_missing_dates(self):
  items=[{'title':'finished undated','ongoing':False,'start':'2099-01'},
   {'title':'finished older','end':'2020-05'},
   {'title':'ongoing undated','ongoing':True,'end':'2099-12'},
   {'title':'ongoing older','ongoing':True,'start':'2024-01'},
   {'title':'finished newer a','end':'2026-05'},
   {'title':'finished newer b','end':'2026-05'},
   {'title':'ongoing newer','ongoing':True,'start':'2026-05'}]
  self.assertEqual([i['title'] for i in sorted(items,key=experience_sort_key,reverse=True)],['ongoing newer','ongoing older','ongoing undated','finished newer a','finished newer b','finished older','finished undated'])
 def test_labels_and_validation(self):
  self.assertEqual(experience_period({'start':'2018-03','ongoing':True}),'March 2018 - ongoing')
  self.assertEqual(experience_period({'start':'2001-01','end':'2005-11'}),'January 2001 - November 2005')
  self.assertEqual(experience_period({'start':'2026-01','end':'invalid','ongoing':True}),'January 2026 - ongoing')
  self.assertEqual(experience_period({'period':'Legacy period'}),'Legacy period')
  self.assertEqual(experience_period({'ongoing':False,'period':'Stale period'}),'')
  for item in [{'start':'2026-13'},{'end':'2026-02-30'},{'start':'2026-05','end':'2025-12'},{'ongoing':'false'}]:
   with self.assertRaises(ValueError):experience_period(item)
 def test_cms_date_fields_keep_month_precision_and_empty_defaults(self):
  config=json.loads((ROOT/'.pages.yml').read_text());fields=next(x for x in config['content'] if x['name']=='experience')['fields'][0]['fields']
  for name in ['start','end']:
   field=next(x for x in fields if x['name']==name)
   self.assertEqual(field['default'],'');self.assertEqual(field['options']['format'],'yyyy-MM')
 def test_cms_sync_and_both_public_views_use_same_order(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   source=root/'content/cms/experience.json';data={'items':[
    {'title':'Finished earlier','start':'2000-01','end':'2010-01','ongoing':False,'body':'<p>Preserved body</p>'},
    {'title':'Ongoing older','start':'2020-01','ongoing':True},
    {'title':'Finished recent','start':'2005-01','end':'2026-05'},
    {'title':'Ongoing newest','start':'2026-09','ongoing':True},
    {'title':'Undated ongoing','ongoing':True},
    {'title':'Undated finished','ongoing':False}]}
   source.write_text(json.dumps(data));about=root/'content/cms/about.json';a=json.loads(about.read_text());a['career_highlights']=[i['title'] for i in data['items']];about.write_text(json.dumps(a))
   expected=['Ongoing newest','Ongoing older','Undated ongoing','Finished recent','Finished earlier','Undated finished']
   def verify():
    result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
    model=load_cms(root,json.loads((root/'content/site.json').read_text()))
    self.assertEqual([i['title'] for i in model['experience_entries']],expected)
    for page in ['work-experience','about']:
     html=(root/'dist'/page/'index.html').read_text();positions=[html.index('>'+title+'</h') for title in expected];self.assertEqual(positions,sorted(positions))
     self.assertIn('September 2026 - ongoing',html);self.assertIn('Preserved body',html)
   # The website sorts immediately, even before the automated CMS commit.
   verify();self.assertEqual(json.loads(source.read_text()),data)
   sync(root);saved=json.loads(source.read_text());self.assertEqual([i['title'] for i in saved['items']],expected)
   before=source.read_bytes();sync(root);self.assertEqual(source.read_bytes(),before)
   subprocess.run([sys.executable,'scripts/sync_expertise.py'],cwd=root,check=True)
   config=json.loads((root/'.pages.yml').read_text());fields=next(x for x in config['content'] if x['name']=='about')['fields']
   self.assertEqual(next(x for x in fields if x['name']=='career_highlights')['options']['values'],expected)
   verify()
if __name__=='__main__':unittest.main()
