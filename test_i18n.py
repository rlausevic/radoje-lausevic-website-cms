"""Editorial safety and real bilingual outputs, including stale-source races."""
import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from i18n import complete,ready,source_hash,sync_record,localize,Locale,digest,content_date
from scripts.translate_sr import validate_translation,export,apply,ai_prepare,payload_target
from unittest.mock import patch
import io,os
ROOT=Path(__file__).resolve().parent

def draft(item,key,**values):
 item['sr']=dict(values,source_hash=source_hash(item,key),approved=False)
 sync_record(item,key)
 return item

class Editorial(unittest.TestCase):
 def test_recommendation_author_translation_and_existing_approvals(self):
  key='about.recommendations'
  item={'author':'Original author, role','summary':'English summary','body':'English body'}
  # Existing approval fingerprints predate the optional attribution field.
  item['sr']={'approved':True,'summary':'Сажетак','body':'Текст'}
  fields=['summary','body','seo_description']
  item['sr']['source_hash']=digest({f:item.get(f) or '' for f in fields})
  item['sr']['approved_hash']=digest({f:item['sr'].get(f) or '' for f in fields})
  before=copy.deepcopy(item);sync_record(item,key);self.assertEqual(item,before)
  self.assertTrue(ready(item,key));self.assertEqual(localize(item,key)['author'],item['author'])
  changed=copy.deepcopy(item);changed['sr']['body']='Измењен текст'
  self.assertFalse(ready(changed,key));sync_record(changed,key);self.assertFalse(changed['sr']['approved'])
  changed=copy.deepcopy(item);changed['summary']='Changed original'
  self.assertFalse(ready(changed,key))
  item['sr']['author']='Аутор, функција'
  self.assertFalse(ready(item,key));sync_record(item,key);self.assertFalse(item['sr']['approved'])
  item['sr']['refresh_source']=True;sync_record(item,key);self.assertFalse(ready(item,key))
  item['sr']['approved']=True;sync_record(item,key)
  self.assertTrue(ready(item,key));self.assertEqual(localize(item,key)['author'],'Аутор, функција')
  item['author']='Changed attribution';self.assertFalse(ready(item,key))
  config=json.loads((ROOT/'.pages.yml').read_text())
  about=next(x for x in config['content'] if x['name']=='about')
  recommendations=next(x for x in about['fields'] if x['name']=='recommendations')
  sr=next(x for x in recommendations['fields'] if x['name']=='sr')
  self.assertEqual(next(x for x in sr['fields'] if x['name']=='author')['type'],'string')
 def test_card_date_languages(self):
  months='јануар фебруар март април мај јун јул август септембар октобар новембар децембар'.split()
  for month,name in enumerate(months,1):
   self.assertEqual(content_date(f'2026-{month:02d}-02','sr'),f'2. {name} 2026.')
  self.assertEqual(content_date('2026-11-22','en'),'Nov 22, 2026')
  self.assertEqual(content_date('2024-02-29','sr'),'29. фебруар 2024.')
 def test_project_action_exports_only_saved_selected_project(self):
  payload={'repository':{'ref':'main'},'action':{'name':'translate-project-sr'},'context':{'type':'repository'},'inputs':{'project_path':'/project/REDEEM'}}
  self.assertLess(len(json.dumps(payload)),1000)
  path,project=payload_target(payload)
  patch_data=export(path,project)
  projects=json.loads((ROOT/path).read_text())['items']
  selected=next(item for item in projects if item['path']==project)
  self.assertEqual(patch_data['source']['full_name'],selected['full_name'])
  self.assertEqual(patch_data['source']['body'],selected['body'])
  self.assertEqual(export(path,'/project/cc5880ac12fff035')['source'],patch_data['source'])
  self.assertNotIn('items',patch_data['source'])
  with self.assertRaisesRegex(ValueError,'exact permanent project path'):export(path,'/project/not-a-saved-project')
 def test_saved_file_actions_and_branch_guard_still_work(self):
  payload={'repository':{'ref':'main'},'context':{'path':'content/cms/home.json'}}
  self.assertEqual(payload_target(payload),('content/cms/home.json',None))
  payload['repository']['ref']='other-branch'
  with self.assertRaisesRegex(ValueError,'main branch'):payload_target(payload)
 def test_explicit_approval_and_staleness(self):
  item=draft({'title':'Title','excerpt':'Lead','body':'<p>Original</p>'},'posts',title='Наслов',excerpt='Увод',body='<p>Превод</p>')
  self.assertFalse(ready(item,'posts'))
  item['sr']['approved']=True
  self.assertFalse(ready(item,'posts')) # A CMS Save must pass sync before it is public.
  sync_record(item,'posts');self.assertTrue(ready(item,'posts'))
  item['date']='2026-11-22';item['cover']='/assets/shared.jpg';self.assertTrue(ready(item,'posts'))
  item['body']='<p>Changed source</p>';self.assertFalse(ready(item,'posts')) # Safe before sync.
  sync_record(item,'posts');self.assertFalse(item['sr']['approved']);self.assertIn('ажурирање',item['sr']['status'])
  item['sr']['approved']=True;sync_record(item,'posts');self.assertFalse(ready(item,'posts'))
  item['sr']['refresh_source']=True;sync_record(item,'posts');self.assertFalse(ready(item,'posts'))
  item['sr']['approved']=True;sync_record(item,'posts');self.assertTrue(ready(item,'posts'))
  item['sr']['body']='<p>Another translation</p>';self.assertFalse(ready(item,'posts'))
  sync_record(item,'posts');self.assertFalse(item['sr']['approved'])
 def test_incomplete_and_shared_identity(self):
  item=draft({'title':'ACRONYM','path':'/project/stable','full_name':'Full name','summary':'Text','body':'Original','related_content':{'journal':['/post/stable']}},'projects.items',full_name='Пун назив',summary='Сажетак')
  item['sr']['approved']=True;sync_record(item,'projects.items');self.assertFalse(ready(item,'projects.items'))
  item['sr']['body']='Превод';item['sr']['approved']=True;sync_record(item,'projects.items')
  data=localize(item,'projects.items')
  self.assertEqual(data['title'],'ACRONYM');self.assertEqual(data['path'],item['path']);self.assertEqual(data['related_content'],item['related_content']);self.assertEqual(data['body'],'Превод')
 def test_ai_output_rejects_changed_urls_and_invented_fields(self):
  source={'body':'<p><a href="https://example.com/">Link</a></p>','seo_description':''}
  with self.assertRaises(ValueError):validate_translation({'body':'<a href="https://other.com/">Текст</a>','seo_description':''},source)
  with self.assertRaises(ValueError):validate_translation(dict(source,approved=True),source)
  with self.assertRaises(ValueError):validate_translation(dict(source,seo_description='Invented'),source)
 def test_ai_request_and_missing_configuration_are_draft_only(self):
  patch_data={'source':{'title':'English','body':'<p>Body</p>','seo_description':''}}
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaisesRegex(ValueError,'OPENAI_API_KEY'):ai_prepare(copy.deepcopy(patch_data))
  response={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps({'title':'Наслов','body':'<p>Текст</p>','seo_description':''})}]}]}
  with patch.dict(os.environ,{'OPENAI_API_KEY':'unit-test-placeholder'}):
   with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as request:
    result=ai_prepare(copy.deepcopy(patch_data))
    self.assertEqual(result['translation']['title'],'Наслов');self.assertNotIn('approved',result['translation'])
    sent=json.loads(request.call_args.args[0].data)
    self.assertFalse(sent['store']);self.assertTrue(sent['text']['format']['strict'])
 def test_url_mapping_keeps_assets_and_untranslated_originals(self):
  locale=Locale()
  for url in ['/assets/file.pdf','/api/contact','/post/untranslated','https://example.com/']:
   self.assertEqual(locale.target(url),url)
  self.assertEqual(locale.target('/blog?page=2'),'/sr/blog?page=2')
  self.assertEqual(locale.target('/blog/archive-index.json?v=1'),'/sr/blog/archive-index.json?v=1')
  self.assertEqual(locale.target('/blog/page/2/'),'/sr/blog/page/2/')

class BilingualBuild(unittest.TestCase):
 def test_draft_approval_source_change_and_seo(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','.openai','__pycache__','.build-deps'))
   def run(*args):
    result=subprocess.run([sys.executable,*args],cwd=root,capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
   path='/post/i18n-editorial-test';source=root/'content/cms/posts/i18n-test.json'
   item={'title':'Original English title','path':path,'published':True,'date':'2026-11-22','excerpt':'English summary','body':'<p>English body</p>','seo_description':'English SEO'}
   draft(item,'posts',title='Наслов за проверу',excerpt='Сажетак за проверу',body='<p>Преведени текст за проверу</p>',seo_description='Српски SEO опис')
   def save():source.write_text(json.dumps(item,ensure_ascii=False))
   save();run('build.py')
   sr=root/('dist/sr'+path+'/index.html');en=root/('dist'+path+'/index.html')
   self.assertIn('noindex,follow',sr.read_text());self.assertNotIn('Преведени текст за проверу',sr.read_text())
   self.assertNotIn('/sr'+path,(root/'dist/sitemap.xml').read_text())
   item['sr']['approved']=True;sync_record(item,'posts');save()
   project_file=root/'content/cms/projects.json';project_data=json.loads(project_file.read_text());project=project_data['items'][0]
   from i18n import source_text
   translated_project={key:('СР '+value if value else '') for key,value in source_text(project,'projects.items').items()}
   draft(project,'projects.items',**translated_project);project['sr']['approved']=True;sync_record(project,'projects.items')
   project.setdefault('related_content',{})['journal']=[path]
   home_file=root/'content/cms/home.json';home=json.loads(home_file.read_text())
   draft(home,'home',**{key:('СР '+value if value else '') for key,value in source_text(home,'home').items()})
   home['sr']['approved']=True;sync_record(home,'home');home_file.write_text(json.dumps(home,ensure_ascii=False))
   project_file.write_text(json.dumps(project_data,ensure_ascii=False));run('build.py')
   import re,html
   for name in ['index.html','insights/index.html','blog/index.html','video/index.html','galleries/index.html']:
    for prefix,labels in [('sr/',{'ОБЈАВЕ','ВИДЕО','ГАЛЕРИЈА'}),('',{'JOURNAL','VIDEO','GALLERY'})]:
     cards=(root/('dist/'+prefix+name)).read_text()
     metadata=re.findall(r'<span class="date"><time datetime="([^"]+)">(.*?)</time> · <span>(.*?)</span></span>',cards)
     self.assertTrue(metadata,name)
     for iso,display,label in metadata:
      self.assertEqual(html.unescape(display),content_date(iso,'sr' if prefix else 'en'))
      self.assertIn(label,labels)
     if name in ['index.html','insights/index.html']:self.assertEqual({x[2] for x in metadata},labels)
   for archive in ['blog','video','galleries']:
    entries=json.loads((root/f'dist/sr/{archive}/archive-index.json').read_text())
    for entry in entries:
     self.assertRegex(entry['html'],r'</time> · <span>(ОБЈАВЕ|ВИДЕО|ГАЛЕРИЈА)</span>')
   project_html=(root/('dist/sr'+project['path']+'/index.html')).read_text()
   self.assertIn('href="/sr'+path+'"',project_html)
   self.assertIn('<h1>'+project['title']+'</h1>',project_html)
   self.assertIn('Пун назив пројекта:',project_html)
   from cms_data import project_period
   for prefix,label in [('project','Трајање пројекта:'),('assignment','Мој ангажман:')]:
    period=project_period(project,prefix,language='sr')
    self.assertIn('<strong>'+label+'</strong> '+period,project_html)
   period=project_period(project,language='sr')
   for page in ['dist/sr/index.html','dist/sr/projects/index.html','dist/sr/projects/archive-index.json']:
    self.assertIn('<strong>Мој ангажман:</strong> '+period,(root/page).read_text())
   english_project=(root/('dist'+project['path']+'/index.html')).read_text()
   self.assertIn('<strong>My assignment:</strong> '+project_period(project),english_project)
   self.assertIn('href="/sr'+project['path']+'"',sr.read_text())
   translated=sr.read_text();original=en.read_text()
   for value in ['lang="sr-Cyrl"','Преведени текст за проверу','content="Српски SEO опис"','rel="canonical" href="https://www.radojelausevic.com/sr'+path,'hreflang="en"','hreflang="sr-Cyrl"','href="'+path+'" lang="en"']:
    self.assertIn(value,translated)
   self.assertNotIn('noindex',translated);self.assertIn('English body',original);self.assertIn('content="English SEO"',original)
   self.assertIn('hreflang="sr-Cyrl"',original)
   sitemap=(root/'dist/sitemap.xml').read_text();self.assertIn('/sr'+path,sitemap)
   index=(root/'dist/sr/blog/archive-index.json').read_text();self.assertIn('/sr'+path,index);self.assertIn('Наслов за проверу',index)
   item['body']='<p>Changed English source</p>';save();run('build.py')
   self.assertIn('noindex,follow',sr.read_text());self.assertNotIn('/sr'+path,(root/'dist/sitemap.xml').read_text())
   self.assertNotIn('hreflang="sr-Cyrl"',en.read_text())
   item['published']=False;save();run('build.py');self.assertFalse(sr.exists());self.assertFalse(en.exists())
   run('validate.py')

if __name__=='__main__':unittest.main()
