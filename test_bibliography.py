from cms_data import project_sort_date
"""Verify bibliography fields, grouped ordering, attachments and shared archive search."""
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from content_archives import ARCHIVES,read_archive,write_archive
ROOT=Path(__file__).resolve().parent
class BibliographyCMS(unittest.TestCase):
 def test_ordered_sources_and_bibliography(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   def read(name):return read_archive(root,Path(name).stem) if Path(name).stem in ARCHIVES else json.loads((root/'content/cms'/name).read_text())
   def save(name,data):
    if Path(name).stem in ARCHIVES:write_archive(root,Path(name).stem,data)
    else:(root/'content/cms'/name).write_text(json.dumps(data))
   exp=read('experience.json');projects=read('projects.json')
   exp['items'].reverse();projects['items'].reverse()
   exp['items'][0]['order']=999;projects['items'][0]['order']=999
   save('experience.json',exp);save('projects.json',projects)
   b=read('bibliography.json');template=dict(b['items'][0],files=['/assets/'+next((root/'dist/assets').glob('*.pdf')).name])
   template.pop('id',None)
   b['items']=[dict(template,category='Articles',title='Second article'),dict(template,category='Publications',title='First publication',url='https://example.org/publication',files=[template['files'][0]],description='<p>Searchable detailed bibliography</p>'),dict(template,category='Articles',title='First article')]
   save('bibliography.json',b)
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   html=(root/'dist/bibliography/index.html').read_text()
   self.assertLess(html.index('First publication'),html.index('Second article'));self.assertLess(html.index('Second article'),html.index('First article'))
   self.assertIn('3 bibliography items',html);self.assertIn('>Download</a>',html);self.assertNotIn('<dl',html);self.assertIn('<ul class="bibliography-list">',html);self.assertIn('target="_blank"',html)
   self.assertIn('searchable detailed bibliography',html);self.assertIn('Invited lectures',html)
   for name,modelname in [('experience.json','experience_entries'),('projects.json','project_entries')]:
    code="import json;from pathlib import Path;from cms_data import load_cms;m=load_cms(Path('.'),json.loads(Path('content/site.json').read_text()));print(json.dumps([(p['title'],p['order']) for p in m['"+modelname+"']]))"
    data=json.loads(subprocess.check_output([sys.executable,'-c',code],cwd=root,text=True));expected=read(name)['items']
    if name=='projects.json':expected=sorted(expected,key=project_sort_date,reverse=True)
    self.assertEqual([p[0] for p in data],[p['title'] for p in expected]);self.assertEqual(sorted(p[1] for p in data),list(range(1,len(expected)+1)))
   home=(root/'dist/index.html').read_text();selected=sorted(projects['items'],key=project_sort_date,reverse=True)[:2];self.assertLess(home.index(selected[0]['title']),home.index(selected[1]['title']))
   # Shuffled years, equal-year ties, ranges and undated entries must work in every category.
   cases=[('Undated', ''),('Older', '1990-1991'),('Newest A', '2026'),('Range', '1993/94'),('Newest B', 2026),('Recent', '2022'),('Unknown', 'n.d.')]
   categories=['Publications','Articles','Conferences','Invited lectures']
   b['items']=[dict(template,category=category,title=category+' '+label,year=year) for label,year in cases for category in reversed(categories)]
   save('bibliography.json',b)
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   html=(root/'dist/bibliography/index.html').read_text();resume=(root/'dist/resume/index.html').read_text()
   for category in categories:
    expected=[category+' '+label for label in ['Newest A','Newest B','Recent','Range','Older','Undated','Unknown']]
    positions=[html.index(title) for title in expected];self.assertEqual(positions,sorted(positions))
    selected=[resume.index(title) for title in expected[:3]];self.assertEqual(selected,sorted(selected))
    for title in expected[3:]:self.assertNotIn(title,resume)
   positions=[html.index(category+' Newest A') for category in categories];self.assertEqual(positions,sorted(positions))
   b['items']=[];save('bibliography.json',b);result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr);self.assertIn('0 bibliography items',(root/'dist/bibliography/index.html').read_text())
   b['items']=[dict(template,title='')];save('bibliography.json',b);self.assertNotEqual(subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True).returncode,0)
 def test_shared_search_categories_and_terms(self):
  subprocess.run(['node','-e',r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
function test(prefix,selector,singular,plural,category=false){
 const events={};const input={value:'',addEventListener:(name,fn)=>events.search=fn};
 const select={value:'',options:[{value:''},{value:'Articles'},{value:'Publications'}],addEventListener:(name,fn)=>events.category=fn};
 const count={},empty={};const cards=[{dataset:{search:'Laušević Jordan water 2017',categories:'Articles'}},{dataset:{search:'Local water manual 2016',categories:'Publications'}}];
 const group={querySelectorAll:()=>cards};
 const names=prefix==='post'?['#post-search','#result-count','#no-results','#post-category']:prefix==='video'?['#video-search','#video-result-count','#no-videos',null]:['#bibliography-search','#bibliography-result-count','#no-bibliography','#bibliography-category'];
 const nodes={[names[0]]:input,[names[1]]:count,[names[2]]:empty};if(category)nodes[names[3]]=select;
 vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{document:{querySelector:s=>nodes[s]||null,querySelectorAll:s=>s===selector?cards:s==='[data-archive-group]'?[group]:[]},location:{search:''},URLSearchParams});
 assert.equal(count.textContent,'2 '+plural);
 input.value='2017 lausevic';events.search();assert.equal(count.textContent,'1 '+singular);assert.equal(cards[1].hidden,true);
 input.value='water';if(category){select.value='Publications';events.category();assert.equal(cards[0].hidden,true);assert.equal(count.textContent,'1 '+singular);}else events.search();
 input.value='missing';events.search();assert.equal(empty.hidden,false);
 input.value='';if(category)select.value='';events.search();assert.equal(count.textContent,'2 '+plural);assert.equal(empty.hidden,true);
}
test('post','[data-post]','article','articles',true);test('video','[data-video]','video','videos');test('bibliography','[data-bibliography]','bibliography item','bibliography items',true);
"""],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
