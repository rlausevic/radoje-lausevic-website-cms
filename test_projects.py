"""Project archive, details, CMS topic synchronization and shared search."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class ProjectArchive(unittest.TestCase):
 def test_cms_topics_details_and_footer(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   about=root/'content/cms/about.json';data=json.loads(about.read_text());data['services'].append({'title':'Test expertise','motto':'','summary':'Test','description':''});about.write_text(json.dumps(data))
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
   self.assertIn('href="/projects" aria-current="page"',first)
   brief=json.loads((root/'content/cms/resume.json').read_text())['brief_cv'];brief=brief[0] if isinstance(brief,list) else brief
   for page in ['index.html','resume/index.html','projects/index.html']:
    html=(root/'dist'/page).read_text();self.assertIn('href="'+brief+'" download>Download CV',html)
   self.assertIn('Selected Bibliography',(root/'dist/resume/index.html').read_text())
   self.assertNotIn('Selected Bibliogrpahy',(root/'dist/resume/index.html').read_text())
   data['items'].reverse();data['items'].pop();p.write_text(json.dumps(data));subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   self.assertFalse((root/'dist'/links[0].strip('/')/'index.html').exists())
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
