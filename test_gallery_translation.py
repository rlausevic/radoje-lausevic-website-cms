"""One gallery draft includes every photo, with shared editorial approval."""
import copy,io,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from i18n import digest,localize,ready,source_hash,source_text,sync_record
from scripts import translate_sr

ROOT=Path(__file__).resolve().parent
KEY='gallery_entries'
ENTRY='content/cms/gallery_entries/test.json'

def gallery():
 return {'title':'Gallery','summary':'Summary','body':'<p>Body</p>',
  'seo_description':'English SEO','path':'/gallery/translation-test','date':'2026-11-23',
  'photos':[{'title':'First photo','caption':'First caption','image':'/assets/one.jpg'},
            {'title':'Second photo','caption':'','image':'/assets/two.jpg'}]}

def translated(source):return {k:('Превод '+v if v else '') for k,v in source.items()}

class GalleryTranslation(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.path=self.root/ENTRY;self.path.parent.mkdir(parents=True)
  self.path.write_text(json.dumps(gallery()))
  self.mock=patch.object(translate_sr,'ROOT',self.root);self.mock.start();self.addCleanup(self.mock.stop)
 def prepare(self):
  data=translate_sr.export(ENTRY);data['translation']=translated(data['source']);return data
 def test_export_request_and_import_all_fields_in_one_call(self):
  data=self.prepare()
  self.assertEqual(set(data['source']),{'title','summary','body','seo_description','photos.0.title','photos.0.caption','photos.1.title','photos.1.caption'})
  response={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(data['translation'])}]}]}
  with patch.dict(os.environ,{'OPENAI_API_KEY':'test-placeholder'}),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as request:
   result=translate_sr.ai_prepare(data)
  self.assertEqual(request.call_count,1)
  sent=json.loads(request.call_args.args[0].data)
  self.assertEqual(json.loads(sent['input']),data['source'])
  self.assertEqual(set(sent['text']['format']['schema']['required']),set(data['source']))
  translate_sr.apply(result);item=json.loads(self.path.read_text())
  self.assertEqual(item['sr']['seo_description'],'Превод English SEO')
  self.assertEqual(item['photos'][0]['sr']['caption'],'Превод First caption')
  self.assertEqual(item['photos'][1]['sr']['caption'],'')
  self.assertFalse(item['sr']['approved']);self.assertFalse(ready(item,KEY))
  self.assertEqual([{k:v for k,v in p.items() if k!='sr'} for p in item['photos']],gallery()['photos'])
  item['sr']['approved']=True;sync_record(item,KEY);self.assertTrue(ready(item,KEY))
  localized=localize(item,KEY)
  self.assertEqual(localized['photos'][0]['caption'],'Превод First caption')
  self.assertEqual(localized['photos'][1]['title'],'Превод Second photo')
  self.assertEqual(localized['photos'][0]['image'],item['photos'][0]['image'])
  for side,field in [('en','caption'),('sr','caption'),('en','image')]:
   changed=copy.deepcopy(item);photo=changed['photos'][0]
   (photo['sr'] if side=='sr' else photo)[field]='Changed'
   self.assertFalse(ready(changed,KEY));sync_record(changed,KEY);self.assertFalse(changed['sr']['approved'])
 def test_missing_photo_translation_is_rejected_atomically(self):
  for mutation in ['missing','empty','extra']:
   data=self.prepare()
   if mutation=='missing':del data['translation']['photos.0.caption']
   elif mutation=='empty':data['translation']['photos.0.caption']=''
   else:data['translation']['photos.0.image']='/assets/other.jpg'
   before=self.path.read_text()
   with self.assertRaises(ValueError):translate_sr.apply(data)
   self.assertEqual(self.path.read_text(),before)
 def test_missing_english_seo_is_generated_with_serbian_in_one_request(self):
  item=gallery();item.pop('seo_description');self.path.write_text(json.dumps(item))
  data=self.prepare();response_text=dict(data['translation'],seo_description_en='Gallery of project meetings and cooperation.',seo_description='Галерија пројектних састанака и сарадње.')
  response={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(response_text)}]}]}
  with patch.dict(os.environ,{'OPENAI_API_KEY':'test-placeholder'}),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as request:
   result=translate_sr.ai_prepare(data)
  self.assertEqual(request.call_count,1)
  sent=json.loads(request.call_args.args[0].data)
  self.assertIn('seo_description_en',sent['text']['format']['schema']['required'])
  translate_sr.apply(result);saved=json.loads(self.path.read_text())
  self.assertEqual(saved['seo_description'],response_text['seo_description_en'])
  self.assertEqual(saved['sr']['seo_description'],response_text['seo_description'])
  self.assertEqual(saved['sr']['source_hash'],source_hash(saved,KEY))
  self.assertFalse(saved['sr']['approved'])
  sync_record(saved,KEY);self.assertNotIn('ажурирање',saved['sr']['status'])
  saved['sr']['approved']=True;sync_record(saved,KEY);self.assertTrue(ready(saved,KEY))
  for field in ['title','summary','body','path','date']:self.assertEqual(saved[field],item[field])
 def test_generated_seo_cannot_replace_existing_english_or_other_content(self):
  data=self.prepare();data['generated_seo_description']='Replacement SEO'
  before=self.path.read_text()
  with self.assertRaisesRegex(ValueError,'empty English SEO'):translate_sr.apply(data)
  self.assertEqual(self.path.read_text(),before)
  with self.assertRaisesRegex(ValueError,'only for a gallery'):
   translate_sr.translation_source({'generated_seo_description':'New SEO'},{'seo_description':''},'posts')
 def test_generated_seo_rejects_invalid_or_missing_text_without_writing(self):
  item=gallery();item['seo_description']='';self.path.write_text(json.dumps(item))
  for english,serbian in [('', 'Опис'),('<p>English</p>','Опис'),('English',''),('x'*301,'Опис'),('English','x'*301),('English','<p>Опис</p>')]:
   data=self.prepare();data['generated_seo_description']=english;data['translation']['seo_description']=serbian
   before=self.path.read_text()
   with self.assertRaises(ValueError):translate_sr.apply(data)
   self.assertEqual(self.path.read_text(),before)
 def test_generated_seo_rejects_concurrent_editor_seo_or_source_changes(self):
  for field,value in [('seo_description','Editor English SEO'),('summary','Updated summary')]:
   item=gallery();item['seo_description']='';self.path.write_text(json.dumps(item))
   data=self.prepare();data['generated_seo_description']='Generated English SEO';data['translation']['seo_description']='Генерисани SEO опис'
   item[field]=value;self.path.write_text(json.dumps(item));before=self.path.read_text()
   with self.assertRaisesRegex(ValueError,'Nothing was overwritten'):translate_sr.apply(data)
   self.assertEqual(self.path.read_text(),before)
 def test_concurrent_photo_edits_and_reordering_are_not_overwritten(self):
  for mutation in ['caption','image','sr','order','add']:
   self.path.write_text(json.dumps(gallery()));data=self.prepare();item=gallery()
   if mutation=='sr':item['photos'][0]['sr']={'caption':'Ручна измена'}
   elif mutation=='order':item['photos'].reverse()
   elif mutation=='add':item['photos'].append(copy.deepcopy(item['photos'][0]))
   else:item['photos'][0][mutation]='Changed'
   self.path.write_text(json.dumps(item));before=self.path.read_text()
   with self.assertRaisesRegex(ValueError,'Nothing was overwritten'):translate_sr.apply(data)
   self.assertEqual(self.path.read_text(),before)
 def test_legacy_approved_galleries_remain_unchanged(self):
  item=gallery();fields=['title','summary','body','seo_description']
  item['sr']=dict(translated({f:item[f] for f in fields}),approved=True)
  item['sr']['source_hash']=digest({f:item[f] for f in fields})
  item['sr']['approved_hash']=digest({f:item['sr'][f] for f in fields})
  before=copy.deepcopy(item);sync_record(item,KEY)
  self.assertEqual(item,before);self.assertTrue(ready(item,KEY))
  self.assertEqual(localize(item,KEY)['photos'],item['photos'])
  item['photos'][0]['sr']={'title':'','caption':''};self.assertTrue(ready(item,KEY))
  item['photos'][0]['sr']['caption']='Нови превод';self.assertFalse(ready(item,KEY))
  item['sr']['refresh_source']=True;sync_record(item,KEY)
  item['sr']['approved']=True;sync_record(item,KEY);self.assertFalse(ready(item,KEY))
 def test_all_saved_photos_and_cms_fields_are_covered(self):
  for path in (ROOT/'content/cms/gallery_entries').glob('*.json'):
   item=json.loads(path.read_text());source=source_text(item,KEY)
   for i,photo in enumerate(item.get('photos') or []):
    for f in ['title','caption']:self.assertEqual(source[f'photos.{i}.{f}'],photo.get(f) or '')
  config=json.loads((ROOT/'.pages.yml').read_text())
  entry=next(x for x in config['content'] if x['name']==KEY)
  photo=next(x for x in entry['fields'] if x['name']=='photos')
  sr=next(x for x in photo['fields'] if x['name']=='sr')
  self.assertEqual([x['name'] for x in sr['fields']],['title','caption'])
  self.assertEqual(entry['actions'][0]['scope'],'entry')

class GalleryTranslationBuild(unittest.TestCase):
 def test_approved_photo_text_is_rendered_in_gallery_search_and_seo(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   path=next((root/'content/cms/gallery_entries').glob('*.json'))
   item=json.loads(path.read_text());item['date']='2099-01-01';item['seo_description']=''
   path.write_text(json.dumps(item))
   with patch.object(translate_sr,'ROOT',root):
    data=translate_sr.export(str(path.relative_to(root)));data['translation']=translated(data['source'])
    data['generated_seo_description']='English gallery SEO'
    data['translation']['seo_description']='Преведен SEO опис галерије'
    data['translation']['photos.0.title']='Посебан наслов фотографије'
    data['translation']['photos.0.caption']='Посебан опис фотографије'
    translate_sr.apply(data)
   item=json.loads(path.read_text());item['sr']['approved']=True;sync_record(item,KEY)
   path.write_text(json.dumps(item,ensure_ascii=False))
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   route=item['path'].strip('/')+'/index.html'
   en=(root/'dist'/route).read_text();sr=(root/'dist/sr'/route).read_text()
   self.assertIn('data-caption="Посебан опис фотографије"',sr)
   self.assertIn('alt="Посебан опис фотографије"',sr)
   self.assertIn('>Посебан наслов фотографије',sr)
   self.assertIn('name="description" content="Преведен SEO опис галерије"',sr)
   self.assertNotIn('Посебан опис фотографије',en)
   self.assertIn('English gallery SEO',en)
   index=(root/'dist/sr/galleries/archive-index.json').read_text()
   self.assertIn('посебан опис фотографије',index.lower())
   self.assertEqual(json.loads(path.read_text()),item)

if __name__=='__main__':unittest.main()
