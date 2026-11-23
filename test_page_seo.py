"""Approval isolation, archive inheritance and real bilingual head output."""
import copy,json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from html.parser import HTMLParser
from unittest.mock import patch
from i18n import Locale,ready,source_hash,sync_record
from page_seo import description,load_descriptions
ROOT=Path(__file__).resolve().parent

class Head(HTMLParser):
 def __init__(self,text):
  super().__init__();self.meta={};self.feed(text)
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='meta':self.meta[d.get('name') or d.get('property')]=d.get('content')

class Metadata(unittest.TestCase):
 def test_approval_is_separate_and_stale_text_is_never_published(self):
  item={'path':'/blog','description':'English archive description'}
  item['sr']={'description':'Српски опис архиве','approved':False,'source_hash':source_hash(item,'page_seo')}
  sync_record(item,'page_seo');data={'/blog':item}
  self.assertIsNone(description(data,'/blog','sr'))
  item['sr']['approved']=True
  self.assertIsNone(description(data,'/blog','sr'))
  sync_record(item,'page_seo')
  self.assertEqual(description(data,'/blog','sr'),'Српски опис архиве')
  self.assertEqual(description(data,'/blog/page/3','sr'),'Српски опис архиве Страна 3.')
  self.assertEqual(description(data,'/blog/page/3','en'),'English archive description Page 3.')
  self.assertEqual(description(data,'/blog','sr','Раније одобрен опис'),'Раније одобрен опис')
  changed=copy.deepcopy(item);changed['sr']['description']='Измењен нацрт'
  self.assertIsNone(description({'/blog':changed},'/blog','sr'))
  changed=copy.deepcopy(item);changed['description']='Changed English source'
  self.assertIsNone(description({'/blog':changed},'/blog','sr'))
  sync_record(changed,'page_seo');self.assertFalse(changed['sr']['approved'])
  changed=copy.deepcopy(item);changed['sr']['description']=''
  sync_record(changed,'page_seo');self.assertFalse(ready(changed,'page_seo'))

 def test_bad_or_duplicate_routes_are_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'content/cms/page_seo';folder.mkdir(parents=True)
   file=folder/'one.json'
   for path in ['/a/../b','https://example.com','/sr/blog','/blog/page/2','/blog?test=1']:
    file.write_text(json.dumps({'path':path}))
    with self.assertRaisesRegex(ValueError,'Invalid base SEO path'):load_descriptions(tmp)
   file.write_text(json.dumps({'path':'/blog'}));(folder/'two.json').write_text(file.read_text())
   with self.assertRaisesRegex(ValueError,'Duplicate SEO path'):load_descriptions(tmp)

 def test_new_records_are_drafts_and_do_not_grant_content_availability(self):
  locale=Locale(ROOT);original=copy.deepcopy(locale.records)
  path='/project/SEO-ONLY-TEST'
  item={'path':path,'description':'English description'}
  item['sr']={'description':'Српски опис','approved':False,'source_hash':source_hash(item,'page_seo')}
  locale.page_seo[path]=item
  self.assertFalse(ready(item,'page_seo'));self.assertFalse(locale.available(path))
  item['sr']['approved']=True;sync_record(item,'page_seo')
  self.assertFalse(locale.available(path));self.assertEqual(locale.records,original)

 def test_real_html_and_local_approval_cover_every_archive_page(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   original_sources={str(f.relative_to(root)):f.read_bytes() for f in (root/'content/cms').rglob('*.json') if f.parent.name!='page_seo'}
   # Tests reset metadata only in the disposable copy, regardless of later
   # owner approvals in the live CMS.
   for file in (root/'content/cms/page_seo').glob('*.json'):
    item=json.loads(file.read_text())
    if item.get('sr'):
     item['sr'].update(approved=False,approved_hash='',source_hash=source_hash(item,'page_seo'))
     sync_record(item,'page_seo');file.write_text(json.dumps(item,ensure_ascii=False))
   def build():
    result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
   def head(path):return Head((root/'dist'/path.strip('/')/'index.html').read_text()).meta
   build()
   data=load_descriptions(root)
   for path,item in data.items():
    h=head(path);self.assertEqual(h['description'],item['description'],path)
    self.assertEqual(h['og:description'],item['description'],path)
   self.assertEqual(head('/sr/blog')['description'],'Преведени садржаји и енглески оригинали.')
   self.assertNotIn('noindex',head('/sr/gallery/REDEEM').get('robots',''))
   # Simulate the owner's Save only in this disposable test copy.
   for file in (root/'content/cms/page_seo').glob('*.json'):
    item=json.loads(file.read_text())
    if item['path'] in {'/blog','/video','/galleries','/projects','/project/TOUR'}:
     item['sr']['approved']=True;sync_record(item,'page_seo');file.write_text(json.dumps(item,ensure_ascii=False))
   build()
   for base,pages in [('/blog',5),('/galleries',3),('/video',2),('/projects',2)]:
    value=data[base]['sr']['description']
    for number in range(1,pages+1):
     suffix='' if number==1 else '/page/'+str(number)
     expected=value+(' Страна '+str(number)+'.' if number>1 else '')
     h=head('/sr'+base+suffix)
     self.assertEqual(h['description'],expected)
     self.assertEqual(h['og:description'],expected)
   h=head('/sr/project/TOUR')
   self.assertIn('noindex',h['robots'])
   self.assertEqual(h['description'],'Овај садржај можете прочитати у енглеском оригиналу.')
   for path,before in original_sources.items():self.assertEqual((root/path).read_bytes(),before,path)

if __name__=='__main__':unittest.main()
