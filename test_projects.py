"""Project archive, details, CMS topic synchronization and shared search."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class ProjectArchive(unittest.TestCase):
 def test_assignment_dates_and_detail_sections(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   fields=next(x for x in json.loads((root/'.pages.yml').read_text())['content'] if x['name']=='projects')['fields'][0]['fields']
   self.assertEqual(len(fields),16);self.assertNotIn('period',[x['name'] for x in fields])
   source=root/'content/cms/projects.json';data=json.loads(source.read_text());p=data['items'][0]
   p.update(title='Test assignment',full_name='Unique full project name',assignment_start='2024-08-30',assignment_end='2025-01-13',assignment_ongoing=False,project_start='2023-07-01',project_end='2028-10-31',role='Test policy expert',contribution='<p>Unique stakeholder support</p>',results='<p>Unique verified output</p>')
   source.write_text(json.dumps(data));subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   archive=(root/'dist/projects/index.html').read_text();detail=(root/'dist'/p['path'].strip('/')/'index.html').read_text()
   self.assertIn('<strong>My assignment:</strong> Aug 2024 – Jan 2025',archive)
   self.assertLess(archive.index('Test assignment</h2>'),archive.index('<strong>My assignment:</strong>'))
   self.assertIn('unique stakeholder support',archive);self.assertIn('unique verified output',archive);self.assertIn('test policy expert',archive)
   for text in ['<h2>Full project name:</h2><p>Unique full project name','<h2>My role:</h2><p>Test policy expert','<h2>My assignment:</h2><p>Aug 2024 – Jan 2025','<h2>Project duration:</h2><p>Jul 2023 – Oct 2028','Project overview:','My contribution:','Selected results:','Unique verified output']:
    self.assertIn(text,detail)
   order=['← Back to projects','<h1>Test assignment</h1>','<h2>Full project name:</h2>','<h2>Project duration:</h2>','<h2>My role:</h2>','<h2>My assignment:</h2>','src="'+p['image']+'"','<h2>Project overview:</h2>','<h2>My contribution:</h2>','<h2>Selected results:</h2>']
   positions=[detail.index(value) for value in order];self.assertEqual(positions,sorted(positions))
   self.assertIn('unique full project name',archive)
   self.assertEqual(next(x for x in fields if x['name']=='title')['label'],'Akronim')
   p.update(full_name='',assignment_ongoing=True,assignment_end='2025-01-13',project_start='',project_end='',role='',contribution='',results='<p> </p>')
   source.write_text(json.dumps(data));subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   detail=(root/'dist'/p['path'].strip('/')/'index.html').read_text()
   self.assertIn('Aug 2024 – present',detail)
   for text in ['<h2>Full project name:</h2>','<h2>My role:</h2>','<h2>Project duration:</h2>','<h2>My contribution:</h2>','<h2>Selected results:</h2>']:self.assertNotIn(text,detail)
 def test_project_date_validation(self):
  from cms_data import project_period
  self.assertEqual(project_period({}),'')
  self.assertEqual(project_period({'assignment_start':'2026-09-07','assignment_end':'2026-10-22','assignment_ongoing':True}),'Sep 2026 – present')
  self.assertEqual(project_period({'assignment_start':'2026-09-07','assignment_end':'2020-01-01','assignment_ongoing':True}),'Sep 2026 – present')
  self.assertEqual(project_period({'project_start':'2023-07-01'},'project'),'From Jul 2023')
  for data in [{'assignment_start':'bad'},{'assignment_start':'2024-02-30'},{'assignment_start':'2026-01-01','assignment_end':'2025-01-01'},{'assignment_ongoing':'false'}]:
   with self.assertRaises(ValueError):project_period(data)
 def test_cms_topics_details_and_footer(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   about=root/'content/cms/expertise.json';data=json.loads(about.read_text());data['services'].append({'title':'Test expertise','motto':'','summary':'Test','description':''});about.write_text(json.dumps(data))
   subprocess.run([sys.executable,'scripts/sync_expertise.py'],cwd=root,check=True)
   cfg=json.loads((root/'.pages.yml').read_text());projects=next(x for x in cfg['content'] if x['name']=='projects')['fields'][0]['fields']
   self.assertEqual(next(x for x in projects if x['name']=='topic')['options']['values'],[x['title'] for x in data['services']])
   self.assertNotIn('publication_items',[x['name'] for x in next(x for x in cfg['content'] if x['name']=='resume')['fields']])
   p=root/'content/cms/projects.json';data=json.loads(p.read_text());data['items'][0]['topic']='Test expertise';data['items'][0]['body']='<p>Searchable detailed project content</p>';p.write_text(json.dumps(data))
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   archive=(root/'dist/projects/index.html').read_text()
   self.assertIn('Search projects',archive);self.assertIn('Topic of expertise',archive);self.assertIn('value="Test expertise"',archive)
   self.assertIn('data-categories="Test expertise"',archive);self.assertIn('searchable detailed project content',archive)
   links=re.findall(r'href="(/project/[a-f0-9]+)">View all details',archive);self.assertEqual(len(links),len(data['items']))
   first=(root/'dist'/links[0].strip('/')/'index.html').read_text();self.assertIn('<p>Searchable detailed project content</p>',first)
   self.assertIn('href="/projects" aria-current="true"',first)
   brief=json.loads((root/'content/cms/resume.json').read_text())['brief_cv'];brief=brief[0] if isinstance(brief,list) else brief
   for page in ['index.html','resume/index.html','projects/index.html']:
    html=(root/'dist'/page).read_text();self.assertIn('href="'+brief+'" download aria-label="Download CV — Europass Brief CV">Download CV',html)
   self.assertIn('Selected Bibliography',(root/'dist/resume/index.html').read_text())
   self.assertNotIn('Selected Bibliogrpahy',(root/'dist/resume/index.html').read_text())
   data['items'].reverse();data['items'].pop();p.write_text(json.dumps(data));subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   self.assertFalse((root/'dist'/links[0].strip('/')/'index.html').exists())
 def test_permanent_addresses_and_legacy_redirects(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   source=root/'content/cms/projects.json';data=json.loads(source.read_text())
   paths={p['path'] for p in data['items']}
   legacy=json.loads((root/'content/project-redirects.json').read_text())
   self.assertEqual(legacy['/project/2c631ae227efe57f'],'/project/66b9602360ee8e93')
   # Rename every project and reverse CMS order without changing any address.
   for p in data['items']:p['title']='Renamed '+p['title']
   data['items'].reverse();source.write_text(json.dumps(data))
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   archive=(root/'dist/projects/index.html').read_text()
   self.assertEqual(re.findall(r'href="(/project/[^\"]+)">View all details',archive),[p['path'] for p in data['items']])
   for p in data['items']:
    detail=(root/'dist'/p['path'].strip('/')/'index.html').read_text()
    self.assertIn(p['title'],detail)
    self.assertIn(p['path'],(root/'dist/sitemap.xml').read_text())
   rules=(root/'dist/_redirects').read_text().splitlines()
   for old,new in legacy.items():
    self.assertIn(new,paths)
    self.assertIn(old+' '+new+' 301',rules)
    self.assertIn(old+'/ '+new+' 301',rules)
    self.assertNotIn(old,(root/'dist/sitemap.xml').read_text())
   # Home and Expertise links still point at the same current projects.
   for name in ['index.html','expertise/index.html']:
    links=re.findall(r'href="(/project/[^\"]+)"',(root/'dist'/name).read_text())
    self.assertTrue(links)
    self.assertTrue(set(links)<=paths)
   # New projects can use readable URLs independent of their titles.
   data['items'].append({'title':'A new project','path':'/project/new-project','period':'2026','body':''})
   source.write_text(json.dumps(data));subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   self.assertTrue((root/'dist/project/new-project/index.html').exists())
 def test_invalid_project_routes_and_redirects_fail_build(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   source=root/'content/cms/projects.json';original=json.loads(source.read_text())
   mapping=root/'content/project-redirects.json';legacy=mapping.read_text()
   def fails(message):
    result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True)
    self.assertNotEqual(result.returncode,0);self.assertIn(message,result.stderr)
   for invalid in [None,'/project/../../outside','/project/name?query=yes','/about','/project/with space']:
    data=json.loads(json.dumps(original));data['items'][0]['path']=invalid;source.write_text(json.dumps(data))
    fails('Invalid or missing permanent project address')
   data=json.loads(json.dumps(original));data['items'][0]['path']=data['items'][1]['path'];source.write_text(json.dumps(data));fails('Duplicate permanent project address')
   source.write_text(json.dumps(original));path=original['items'][0]['path']
   for redirects,error in [({'/project/old':'/project/missing'},'destination must be an existing project'),({path:path},'conflicts with a current project'),({'/project/old':'/project/other','/project/other':'/project/old'},'destination must be an existing project')]:
    mapping.write_text(json.dumps(redirects));fails(error)
   mapping.write_text('{"/project/old":"'+path+'","/project/old":"'+path+'"}');fails('Duplicate project redirect source')
   mapping.write_text(legacy)
 def test_search_and_topic_combination(self):
  subprocess.run(['node','-e',r"""
const vm=require('vm'),fs=require('fs'),assert=require('assert');let filter,change;
const input={value:'',addEventListener:(n,f)=>filter=f};const select={value:'',options:[{value:''},{value:'Climate'}],addEventListener:(n,f)=>change=f};
const count={},empty={},cards=[{dataset:{search:'Laušević solar 2026',categories:'Climate'}},{dataset:{search:'Marine ecology 2026',categories:'Blue'}}];
const nodes={'#project-search':input,'#project-category':select,'#project-result-count':count,'#no-projects':empty};
vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{document:{querySelector:s=>nodes[s]||null,querySelectorAll:s=>s==='[data-project]'?cards:[]},location:{search:''},URLSearchParams});
assert.equal(count.textContent,'2 projects');input.value='lausevic 2026';filter();assert.equal(count.textContent,'1 project');assert.equal(cards[1].hidden,true);
input.value='2026';select.value='Climate';change();assert.equal(count.textContent,'1 project');input.value='marine';filter();assert.equal(empty.hidden,false);input.value='';select.value='';change();assert.equal(count.textContent,'2 projects');
"""],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
