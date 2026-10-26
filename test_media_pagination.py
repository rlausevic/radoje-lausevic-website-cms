"""Card archives share pagination; Bibliography retains its full grouped list."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from content_archives import read_archive,write_archive
ROOT=Path(__file__).resolve().parent
class MediaPagination(unittest.TestCase):
 def test_pages_full_indexes_and_cleanup(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   for name in ['videos','gallery']:
    data=read_archive(root,name);key='items' if name=='videos' else 'albums'
    sample=data[key][0];entries=[]
    for n in range(25):
     item=dict(sample,title=f'{name} {n}',date=f'2026-01-{n+1:02}',topic='Climate and Energy Planning',body=f'<p>Unique body term distant-{n}</p>')
     if name=='videos':item['link']=f'https://example.org/video-{n}'
     else:item.update(path=f'/gallery/pagination-{n}',photos=[])
     entries.append(item)
    data[key]=entries;write_archive(root,name,data)
   def build():subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   build()
   for route,selector in [('video','data-video'),('galleries','data-album')]:
    files=[root/f'dist/{route}/{path}' for path in ['index.html','page/2/index.html','page/3/index.html']]
    self.assertEqual([len(re.findall(r'\b'+selector+r'\s',p.read_text())) for p in files],[12,12,1])
    index=json.loads((root/f'dist/{route}/archive-index.json').read_text());self.assertEqual(len(index),25)
    self.assertIn('distant-0',index[-1]['search']);self.assertIn('Year',files[0].read_text())
    self.assertIn('href="/insights" aria-current="true"',files[-1].read_text())
    self.assertIn(f'href="/{route}/page/2/"',files[0].read_text())
    self.assertIn(f'data-archive-back="/{route}/"',next((root/('dist/video' if route=='video' else 'dist/gallery')).glob('*/index.html')).read_text())
   # Media paging does not remove or paginate bibliography records.
   bibliography=(root/'dist/bibliography/index.html').read_text()
   self.assertEqual(bibliography.count(' data-bibliography '),len(read_archive(root,'bibliography')['items']))
   self.assertIn('id="bibliography-year"',bibliography)
   for name in ['videos','gallery']:
    data=read_archive(root,name);data['items' if name=='videos' else 'albums']=[];write_archive(root,name,data)
   build()
   for route in ['video','galleries']:
    self.assertFalse((root/f'dist/{route}/page/2/index.html').exists())
    self.assertEqual(json.loads((root/f'dist/{route}/archive-index.json').read_text()),[])
 def test_bibliography_range_years(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   data=read_archive(root,'bibliography');sample=data['items'][0]
   data['items']=[dict(sample,id=None,title=label,year=value) for label,value in [('Slash range','1993/94'),('Full range','1990–1992'),('Century','1999/00'),('Unknown','n.d.')]]
   write_archive(root,'bibliography',data)
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   page=(root/'dist/bibliography/index.html').read_text()
   for value in ['1993|1994','1990|1991|1992','1999|2000','undated']:self.assertIn('data-years="'+value+'"',page)
   self.assertIn('>Undated</option>',page)
if __name__=='__main__':unittest.main()
