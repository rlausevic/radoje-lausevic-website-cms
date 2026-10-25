"""Navigation, source migration, Insights and document regression checks."""
import html,json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from content_archives import ARCHIVES,read_archive,write_archive
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class NavigationTests(unittest.TestCase):
 def test_every_page_navigation_documents_and_links(self):
  brief=json.loads((ROOT/'content/cms/resume.json').read_text())['brief_cv'];brief=brief[0] if isinstance(brief,list) else brief
  self.assertTrue((ROOT/'dist'/brief.lstrip('/')).read_bytes().startswith(b'%PDF'))
  pages=list((ROOT/'dist').rglob('*.html'));self.assertGreater(len(pages),40)
  header=None;footer=None
  class Links(HTMLParser):
   def __init__(self):super().__init__();self.links=[];self.ids=set()
   def handle_starttag(self,tag,attrs):
    a=dict(attrs)
    if a.get('id'):self.ids.add(a['id'])
    if tag=='a' and a.get('href'):self.links.append(a['href'])
  parsed={}
  for file in pages:
   text=file.read_text();p=Links();p.feed(text);parsed[file]=p
   h=re.search(r'<header class="site-header">(.*?)</header>',text).group(1)
   normalized=re.sub(r' aria-current="[^"]+"','',h)
   if header is None:header=normalized
   self.assertEqual(normalized,header,file)
   f=re.search(r'<footer class="footer">(.*?)</footer>',text).group(1)
   if footer is None:footer=f
   self.assertEqual(f,footer,file)
   for name in ['About','Expertise','Projects','Bibliography','Insights','Contact']:self.assertIn('>'+name+'</a>',h)
   for name in ['Home','Experience','Resume']:self.assertNotIn('>'+name+'</a>',h)
   self.assertIn('href="'+brief+'" download',h);self.assertIn('href="'+brief+'" download',f)
   self.assertIn('Career history',f);self.assertIn('CV &amp; documents',f)
   self.assertIn('aria-controls="insights-menu"',h);self.assertIn('id="insights-menu" hidden',h)
  for file,p in parsed.items():
   for link in p.links:
    if not link.startswith('/') or '#' not in link:continue
    path,fragment=link.split('#',1);target=ROOT/'dist'/path.lstrip('/');target=target/'index.html' if target.is_dir() else target
    if fragment and target in parsed:self.assertIn(fragment,parsed[target].ids,(file,link))
  for name in ['blog','video','galleries']:
   self.assertIn('href="/insights" aria-current="true"',(ROOT/'dist'/name/'index.html').read_text())
  about=(ROOT/'dist/about/index.html').read_text();order=['>Profile</h2>','>Career highlights</h2>','>Professional network</h2>','>Recommendations</h2>','>CV &amp; documents</h2>'];positions=[about.index(x) for x in order];self.assertEqual(positions,sorted(positions))
  self.assertIn('href="'+brief+'" download',about)
  self.assertTrue((ROOT/'dist/work-experience/index.html').exists());self.assertTrue((ROOT/'dist/resume/index.html').exists())
 def test_cms_single_source_and_insights(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   def read(name):return read_archive(root,Path(name).stem) if Path(name).stem in ARCHIVES else json.loads((root/'content/cms'/name).read_text())
   def save(name,data):
    if Path(name).stem in ARCHIVES:write_archive(root,Path(name).stem,data)
    else:(root/'content/cms'/name).write_text(json.dumps(data))
   self.assertNotIn('services',read('about.json'))
   expertise=read('expertise.json');expertise['services'][0]['summary']='One source expertise check';save('expertise.json',expertise)
   about=read('about.json');about['body']='<p>Updated profile check</p>';about['recommendations'][0]['summary']='Shared recommendation check';save('about.json',about)
   gallery=read('gallery.json');gallery['albums'][0].update(title='Shared album check',date='2099-01-01');save('gallery.json',gallery)
   archive=read('videos.json');archive['items'].reverse();save('videos.json',archive)
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   self.assertIn('One source expertise check',(root/'dist/index.html').read_text());self.assertIn('One source expertise check',(root/'dist/expertise/index.html').read_text())
   self.assertIn('Updated profile check',(root/'dist/about/index.html').read_text());self.assertIn('Shared recommendation check',(root/'dist/index.html').read_text())
   insights=(root/'dist/insights/index.html').read_text();self.assertIn('Shared album check',insights)
   self.assertEqual(insights.count('data-video '),min(3,len(archive['items'])))
   self.assertEqual(insights.count('data-post '),3)
   videos=sorted(archive['items'],key=lambda item:item['date'],reverse=True)[:3]
   pos=[insights.index(html.escape(x['title'])) for x in videos];self.assertEqual(pos,sorted(pos))
   self.assertEqual(insights.count('View full gallery →'),min(3,len(gallery['albums'])))
   schema=json.loads((root/'.pages.yml').read_text());about_schema=next(x for x in schema['content'] if x['name']=='about');expertise_schema=next(x for x in schema['content'] if x['name']=='expertise')
   self.assertNotIn('services',[x['name'] for x in about_schema['fields']]);self.assertIn('services',[x['name'] for x in expertise_schema['fields']])
 def test_disclosure_keyboard_escape_and_mobile_menu(self):
  subprocess.run(['node','-e',r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
function node(){const attrs={},events={},classes=new Set();return {attrs,events,hidden:true,textContent:'',classList:{contains:n=>classes.has(n),add:n=>classes.add(n),remove:n=>classes.delete(n)},setAttribute:(k,v)=>attrs[k]=v,addEventListener:(n,f)=>events[n]=f,focus(){this.focused=true;}};}
const toggle=node(),nav=node(),button=node(),menu=node(),first=node();menu.querySelector=()=>first;const docEvents={};
const nodes={'.menu-toggle':toggle,'#primary-nav':nav,'.insights-toggle':button,'#insights-menu':menu};
vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{document:{querySelector:s=>nodes[s]||null,querySelectorAll:()=>[],addEventListener:(n,f)=>docEvents[n]=f},location:{pathname:'/',search:''},URLSearchParams});
button.events.click();assert.equal(menu.hidden,false);assert.equal(button.attrs['aria-expanded'],'true');docEvents.keydown({key:'Escape',preventDefault(){}});assert.equal(menu.hidden,true);assert.equal(button.focused,true);
button.events.keydown({key:'ArrowDown',preventDefault(){}});assert.equal(menu.hidden,false);assert.equal(first.focused,true);
toggle.events.click();assert.equal(toggle.attrs['aria-expanded'],'true');assert(nav.classList.contains('open'));docEvents.keydown({key:'Escape',preventDefault(){}});assert(!nav.classList.contains('open'));assert.equal(toggle.attrs['aria-expanded'],'false');assert.equal(menu.hidden,true);assert.equal(toggle.focused,true);
"""],cwd=ROOT,check=True)
 def test_old_about_anchors_after_trailing_slash_redirect(self):
  subprocess.run(['node','-e',r"""
const vm=require('vm'),fs=require('fs'),assert=require('assert');
for(const pathname of ['/about','/about/']){let destination;vm.runInNewContext(fs.readFileSync('dist/assets/site.js','utf8'),{document:{querySelector:()=>null,querySelectorAll:()=>[]},location:{pathname,hash:'#expertise-3',search:'',replace:url=>destination=url},URLSearchParams});assert.equal(destination,'/expertise#expertise-3');}
"""],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
