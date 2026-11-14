"""Multiple gallery topics across CMS synchronization, previews and archive filters."""
import json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from content_archives import read_archive
from scripts.sync_related_content import sync
ROOT=Path(__file__).resolve().parent
class GalleryTopics(unittest.TestCase):
 def test_sync_previews_details_photos_and_filters(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'site';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','.build-deps'))
   def topic_field():
    config=json.loads((root/'.pages.yml').read_text())
    return next(x for x in next(x for x in config['content'] if x['name']=='gallery_entries')['fields'] if x['name']=='topic')
   self.assertTrue(topic_field()['options']['multiple']);topics=topic_field()['options']['values'][:2]
   folder=root/'content/cms/gallery_entries';sample=next(x for x in read_archive(root,'gallery')['albums'] if x.get('photos'))
   item=dict(sample,title='Multiple gallery topics fixture',path='/gallery/multiple-topics-fixture',date='2099-01-02',topic=topics,body='<p>Unique gallery topic body</p>',photos=sample['photos'][:2])
   source=folder/'multiple-topics-test.json';source.write_text(json.dumps(item))
   legacy=folder/'legacy-topic-test.json';legacy.write_text(json.dumps(dict(item,title='Legacy gallery topic',path='/gallery/legacy-topic-test',date='2097-01-02',topic=topics[0])))
   optional=folder/'no-topic-test.json';no_topic=dict(item,title='No topic gallery',path='/gallery/no-topic-test',date='2098-01-02');no_topic.pop('topic');optional.write_text(json.dumps(no_topic))
   # Keep string selections supported even before the automatic CMS synchronization.
   result=subprocess.run([sys.executable,'build.py'],cwd=root,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   for name in ['index.html','insights/index.html','galleries/index.html']:
    html=(root/'dist'/name).read_text();self.assertIn('data-categories="'+'|'.join(topics)+'"',html)
    for topic in topics:self.assertIn('<span class="post-topic">'+topic+'</span>',html)
   detail=(root/'dist/gallery/multiple-topics-fixture/index.html').read_text()
   self.assertIn('Jan 02, 2099 · '+' · '.join(topics),detail)
   self.assertEqual(detail.count('data-gallery '),len(item['photos']))
   for photo in item['photos']:self.assertIn(photo['image'].split('/')[-1].split('.')[0] if '/media/' in photo['image'] else photo.get('title') or item['title'],detail)
   meta=re.search(r'<p class="article-meta">(.*?)</p>',(root/'dist/gallery/no-topic-test/index.html').read_text())[1]
   self.assertEqual(re.sub(r'<[^>]+>','',meta),'Jan 02, 2098')
   index=json.loads((root/'dist/galleries/archive-index.json').read_text());entry=next(x for x in index if item['path'] in x['html'])
   self.assertEqual(entry['topic'],topics)
   for topic in topics:self.assertIn(topic.lower(),entry['search'])
   subprocess.run(['node','-e',r"""
const fs=require('fs'),assert=require('assert');
const {selectEntries}=require('./dist/assets/journal.js');
const entries=JSON.parse(fs.readFileSync('dist/galleries/archive-index.json','utf8'));
const fixture=entries.find(x=>x.html.includes('/gallery/multiple-topics-fixture'));
for(const category of fixture.topic){
 const result=selectEntries(entries,{category,year:'2099',search:'unique gallery topic body',page:1});
 assert.equal(result.total,1);assert.equal(result.items[0],fixture);
}
assert.equal(selectEntries(entries,{category:'Missing topic',search:'unique gallery topic body'}).total,0);
"""],cwd=root,check=True)
   sync(root);self.assertEqual(json.loads(source.read_text()),item)
   self.assertEqual(json.loads(legacy.read_text())['topic'],[topics[0]])
   self.assertNotIn('topic',json.loads(optional.read_text()))
   before={p.name:p.read_bytes() for p in folder.glob('*.json')};sync(root)
   self.assertEqual({p.name:p.read_bytes() for p in folder.glob('*.json')},before)
   subprocess.run([sys.executable,'scripts/sync_expertise.py'],cwd=root,check=True)
   self.assertTrue(topic_field()['options']['multiple'])
if __name__=='__main__':unittest.main()
