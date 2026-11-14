"""Journal uses expertise topics, with no obsolete theme metadata."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from content_archives import read_archive,write_archive
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class JournalTopics(unittest.TestCase):
 def test_multiple_topics_sync_previews_details_and_filter(self):
  from scripts.sync_related_content import sync
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   config=json.loads((root/'.pages.yml').read_text());field=next(x for x in next(x for x in config['content'] if x['name']=='posts')['fields'] if x['name']=='topic')
   self.assertTrue(field['options']['multiple']);topics=field['options']['values'][:2]
   folder=root/'content/cms/posts';source=folder/'multi-topic-test.json'
   item={'title':'Multiple topic fixture','path':'/post/multiple-topic-fixture','date':'2099-01-02','published':True,'excerpt':'Multiple topics preview','body':'<p>Unique multiple topic body</p>','topic':topics}
   source.write_text(json.dumps(item))
   legacy=folder/'legacy-topic-test.json';legacy.write_text(json.dumps(dict(item,title='Legacy selection',path='/post/legacy-selection',date='2098-01-02',topic=topics[0])))
   draft=folder/'draft-topic-test.json';draft.write_text(json.dumps(dict(item,title='Multiple topic draft',path='/post/multiple-topic-draft',published=False)))
   sync(root);self.assertEqual(json.loads(legacy.read_text())['topic'],[topics[0]]);self.assertEqual(json.loads(source.read_text()),item)
   self.assertEqual(json.loads(draft.read_text())['topic'],topics)
   before={p.name:p.read_bytes() for p in folder.glob('*.json')};sync(root)
   self.assertEqual({p.name:p.read_bytes() for p in folder.glob('*.json')},before)
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   for name in ['index.html','insights/index.html','blog/index.html']:
    html=(root/'dist'/name).read_text()
    self.assertIn('data-categories="'+'|'.join(topics)+'"',html)
    for topic in topics:self.assertIn('<span class="post-topic">'+topic+'</span>',html)
   detail=(root/'dist/post/multiple-topic-fixture/index.html').read_text()
   self.assertIn('Jan 02, 2099 · '+' · '.join(topics),detail)
   index=json.loads((root/'dist/blog/archive-index.json').read_text());entry=next(x for x in index if item['path'] in x['html'])
   self.assertEqual(entry['topic'],topics)
   for topic in topics:self.assertIn(topic.lower(),entry['search'])
   self.assertNotIn('Multiple topic draft',json.dumps(index))
   subprocess.run(['node','-e',r"""
const fs=require('fs'),assert=require('assert');
const {selectEntries}=require('./dist/assets/journal.js');
const entries=JSON.parse(fs.readFileSync('dist/blog/archive-index.json','utf8'));
const fixture=entries.find(x=>x.html.includes('/post/multiple-topic-fixture'));
for(const category of fixture.topic){
 const result=selectEntries(entries,{category,year:'2099',search:'unique multiple topic body',page:1});
 assert.equal(result.total,1);assert.equal(result.items[0],fixture);
}
assert.equal(selectEntries(entries,{category:'Missing topic',search:'unique multiple topic body'}).total,0);
"""],cwd=root,check=True)
 def test_topic_search_cards_metadata_and_legacy_routes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   schema=json.loads((root/'.pages.yml').read_text());fields=next(x for x in schema['content'] if x['name']=='posts')['fields']
   self.assertNotIn('categories',[x['name'] for x in fields]);self.assertIn('topic',[x['name'] for x in fields])
   for p in (root/'content/cms/posts').glob('*.json'):self.assertNotIn('categories',json.loads(p.read_text()))
   g=read_archive(root,'gallery')
   for album in g['albums']:album['photos']=[]
   write_archive(root,'gallery',g)
   path='/post/topic-check';topic='Environmental Research and Policy'
   item={'title':'Unique title','excerpt':'Unique excerpt','body':'<p>Unique body</p><a href="/blog/categories/old-theme">Continue</a>','topic':topic,'path':path,'date':'2099-01-02','published':True,'cover':'','categories':['ObsoleteSentinel']}
   (root/'content/cms/posts/topic-check.json').write_text(json.dumps(item))
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   archive=(root/'dist/blog/index.html').read_text()
   class Cards(HTMLParser):
    def __init__(self):super().__init__();self.cards=[]
    def handle_starttag(self,tag,attrs):
     a=dict(attrs)
     if 'data-post' in a:self.cards.append(a)
   parser=Cards();parser.feed(archive);card=next(x for x in parser.cards if x.get('href')==path)
   self.assertEqual(card['data-categories'],topic)
   for text in ['unique title','unique excerpt','unique body',topic.lower()]:self.assertIn(text,card['data-search'])
   for text in ['obsoletesentinel','2099','jan 02']:self.assertNotIn(text,card['data-search'])
   detail=(root/'dist/post/topic-check/index.html').read_text()
   self.assertIn('Jan 02, 2099 · '+topic,detail);self.assertNotIn('ObsoleteSentinel',detail)
   self.assertIn('href="/blog">Continue</a>',detail)
   for name in ['index.html','insights/index.html','blog/index.html']:
    html=(root/'dist'/name).read_text();self.assertIn('Read more',html);self.assertNotIn('Read article',html)
   self.assertIn('/blog/categories/* /blog 301',(root/'dist/_redirects').read_text())
   # An omitted optional topic does not leave an empty separator in the metadata.
   item.pop('topic');(root/'content/cms/posts/topic-check.json').write_text(json.dumps(item))
   subprocess.run([sys.executable,'build.py'],cwd=root,check=True,capture_output=True)
   detail=(root/'dist/post/topic-check/index.html').read_text()
   metadata=re.search(r'<p class="article-meta">(.*?)</p>',detail)[1]
   self.assertEqual(re.sub(r'<[^>]+>','',metadata),'Radoje Laušević · Jan 02, 2099')
if __name__=='__main__':unittest.main()
