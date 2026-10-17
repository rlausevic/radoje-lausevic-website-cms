"""Meaningful CMS build checks: content edits, publication and route validation."""
import unittest,tempfile,shutil,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class CMSBuild(unittest.TestCase):
 def test_content_and_publication(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp)/'site';shutil.copytree(ROOT,r,ignore=shutil.ignore_patterns('.git','.openai','__pycache__'))
   def build(ok=True):
    x=subprocess.run([sys.executable,'build.py'],cwd=r,capture_output=True,text=True)
    self.assertEqual(x.returncode==0,ok,x.stderr);return x
   h=r/'content/cms/home.json';d=json.loads(h.read_text());d['heading']='CMS editing check';h.write_text(json.dumps(d));build()
   self.assertIn('CMS editing check',(r/'dist/index.html').read_text())
   self.assertNotIn('{len(M', (r/'dist/blog/index.html').read_text())
   p=r/'content/cms/posts/test-entry.json';d={'title':'Test article','path':'/post/cms-check','date':'2026-10-13','published':False,'cover':'','excerpt':'Test excerpt','categories':['New topic'],'body':'<p>CMS body content</p>'};p.write_text(json.dumps(d));build();self.assertFalse((r/'dist/post/cms-check/index.html').exists())
   d['published']=True;p.write_text(json.dumps(d));build();self.assertIn('CMS body content',(r/'dist/post/cms-check/index.html').read_text());self.assertIn('New topic',(r/'dist/blog/index.html').read_text())
   d['published']=False;p.write_text(json.dumps(d));build();self.assertFalse((r/'dist/post/cms-check/index.html').exists());self.assertNotIn('/post/cms-check',(r/'dist/sitemap.xml').read_text())
   d['published']=True;d['path']='/post/../../outside';p.write_text(json.dumps(d));build(ok=False)
 def test_resume_optional_documents(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
   p=root/'content/cms/resume.json';data=json.loads(p.read_text())
   for key in ['brief_cv','europass_cv','assortis_cv','bibliography_file','education','publications']:data.pop(key,None)
   data['heading']='Updated resume from CMS'
   data['brief_cv_title']='Updated brief CV'
   data['brief_cv_description']='Current document from CMS'
   asset='/assets/'+next((root/'dist/assets').glob('*.pdf')).name
   data['brief_cv']=[asset];p.write_text(json.dumps(data))
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   html=(root/'dist/resume/index.html').read_text()
   for value in ['Updated resume from CMS','Updated brief CV','Current document from CMS',asset,'View full Bibliography']:self.assertIn(value,html)
   self.assertNotIn('Assortis CV</h2>',html)
   from cms_data import load_cms
   model=load_cms(root,json.loads((root/'content/site.json').read_text()))
   self.assertEqual(model['pages']['/resume']['links'],[{'text':'Download','href':asset}])
 def test_html_filter(self):
  from cms_data import body
  rendered=body('<p onclick="bad()">Hello<script>bad()</script><a href="javascript:bad()">link</a></p>')['html']
  self.assertNotIn('script',rendered);self.assertNotIn('onclick',rendered);self.assertNotIn('javascript',rendered);self.assertIn('Hello',rendered)
if __name__=='__main__':unittest.main()
