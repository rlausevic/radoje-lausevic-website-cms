"""CMS network/recommendation relationships and bounded archive previews."""
import json,re,shutil,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
from network_data import network_records,sync_network_index,dated,safe_network_link
from content_archives import read_archive,write_archive
from cms_data import load_cms
ROOT=Path(__file__).resolve().parent
class SectionArchives(unittest.TestCase):
 def test_network_reference_identity_and_deletion(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);folder=root/'content/cms';folder.mkdir(parents=True)
   source=folder/'network.json';source.write_text(json.dumps({'body':'Preserve prose','document':'/original.pdf','items':[{'name':'Organisation','date':'2024-01-02'},{'name':'Undated'}]}))
   sync_network_index(root);data=json.loads(source.read_text());identifier=data['items'][0]['id']
   data['items'][0]['name']='Renamed organisation';data['items'].reverse();source.write_text(json.dumps(data));sync_network_index(root)
   ref=json.loads((folder/'network_references'/f'{identifier}.json').read_text());self.assertEqual(ref['name'],'Renamed organisation')
   self.assertEqual(network_records(root)[0]['id'],identifier)
   self.assertEqual(json.loads(source.read_text())['body'],'Preserve prose')
   self.assertEqual(json.loads(source.read_text())['document'],'/original.pdf')
   data['items'].pop();source.write_text(json.dumps(data));sync_network_index(root)
   self.assertFalse((folder/'network_references'/f'{identifier}.json').exists())
   self.assertEqual(safe_network_link('hello@example.org'),'mailto:hello@example.org')
   self.assertEqual(safe_network_link('javascript:alert(1)'),'')
   self.assertEqual([i['name'] for i in dated([{'name':'a'},{'name':'b'},{'name':'c','date':'2026-01-01'}])],['c','a','b'])
 def test_cms_contract(self):
  schemas={c['name']:c for c in json.loads((ROOT/'.pages.yml').read_text())['content']}
  network=schemas['network']['fields'];self.assertEqual(network[0]['name'],'body');self.assertEqual(network[0]['label'],'Opis')
  fields=next(f for f in network if f['name']=='items')['fields'];self.assertEqual([f['name'] for f in fields],['id','name','date','link','body'])
  rec=next(f for f in schemas['about']['fields'] if f['name']=='recommendations')['fields']
  self.assertEqual([f['name'] for f in rec],['author','date','summary','body','related_contents'])
  relation=rec[-1];self.assertEqual(relation['type'],'reference');self.assertTrue(relation['options']['multiple'])
  self.assertEqual(relation['options']['collection'],'network_references');self.assertFalse(schemas['network_references']['operations']['create'])
 def test_generated_archives_preserve_all_records(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   source=root/'content/cms/network.json';original=json.loads(source.read_text());data=dict(original)
   data['items']=[{'id':str(uuid.UUID(int=n+1)),'name':f'Partner {n}','date':f'202{n}-01-02','body':f'<p>Network detail needle-{n}</p>','link':'partner@example.org'} for n in range(6)]
   source.write_text(json.dumps(data));about=root/'content/cms/about.json';a=json.loads(about.read_text())
   a['recommendations']=[{'author':f'Author {n}','date':f'202{n}-02-03','summary':f'Summary {n}','body':f'<p>Full recommendation {n}</p>','related_contents':[data['items'][0]['id']]} for n in range(6)]
   about.write_text(json.dumps(a))
   bib=read_archive(root,'bibliography');template=bib['items'][0];categories=['Publications','Articles','Conferences','Invited lectures']
   bib['items']=[dict(template,id=str(uuid.uuid4()),category=c,title=f'{c} record {n}',year=str(2020+n)) for c in categories for n in range(6)]
   write_archive(root,'bibliography',bib)
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   text=(root/'dist/about/index.html').read_text();self.assertIn(re.sub(r'<[^>]+>', '', original['body']),re.sub(r'<[^>]+>', '',text))
   for title in ['Partner','Author']:
    cards=re.findall(r'<details class="post-card about-archive-card"([^>]*)><summary>.*?<h3>('+title+r' \d)</h3>',text)
    self.assertEqual([name for _,name in cards],[f'{title} {n}' for n in reversed(range(6))]);self.assertEqual(sum(' hidden' not in attrs for attrs,_ in cards),4)
   self.assertIn('/about/#network-'+data['items'][0]['id'],text);self.assertIn('href="mailto:partner@example.org"',text)
   self.assertIn('Summary 5',(root/'dist/index.html').read_text());self.assertNotIn('Summary 0',(root/'dist/index.html').read_text())
   text=(root/'dist/bibliography/index.html').read_text();cards=re.findall(r'<li class="bibliography-item"([^>]*)>',text)
   self.assertEqual(len(cards),24);self.assertEqual(sum(' hidden' not in attrs for attrs in cards),12)
   for category in categories:
    positions=[text.index(category+' record '+str(n)) for n in reversed(range(6))];self.assertEqual(positions,sorted(positions))
   projects=load_cms(root,json.loads((root/'content/site.json').read_text()))['project_entries']
   index=json.loads((root/'dist/projects/archive-index.json').read_text());self.assertEqual(len(index),len(projects))
   urls=[re.search(r'href="([^"]+)">View all details',e['html'])[1] for e in index]
   self.assertEqual(urls,[p['path'] for p in projects])
   for page in range(1,(len(projects)+11)//12+1):
    path=root/('dist/projects/index.html' if page==1 else f'dist/projects/page/{page}/index.html');html=path.read_text()
    self.assertEqual(html.count('data-project '),min(12,len(projects)-(page-1)*12));self.assertIn('href="/projects" aria-current=',html)
   self.assertEqual(json.loads(source.read_text()),data)
if __name__=='__main__':unittest.main()
