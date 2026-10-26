#!/usr/bin/env python3
"""Build the portable static website, including optimized gallery images."""
from pathlib import Path
from html.parser import HTMLParser
import json,html,re,urllib.parse,datetime,hashlib,shutil,time
BUILD_STARTED=time.perf_counter()
ROOT=Path(__file__).resolve().parent; DIST=ROOT/'dist'
from cms_data import load_cms
from content_archives import read_archive
from related_content import video_path,bibliography_id,load_catalog,selected_content
from gallery_images import GalleryImages
gallery_images=GalleryImages(DIST)
M=load_cms(ROOT,json.loads((ROOT/'content/site.json').read_text())); S=M['site']; written=[]
resume=json.loads((ROOT/'content/cms/resume.json').read_text())
brief_files=resume.get('brief_cv') or []
if isinstance(brief_files,str):brief_files=[brief_files]
brief_cv_url=next((url for url in brief_files if urllib.parse.urlsplit(url).path.lower().endswith('.pdf')),brief_files[0] if brief_files else '')
E=lambda s:html.escape(str(s),quote=True)
related_catalog=load_catalog(ROOT)
ASSET_VERSION={name:hashlib.sha256((DIST/'assets'/name).read_bytes()).hexdigest()[:12] for name in ['site.css','site.js','contact.js','journal.js']}
NAV=[('/about','About'),('/expertise','Expertise'),('/projects','Projects'),('/bibliography','Bibliography'),('/insights','Insights'),('/contact','Contact')]
def cv_download(cls='button'):
 return f'<a class="{E(cls)}" href="{E(brief_cv_url)}" download aria-label="Download CV — Europass Brief CV">Download CV</a>' if brief_cv_url else ''
def image(src,alt='',cls='',eager=False):
 return f'<img src="{E(src)}" alt="{E(alt)}" class="{E(cls)}" loading="{"eager" if eager else "lazy"}" decoding="async">' if src else ''
def gallery_image(src,alt='',card=False):
 variants=gallery_images.prepare(src)
 if not variants:return image(src,alt)
 preview=variants['previews'][0]
 srcset=', '.join(f'{variant["url"]} {variant["width"]}w' for variant in variants['previews'])
 mobile='calc(100vw - 36px)' if card else 'calc((100vw - 56px) / 2)'
 sizes=f'(max-width: 600px) {mobile}, (max-width: 850px) calc((100vw - 68px) / 2), (max-width: 1100px) calc((100vw - 96px) / 3), (max-width: 1320px) calc((100vw - 128px) / 3), 400px'
 return f'<img src="{E(preview["url"])}" srcset="{E(srcset)}" sizes="{E(sizes)}" width="{preview["width"]}" height="{preview["height"]}" alt="{E(alt)}" loading="lazy" decoding="async">'
def render(b):
 if b['type']=='html':return b['html']
 if b['type']=='image':return image(b['src'],b['alt'])
 tag=b['type'] if b['type'] in ['h2','h3','h4','p','li'] else 'p'
 return f'<{tag}>{b["html"]}</{tag}>'
def render_all(bs):
 out=[];listing=False
 for b in bs:
  if b['type']=='li' and not listing:out.append('<ul>');listing=True
  elif b['type']!='li' and listing:out.append('</ul>');listing=False
  out.append(render(b))
 if listing:out.append('</ul>')
 return ''.join(out)

def apply_link_targets(document):
 # Normalize every rendered anchor, including CMS rich text and shared navigation.
 domain=urllib.parse.urlsplit(S['domain']).hostname or ''
 canonical=domain.removeprefix('www.').lower()
 internal_hosts={canonical,'www.'+canonical,'radoje-lausevic-website-cms.pages.dev'}
 class Anchors(HTMLParser):
  def __init__(self):
   super().__init__(convert_charrefs=False);self.edits=[]
  def handle_starttag(self,tag,attrs):
   if tag!='a':return
   attributes=dict(attrs);href=(attributes.get('href') or '').strip()
   parsed=urllib.parse.urlsplit(href)
   external=(parsed.scheme.lower() in {'http','https'} or (not parsed.scheme and bool(parsed.netloc))) and (parsed.hostname or '').lower() not in internal_hosts
   # Remove a stale target from internal links and email/telephone actions.
   attributes.pop('target',None)
   if external:
    attributes['target']='_blank'
    rel=set((attributes.get('rel') or '').lower().split())-{'opener'}
    attributes['rel']=' '.join(sorted(rel|{'noopener','noreferrer'}))
   replacement='<a'+''.join(' '+key+('="'+E(value)+'"' if value is not None else '') for key,value in attributes.items())+'>'
   line,column=self.getpos();offset=sum(len(value) for value in lines[:line-1])+column
   self.edits.append((offset,len(self.get_starttag_text()),replacement))
 lines=document.splitlines(keepends=True)
 parser=Anchors();parser.feed(document);parser.close()
 for offset,length,replacement in reversed(parser.edits):document=document[:offset]+replacement+document[offset+length:]
 return document

def page(path,title,body,desc=None):
 def fixlink(match):
  value=html.unescape(match.group(1))
  if value.startswith('/about#expertise-') or value=='/about#my-services':
   return 'href="/expertise#'+E(value.split('#',1)[1])+'"'
  if value.startswith('/blog/hashtags/'):
   return 'href="/blog?search='+E(urllib.parse.quote(urllib.parse.unquote(value.split('/')[-1])))+'"'
  if value.startswith('/blog/categories/'):
   return 'href="/blog"'
  return match.group(0)
 body=re.sub(r'href="([^"]+)"',fixlink,body)
 insights_paths=path in {'/insights','/blog','/video','/galleries'} or path.startswith(('/post/','/blog/page/','/video/','/gallery/'))
 active='/insights' if insights_paths else '/projects' if path.startswith('/project/') else '/about' if path in {'/resume','/work-experience'} else path
 nav=''
 for url,label in NAV:
  current=(' aria-current="page"' if path==url else ' aria-current="true"') if active==url else ''
  if url=='/insights':
   sub=''.join(f'<a href="{href}"'+(' aria-current="page"' if path==href else ' aria-current="true"' if (href=='/blog' and path.startswith(('/post/','/blog/page/'))) or (href=='/video' and path.startswith('/video/')) or (href=='/galleries' and path.startswith('/gallery/')) else '')+f'>{name}</a>' for href,name in [('/blog','Journal'),('/video','Video'),('/galleries','Galleries')])
   nav+=f'<div class="nav-insights"><div class="insights-controls"><a href="{url}"{current}>{label}</a><button class="insights-toggle" type="button" aria-label="Open Insights submenu" aria-expanded="false" aria-controls="insights-menu"><span aria-hidden="true">⌄</span></button></div><div class="insights-menu" id="insights-menu" hidden>{sub}</div></div>'
  else:nav+=f'<a href="{url}"{current}>{label}</a>'
 nav+=cv_download('button nav-download')
 schema={'@context':'https://schema.org','@type':'Person','name':S['name'],'url':S['domain'],'jobTitle':'Senior Environmental Consultant','email':S['email'],'sameAs':[S['linkedin'],S['twitter']]}
 if path.startswith('/post/'):
  post=next(p for p in M['posts'] if p['path']==path);schema={'@context':'https://schema.org','@type':'BlogPosting','headline':post['title'],'author':{'@type':'Person','name':S['name']},'mainEntityOfPage':S['domain']+path}
  try:schema['datePublished']=datetime.datetime.strptime(post['date'],'%b %d, %Y').date().isoformat()
  except ValueError:pass
 resume_styles='<style>.resume-education p,.resume-education li{line-height:1.4}.resume-education p{margin:0 0 6px}.resume-education h3{font-size:22px;line-height:1.3;margin:18px 0 6px}.resume-education h3:first-child{margin-top:0}</style>' if path=='/resume' else ''
 contact_script=f'<script src="/assets/contact.js?v={ASSET_VERSION["contact.js"]}" defer></script>' if path=='/contact' else ''
 journal_script=f'<script src="/assets/journal.js?v={ASSET_VERSION["journal.js"]}" defer></script>' if path=='/blog' or path.startswith(('/blog/page/','/post/')) else ''
 fulltitle=title+' | '+S['name'] if path!='/' else S['name']+' — Senior Environmental Consultant'
 contact_cta='<section class="cta"><div class="wrap"><div><h2>Let’s make progress together.</h2><p>Explore a project, exchange ideas, or discuss your next challenge.</p></div><a class="button" href="/contact">Get in touch <span aria-hidden="true">↗</span></a></div></section>' if path!='/contact' else ''
 data=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(fulltitle)}</title><meta name="description" content="{E(desc or S['description'])}"><meta name="theme-color" content="#193d3b"><link rel="canonical" href="{E(S['domain']+path)}"><meta property="og:type" content="{'article' if path.startswith('/post/') else 'website'}"><meta property="og:title" content="{E(fulltitle)}"><meta property="og:description" content="{E(desc or S['description'])}"><meta property="og:url" content="{E(S['domain']+path)}"><meta property="og:image" content="{E(S['domain']+S['portrait'])}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v={ASSET_VERSION['site.css']}">{resume_styles}{contact_script}{journal_script}<script src="/assets/site.js?v={ASSET_VERSION['site.js']}" defer></script><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script></head><body class="{'page-home' if path=='/' else 'page-inner page-about' if path=='/about' else 'page-inner'}"><a class="skip" href="#main">Skip to content</a><div class="topline"><div class="wrap"><span>ENVIRONMENT · PEOPLE · SUSTAINABILITY</span><a href="mailto:{S['email']}">{S['email']} &nbsp; ↗</a></div></div><header class="site-header"><div class="wrap header-row"><a class="brand" href="/" aria-label="Radoje Laušević home"><strong>{E(S['name'])}<span style="color:var(--accent);font-size:inherit;letter-spacing:0;display:inline">.</span></strong><span>{E(S['brand'])}</span></a><button class="menu-toggle" type="button" aria-controls="primary-nav" aria-expanded="false">Menu ☰</button><nav id="primary-nav" aria-label="Main navigation">{nav}</nav></div></header><main id="main">{body}</main>{contact_cta}<footer class="footer"><div class="wrap"><div class="footer-top"><div><strong>{S['name']}</strong><p>Senior Environmental Consultant<br>Partner Consulting · {S['location']}</p></div><div class="footer-links"><a href="/galleries">Galleries</a>{cv_download("footer-download")}<a href="/work-experience">Career history</a><a href="/resume">CV &amp; documents</a><a href="{S['linkedin']}" target="_blank" rel="noopener noreferrer">LinkedIn ↗</a><a href="{S['twitter']}" target="_blank" rel="noopener noreferrer">X / Twitter ↗</a><a href="mailto:{S['email']}">Email ↗</a></div></div><div class="footer-bottom"><span>© {datetime.date.today().year} Radoje Laušević. All rights reserved.</span><span>Leadership · Project management · Environmental research</span></div></div></footer></body></html>'''
 data=apply_link_targets(data)
 f=DIST/('index.html' if path=='/' else path.strip('/')+'/index.html');f.parent.mkdir(parents=True,exist_ok=True);f.write_text(data);written.append(path)
def intro(label,title,text=''):
 return f'<section class="page-intro"><div class="wrap"><span class="eyebrow">{E(label)}</span><h1>{E(title)}</h1><p>{E(text)}</p></div></section>'
def sections(path):
 bs=M['pages'][path]['blocks'];out=[];cur=None;lastimg=None
 for b in bs:
  if b['type']=='image':lastimg=b;continue
  if b['type']=='h2':
   cur={'title':b['text'],'blocks':[],'image':lastimg};out.append(cur);lastimg=None
  elif cur:cur['blocks'].append(b)
 return out
def post_search(p):
 return (p['title']+' '+p['excerpt']+' '+(p.get('topic') or '')+' '+' '.join(b.get('text','') for b in p['blocks'])).lower()
def post_card(p,heading='h3',include_search=True):
 topic=p.get('topic') or ''
 search=f' data-search="{E(post_search(p))}"' if include_search else ''
 badge=f'<span class="post-topic">{E(topic)}</span>' if topic else ''
 return f'<a class="post-card journal-card" data-post data-categories="{E(topic)}"{search} href="{E(p["path"])}"><div class="image-wrap">{image(p["cover"] or S["landscape"],p["title"])}</div><span class="date"><time datetime="{E(p["date_iso"])}">{E(p["date"])}</time> · JOURNAL</span>{badge}<{heading}>{E(p["title"])}</{heading}><p class="post-excerpt">{E(p["excerpt"])}</p><span class="read">Read more &nbsp; ↗</span></a>'
# A shared ordered source powers About and the home previews.
expertise_page=M['expertise']
expertise=expertise_page.get('services') or []
recommendations=M['about'].get('recommendations') or []
video_archive=read_archive(ROOT,'videos')
videos=[];video_paths=set()
for item in video_archive.get('items') or []:
 video=dict(item);link=video.get('link','').strip();parsed=urllib.parse.urlsplit(link)
 if parsed.scheme!='https' or not parsed.hostname or any(c.isspace() for c in link):raise ValueError('Invalid video link: '+link)
 video['link']=link
 path=video_path(link)
 if path in video_paths:raise ValueError('Duplicate video link: '+link)
 video_paths.add(path);video['path']=path
 video['date_iso']=datetime.date.fromisoformat(video['date'][:10]).isoformat()
 video['date_display']=datetime.date.fromisoformat(video['date_iso']).strftime('%b %d, %Y')
 video['content']=__import__('cms_data').body(video.get('body') or '')
 video['excerpt']=video.get('excerpt') or ''
 video['cover']=video.get('cover') or S['landscape']
 videos.append(video)
# Newest dates first across the archive and shared previews; retain CMS order for ties.
videos.sort(key=lambda video:video['date_iso'],reverse=True)
# Rebuild detail routes so removed videos do not leave stale pages behind.
if (DIST/'video').exists():shutil.rmtree(DIST/'video')
def video_card(video,heading='h3'):
 search=' '.join([video['title'],video['date_display'],video['date_iso'],video['excerpt'],video.get('topic') or '',video['content']['text']]).lower()
 return f'<article class="post-card video-card" data-video data-categories="{E(video.get("topic") or "")}" data-search="{E(search)}"><div class="video-detail-link"><div class="image-wrap">{image(video["cover"],video["title"])}</div><span class="date"><time datetime="{E(video["date_iso"])}">{E(video["date_display"])}</time> · VIDEO</span><{heading}>{E(video["title"])}</{heading}><p>{E(video["excerpt"])}</p></div><div class="video-actions"><a class="textlink" href="{E(video["path"])}">Read more →</a><a class="textlink" href="{E(video["link"])}" target="_blank" rel="noopener noreferrer">Watch video ↗</a></div></article>'
# Multiple albums share one CMS source across Home, Insights and the archive.
gallery_archive=read_archive(ROOT,'gallery')
galleries=[];gallery_paths=set()
for item in gallery_archive.get('albums') or []:
 album=dict(item);path=album.get('path') or ''
 if not re.fullmatch(r'/gallery/[A-Za-z0-9_-]+',path):raise ValueError('Invalid gallery address: '+path)
 if path in gallery_paths:raise ValueError('Duplicate gallery address: '+path)
 gallery_paths.add(path)
 album['date_iso']=datetime.date.fromisoformat(album['date'][:10]).isoformat()
 album['date_display']=datetime.date.fromisoformat(album['date_iso']).strftime('%b %d, %Y')
 album['photos']=[photo for photo in album.get('photos') or [] if photo.get('image')]
 album['content']=__import__('cms_data').body(album.get('body') or '')
 galleries.append(album)
galleries.sort(key=lambda album:(album['date_iso'],album['title']),reverse=True)
gallery_images.prepare_many(photo['image'] for album in galleries for photo in album['photos'])
if (DIST/'gallery').exists():shutil.rmtree(DIST/'gallery')
def gallery_card(album,heading='h3'):
 cover=album['photos'][0]['image'] if album['photos'] else S['landscape']
 search=' '.join([album['title'],album['date_iso'],album['date_display'],album.get('topic') or '',album.get('summary') or '',album['content']['text']]+[str(photo.get(key) or '') for photo in album['photos'] for key in ['title','caption']])
 return f'<article class="post-card gallery-card" data-album data-categories="{E(album.get("topic") or "")}" data-search="{E(search)}"><div class="image-wrap">{gallery_image(cover,album["title"],card=True)}</div><span class="date"><time datetime="{E(album["date_iso"])}">{E(album["date_display"])}</time> · GALLERY</span><{heading}>{E(album["title"])}</{heading}><p>{E(album.get("summary") or "")}</p><a class="textlink read" href="{E(album["path"])}">View full gallery →</a></article>'
def gallery_description(album):
 content=album['content'];words=content['text'].split()
 if not words:return ''
 full=render(content)
 if len(words)<=100:return '<div class="prose gallery-description">'+full+'</div>'
 preview=E(' '.join(words[:55]))+'…'
 return '<details class="prose gallery-description gallery-intro"><summary><span class="gallery-intro-preview">'+preview+'</span><span class="textlink gallery-read-more">Read more</span><span class="textlink gallery-read-less">Read less</span></summary><div class="gallery-intro-full">'+full+'</div></details>'
def topic_select(identifier):
 values=list(dict.fromkeys(item['title'] for item in expertise))
 return '<label for="'+identifier+'">Topic<select id="'+identifier+'"><option value="">All topics</option>'+''.join(f'<option value="{E(topic)}">{E(topic)}</option>' for topic in values)+'</select></label>'

projects=sections('/projects')
project_entries=M['project_entries']
expertise_topics=list(dict.fromkeys([item['title'] for item in expertise]+[item['topic'] for item in project_entries if item.get('topic')]))
def project_path(project):
 path=project.get('path')
 if not isinstance(path,str) or not re.fullmatch(r'/project/[A-Za-z0-9_-]+',path):
  raise ValueError('Invalid or missing permanent project address: '+str(path))
 return path
current_project_paths=[project_path(project) for project in project_entries]
if len(set(current_project_paths))!=len(current_project_paths):raise ValueError('Duplicate permanent project address')
def unique_redirects(pairs):
 result={}
 for source,target in pairs:
  if source in result:raise ValueError('Duplicate project redirect source: '+source)
  result[source]=target
 return result
project_redirects=json.loads((ROOT/'content/project-redirects.json').read_text(),object_pairs_hook=unique_redirects)
if not isinstance(project_redirects,dict):raise ValueError('Project redirects must be an address mapping')
for source,target in project_redirects.items():
 if not re.fullmatch(r'/project/[A-Za-z0-9_-]+',source):raise ValueError('Invalid project redirect source: '+source)
 if not isinstance(target,str) or target not in current_project_paths:raise ValueError('Project redirect destination must be an existing project: '+str(target))
 if source in current_project_paths:raise ValueError('Project redirect source conflicts with a current project: '+source)

# Home: compact editorial introduction; detailed source content on inner pages.
home=f'''<div class="wrap"><section class="hero"><div><span class="eyebrow">Senior Environmental Consultant</span><h1>{E(M["home"]["heading"])}</h1><p class="lead">{E(M["home"]["lead"])}</p><div class="actions"><a class="button" href="/projects">Explore my work <span aria-hidden="true">↗</span></a><a class="textlink" href="/about">Meet Radoje →</a></div><p class="hero-foot">Biologist · Project manager · Environmental leader</p></div><figure class="hero-art"><div class="accent-block"></div>{image(S['portrait'],S['name']+' — environmental consultant','portrait',True)}<figcaption class="portrait-note">PhD in Biology · University of Belgrade</figcaption></figure></section></div><div class="stat-strip"><div class="wrap stats"><div class="stat"><strong>100+</strong><span>Projects managed<br>or supervised</span></div><div class="stat"><strong>€50m+</strong><span>Total project<br>portfolio</span></div><div class="stat"><strong>5</strong><span>Connected fields<br>of expertise</span></div></div></div>'''
home+='<section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">How I can help</span><h2>Experience that moves<br>ideas into action.</h2></div><a class="textlink" href="/expertise">View all expertise →</a></div><div class="services">'
for i,item in enumerate(expertise[:3]):
 home+=f'<article class="service"><span class="num">0{i+1} / EXPERTISE</span><h3>{E(item["title"])}</h3><p class="motto">{E(item.get("motto") or "")}</p><p>{E(item.get("summary") or "")}</p><a class="textlink" href="/expertise#expertise-{i+1}">Learn more →</a></article>'
home+='</div></div></section>'
home+=f'<div class="landscape">{image(S["landscape"],"Aerial view of islands from the original website")}<div class="caption">{E(M["home"]["landscape_quote"])}<small>Connecting with nature</small></div></div>'
home+='<section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Selected work</span><h2>From research to impact.</h2></div><a class="textlink" href="/projects">View all projects →</a></div><div class="project-grid">'
for i,p in enumerate(projects[:2]):
 desc=M['project_summaries'].get(p['title'],'')
 title=p['title']
 assignment=project_entries[i]['period']
 assignment_label=f'<p class="project-assignment"><strong>My assignment:</strong> {E(assignment)}</p>' if assignment else ''
 home+=f'<a class="project-card" href="{E(project_path(project_entries[i]))}"><div class="image-wrap">{image(p["image"]["src"],p["title"])}</div><h3>{title}</h3>{assignment_label}<p>{E(desc[:180])}…</p></a>'
home+='</div></div></section>'
# The first two full recommendations in About provide the home excerpts.
home+=f'<section class="section testimonials"><div class="wrap"><div class="section-head"><div><span class="eyebrow">{E(M["home"].get("recommendations_label", "Recommendations"))}</span><h2>{E(M["home"].get("recommendations_heading", "Trusted by colleagues."))}</h2></div><a class="textlink" href="/about#recommendations">View all recommendations →</a></div><div class="quotes">'
for recommendation in recommendations[:2]:
 home+=f'<blockquote><div class="quote-mark">“</div><p>{E(recommendation["summary"])}</p><cite>{E(recommendation["author"])}</cite></blockquote>'
home+='</div></div></section>'
# One latest item per collection keeps Home compact; Insights retains the full previews.
home+='<section class="section home-insights" id="home-insights"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Insights</span><h2>Latest from the field.</h2></div><a class="button" href="/insights">Explore Insights →</a></div><div class="journal-grid">'
home+=''.join(post_card(post) for post in M['posts'][:1])
home+=''.join(video_card(video) for video in videos[:1])
home+=''.join(gallery_card(album) for album in galleries[:1])
home+='</div></div></section>';page('/','Home',home)
# About: shared source records provide career highlights, network and recommendations.
about=M['about'];network_data=json.loads((ROOT/'content/cms/network.json').read_text())
body=intro('About','Experience, with purpose.','A biologist’s perspective. An environmental leader’s experience. A practical approach to sustainability.')
body+='<section class="section" id="profile"><div class="wrap two-col"><aside class="side-note">'+image(S['portrait'],S['name'])+'<p>PhD in Biology<br>University of Belgrade</p></aside><div class="prose"><h2>Profile</h2>'+render(__import__('cms_data').body(about.get('body') or ''))
body+='<div id="my-services">'+''.join(f'<span id="expertise-{i+1}" class="legacy-anchor"></span>' for i in range(len(expertise)))+'<p>'+E(about.get('expertise_intro') or '')+'</p><a class="textlink" href="/expertise">Explore my expertise →</a></div></div></div></section>'
selected=set(about.get('career_highlights') or [])
career=[item for item in M['experience_entries'] if item['title'] in selected]
if career:
 body+='<section class="section" id="career-highlights"><div class="wrap prose"><h2>Career highlights</h2>'
 body+='<div class="career-cards">'
 for item in career:
  body+=f'<details class="career-card"><summary><h3>{E(item["title"])}</h3><span class="date">{E(item["period"])}</span><span class="textlink career-expand">View details →</span><span class="textlink career-collapse">Hide details ↑</span></summary><div class="career-content">'+render(__import__('cms_data').body(item.get('body') or ''))+'</div></details>'
 body+='</div>'
 body+='<p><a class="textlink" href="/work-experience">View full career history →</a></p></div></section>'
body+='<section class="section" id="professional-network"><div class="wrap prose"><h2>Professional network</h2>'+render(__import__('cms_data').body(network_data.get('body') or ''))
network_documents=network_data.get('document') or []
if isinstance(network_documents,str):network_documents=[network_documents]
for url in network_documents:body+=f'<p><a class="textlink" href="{E(url)}" download>Download the full network list ↓</a></p>'
body+='</div></section>'
if recommendations:
 body+='<section class="section testimonials" id="recommendations"><div class="wrap prose"><span class="eyebrow">Professional recommendations</span><h2>Recommendations</h2>'
 body+='<div class="recommendation-cards">'
 for item in recommendations:
  body+=f'<details class="recommendation-card"><summary><h3>{E(item["author"])}</h3><span class="recommendation-summary">{E(item.get("summary") or "")}</span><span class="textlink recommendation-expand">View full recommendation →</span><span class="textlink recommendation-collapse">Hide full recommendation ↑</span></summary><blockquote class="recommendation-content">'+render(__import__('cms_data').body(item.get('body') or ''))+'</blockquote></details>'
 body+='</div>'
 body+='</div></section>'
body+='<section class="section" id="cv-documents"><div class="wrap prose"><h2>CV &amp; documents</h2><div class="actions">'+cv_download()+'<a class="textlink" href="/resume">View full CV &amp; documents →</a></div></div></section>';page('/about','About',body)
# Expertise is the sole service source for this page, Home and project topics.
body=intro(expertise_page.get('label','Expertise'),expertise_page.get('heading','Expertise.'),expertise_page.get('lead',''))+'<section class="section" id="my-services"><div class="wrap journal-grid expertise-grid">'
for i,item in enumerate(expertise):
 body+=f'<details class="expertise-card" id="expertise-{i+1}"><summary><h2>{E(item["title"])}</h2><span class="expertise-summary">{E(item.get("summary") or "")}</span><span class="textlink expertise-expand">View details →</span><span class="textlink expertise-collapse">Hide details ↑</span></summary><div class="prose expertise-content"><p class="motto">{E(item.get("motto") or "")}</p>'
 support=__import__('cms_data').body(item.get('support') or '')
 if support['text']:body+='<h3>Services</h3>'+render(support)
 detail=__import__('cms_data').body(item.get('description') or '')
 if detail['text']:body+='<h3>Experience &amp; approach</h3>'+render(detail)
 related=[project for project in project_entries if project.get('topic')==item['title']]
 if related:body+='<h3>Selected projects</h3><ul>'+''.join(f'<li><a href="{E(project_path(project))}">{E(project["title"])}</a></li>' for project in related)+'</ul>'
 body+='<p><a class="textlink" href="/contact">Discuss a collaboration →</a></p></div></details>'
body+='</div></section>';page('/expertise','Expertise',body,expertise_page.get('lead'))
# Insights draws directly from the existing archives, never copied entries.
body=intro('Insights','Ideas, conversations & field stories.','Explore articles, video conversations and moments from the field.')
if M['posts']:
 body+='<section class="section"><div class="wrap"><div class="section-head"><h2>Journal</h2><a class="textlink" href="/blog">View all articles →</a></div><div class="journal-grid">'+''.join(post_card(post,'h3') for post in M['posts'][:3])+'</div></div></section>'
if videos:
 body+='<section class="section"><div class="wrap"><div class="section-head"><h2>Video</h2><a class="textlink" href="/video">View all videos →</a></div><div class="journal-grid">'+''.join(video_card(video,'h3') for video in sorted(videos,key=lambda item:item['date_iso'],reverse=True)[:3])+'</div></div></section>'
if galleries:
 body+='<section class="section"><div class="wrap"><div class="section-head"><h2>Galleries</h2><a class="textlink" href="/galleries">View all galleries →</a></div><div class="journal-grid">'+''.join(gallery_card(album) for album in galleries[:3])+'</div></div></section>'
page('/insights','Insights',body)
# Video archive shares Journal typography, card layout and search behavior.
body=intro(video_archive.get('label','Video archive'),video_archive.get('heading','Conversation on sustainability'),video_archive.get('lead','Project updates, environmental insights and personal observations'))+'<section class="section" style="padding-top:0"><div class="wrap"><div class="filters"><label for="video-search">Search video archive<input type="search" id="video-search" placeholder="Search video archive…" aria-controls="video-results"></label>'+topic_select('video-category')+'</div>'
body+=f'<p class="result-count" id="video-result-count" role="status" aria-live="polite">{len(videos)} {"video" if len(videos)==1 else "videos"}</p><div class="journal-grid" id="video-results">'+''.join(video_card(video,'h2') for video in videos)+'</div><p class="empty" id="no-videos"'+(' hidden' if videos else '')+'>No videos found. Try another search.</p></div></section>'
page('/video','Video',body,video_archive.get('lead'))
for video in videos:
 body=f'<article class="article"><div class="wrap"><header class="article-head"><a class="textlink" href="/video">← Back to video archive</a><h1>{E(video["title"])}</h1><p class="article-meta"><time datetime="{E(video["date_iso"])}">{E(video["date_display"])}</time> · VIDEO</p></header><div class="prose">'
 body+=image(video['cover'],video['title'])+(render(video['content']) if video['content']['text'] else f'<p>{E(video["excerpt"])}</p>')+f'<p><a class="button" href="{E(video["link"])}" target="_blank" rel="noopener noreferrer">Watch video ↗</a></p>'
 body+='</div></div></article>';page(video['path'],video['title'],body,video['excerpt'])
# Work experience.
body=intro('Professional journey','Work experience.','Leadership, research and project management across universities, international organisations and consultancy.')+'<section class="section"><div class="wrap">'
for sec in sections('/work-experience'):
 if sec['title']=='My Professional Network':continue
 blocks=sec['blocks'];date=blocks[0]['text'] if blocks else ''
 body+=f'<article class="timeline-row"><div class="date">{E(date)}</div><div><h2>{E(sec["title"])}</h2>'+render_all(b for b in blocks[1:] if b.get('text')!='On the Path to Success')+'</div></article>'
body+='</div></section><section class="section testimonials"><div class="wrap prose"><span class="eyebrow">Collaboration</span><h2>My professional network</h2>'
network=next(x for x in sections('/work-experience') if x['title']=='My Professional Network');body+=render_all(network['blocks'])
links=M['pages']['/work-experience']['links'];full=next((a['href'] for a in links if a['text']=='Get full list'),'')
body+=f'<p><a class="button" href="{E(full)}" download>Download the full network list ↓</a></p></div></section>';page('/work-experience','Work experience',body)
# Projects archive uses Journal cards and the shared search engine.
if (DIST/'project').exists():shutil.rmtree(DIST/'project')
body=intro('Selected portfolio','Projects.','A selection from more than 100 projects managed or supervised, with a total portfolio exceeding €50 million.')+'<section class="section" style="padding-top:0"><div class="wrap"><div class="filters"><label for="project-search">Search projects<input type="search" id="project-search" placeholder="Search projects…" aria-controls="project-results"></label><label for="project-category">Topic of expertise<select id="project-category"><option value="">All topics</option>'+''.join(f'<option value="{E(topic)}">{E(topic)}</option>' for topic in expertise_topics)+'</select></label></div>'
body+=f'<p class="result-count" id="project-result-count" role="status" aria-live="polite">{len(project_entries)} projects</p><div class="journal-grid" id="project-results">'
project_paths=set()
for i,project in enumerate(project_entries):
 path=project_path(project)
 if path in project_paths:raise ValueError('Duplicate project address: '+path)
 project_paths.add(path)
 detail=__import__('cms_data').body(project.get('body') or '')
 topic=project.get('topic') or ''
 search=' '.join([project['title'],project.get('full_name') or '',project['period'],project.get('project_duration') or '',project.get('role') or '',project.get('summary') or '',topic,detail['text']]+[__import__('cms_data').body(project.get(field) or '')['text'] for field in ['contribution','results']]+[project.get(field) or '' for field in ['assignment_start','assignment_end','project_start','project_end']]).lower()
 assignment_label=f'<p class="project-assignment"><strong>My assignment:</strong> {E(project["period"])}</p>' if project['period'] else ''
 body+=f'<article class="post-card project-archive-card" id="project-{i+1}" data-project data-categories="{E(topic)}" data-search="{E(search)}"><div class="image-wrap">{image(project.get("image") or S["landscape"],project.get("image_alt") or project["title"])}</div><h2>{E(project["title"])}</h2>{assignment_label}<p>{E(project.get("summary") or "")}</p><div class="project-actions"><a class="textlink" href="{E(path)}">View all details →</a></div></article>'
body+='</div><p class="empty" id="no-projects" hidden>No projects found. Try another search or select all topics.</p></div></section>';page('/projects','Projects',body)
def related_links(project):
 groups=selected_content(project,related_catalog)
 if not groups:return ''
 links=''.join('<li><span class="related-type">'+E(label)+' · </span><a href="'+E(item['href'])+'">'+E(item['title'])+'</a></li>' for _,label,items in groups for item in items)
 return '<section class="project-section related-content"><h2>Related content:</h2><ul class="related-list">'+links+'</ul></section>'
for project in project_entries:
 body=f'<article class="article project-page"><div class="wrap"><header class="article-head"><a class="textlink" href="/projects">← Back to projects</a><h1>{E(project["title"])}</h1></header><div class="prose">'
 body+='<div class="project-facts">'
 for label,value in [('Full project name:',project.get('full_name') or ''),('Project duration:',project.get('project_duration') or ''),('My role:',project.get('role') or ''),('My assignment:',project['period'])]:
  if value:body+='<p><strong>'+label+'</strong> '+E(value)+'</p>'
 body+='</div>'+image(project.get('image') or S['landscape'],project.get('image_alt') or project['title'],'project-cover')
 for field,label in [('body','Project overview:'),('contribution','My contribution:'),('results','Selected results:')]:
  content=__import__('cms_data').body(project.get(field) or '')
  if content['text'] or '<img ' in content['html']:body+='<section class="project-section"><h2>'+label+'</h2>'+render(content)+'</section>'
 body+=related_links(project)+'</div></div></article>'
 page(project_path(project),project['title'],body,project.get('summary'))
# Resume files and publication attachments managed through Pages CMS.
def document_files(value):
 if value is None:return []
 if isinstance(value,str):return [value] if value.strip() else []
 if isinstance(value,list) and all(isinstance(item,str) for item in value):return [item for item in value if item.strip()]
 raise ValueError('Document files must be a path or list of paths')
def document_link(value):
 url=(value or '').strip()
 if not url:return ''
 if not (url.startswith('/assets/') or url.startswith('https://')):
  raise ValueError('Document must use /assets/ or https://: '+url)
 if url.startswith('/assets/') and not (DIST/urllib.parse.unquote(url.lstrip('/'))).is_file():
  raise ValueError('Document not found: '+url)
 return url
def document_downloads(value):
 links=[]
 for value in document_files(value):
  url=document_link(value)
  links.append(f'<p><a class="textlink" href="{E(url)}" download>Download</a></p>')
 return ''.join(links)
def download_card(title,description,value):
 links=document_downloads(value)
 if not links:return ''
 return f'<article class="download"><span>Documents</span><h2>{E(title)}</h2><p>{E(description)}</p>{links}</article>'
# Bibliography: newest year first; stable ties preserve the CMS list order.
bibliography=read_archive(ROOT,'bibliography')
bibliography_categories=['Publications','Articles','Conferences','Invited lectures']
def bibliography_year(item):
 # Use the first year for ranges such as 1993/94 and 1990-1991; undated entries go last.
 match=re.search(r'(?<!\d)(\d{4})(?!\d)',str(item.get('year') or ''))
 return int(match.group(1)) if match else -1
bibliography_items=sorted(bibliography.get('items') or [],key=bibliography_year,reverse=True)
category_descriptions={item['name']:item.get('description') or '' for item in bibliography.get('categories') or []}
for item in bibliography_items:
 if not str(item.get('title') or '').strip():raise ValueError('Bibliography: Title is required')
 if item.get('category') not in bibliography_categories:raise ValueError('Bibliography: choose a valid category')
 url=(item.get('url') or '').strip()
 if url:
  parsed=urllib.parse.urlsplit(url)
  if parsed.scheme not in {'http','https'} or not parsed.hostname:raise ValueError('Bibliography: invalid URL '+url)
def bibliography_citation(item):
 authors=str(item.get('authors') or '').strip()
 year=str(item['year']).strip() if item.get('year') is not None else ''
 prefix=' '.join(part for part in [authors,'('+year+')' if year else ''] if part)
 title=str(item['title']).strip()
 def sentence(value):
  value=str(value or '').strip()
  return E(value)+('' if value.endswith(('.', '?', '!')) else '.') if value else ''
 citation=(E(prefix)+': ' if prefix else '')+sentence(title)
 venue=', '.join(str(item.get(field) or '').strip() for field in ['venue','volume_issue_pages'] if str(item.get(field) or '').strip())
 for value in [venue,item.get('publisher')]:
  if value:citation+=' '+sentence(value)
 url=str(item.get('url') or '').strip()
 if url:citation+=f' <a href="{E(url)}">{E(url)}</a>.'
 return citation
body=intro(bibliography.get('label','Bibliography'),bibliography.get('heading','Research, knowledge and dialogue.'),bibliography.get('lead',''))+'<section class="section" style="padding-top:0"><div class="wrap"><div class="filters"><label for="bibliography-search">Search Bibliography<input type="search" id="bibliography-search" placeholder="Search Bibliography…" aria-controls="bibliography-results"></label><label for="bibliography-category">Category<select id="bibliography-category"><option value="">All categories</option>'+''.join(f'<option value="{E(category)}">{E(category)}</option>' for category in bibliography_categories)+'</select></label></div>'
body+=f'<p class="result-count" id="bibliography-result-count" role="status" aria-live="polite">{len(bibliography_items)} bibliography {"item" if len(bibliography_items)==1 else "items"}</p><div id="bibliography-results">'
for category in bibliography_categories:
 items=[item for item in bibliography_items if item['category']==category]
 body+=f'<section class="bibliography-group" data-archive-group><h2>{E(category)}</h2><p class="category-description">{E(category_descriptions.get(category,""))}</p>'
 if items:body+='<ul class="bibliography-list">'
 for item in items:
  description=__import__('cms_data').body(item.get('description') or '')
  searchable=' '.join(str(item.get(field) or '') for field in ['category','title','year','url','reference','authors','venue','volume_issue_pages','publisher'])+' '+description['text']
  body+=f'<li class="bibliography-item" id="bibliography-{E(bibliography_id(item))}" data-bibliography data-categories="{E(category)}" data-search="{E(searchable.lower())}"><span class="bibliography-citation">{bibliography_citation(item)}</span>'
  if description['text']:body+=' <details class="bibliography-description"><summary>Description</summary><div class="prose">'+render(description)+'</div></details>'
  for index,value in enumerate(document_files(item.get('files')),1):
   url=document_link(value)
   body+=f' <a class="bibliography-download" href="{E(url)}" download aria-label="Download: {E(item["title"])} ({index})">Download</a>'
  body+='</li>'
 if items:body+='</ul>'
 if not items:body+='<p class="category-empty">No entries in this category yet.</p>'
 body+='</section>'
body+='</div><p class="empty" id="no-bibliography"'+(' hidden' if bibliography_items else '')+'>No bibliography items found. Try another search or select all categories.</p></div></section>'
page('/bibliography','Bibliography',body,bibliography.get('lead'))
body=intro(resume.get('label','Qualifications & publications'),resume.get('heading','Resume.'),resume.get('lead','Explore my academic background, download a CV and read selected publications.'))+'<section class="section"><div class="wrap"><div class="download-grid">'
for key,title,description in [('brief_cv','Brief CV','Concise overview of work experience and skills.'),('europass_cv','Europass CV','Detailed experience, education, skills, projects and publications.'),('assortis_cv','Assortis CV','Professional experience and project record in Assortis format.')]:
 body+=download_card(resume.get(key+'_title',title),resume.get(key+'_description',description),resume.get(key))
body+=download_card(resume.get('bibliography_title','Complete bibliography'),'',resume.get('bibliography_file'))
body+='</div><div class="prose"><h2>Education</h2><div class="resume-education">'+render(__import__('cms_data').body(resume.get('education','')))+'</div><h2>Selected Bibliography</h2>'
for category in bibliography_categories:
 items=[item for item in bibliography_items if item['category']==category][:3]
 body+=f'<section class="bibliography-group"><h3>{E(category)}</h3>'
 if items:body+='<ul class="bibliography-list">'
 for item in items:
  body+=f'<li class="bibliography-item"><span class="bibliography-citation">{bibliography_citation(item)}</span>'
  description=__import__('cms_data').body(item.get('description') or '')
  if description['text']:body+=' <details class="bibliography-description"><summary>Description</summary><div class="prose">'+render(description)+'</div></details>'
  for index,value in enumerate(document_files(item.get('files')),1):
   url=document_link(value)
   body+=f' <a class="bibliography-download" href="{E(url)}" download aria-label="Download: {E(item["title"])} ({index})">Download</a>'
  body+='</li>'
 if items:body+='</ul>'
 else:body+='<p class="category-empty">No entries in this category yet.</p>'
 body+='</section>'
body+='<p><a class="textlink" href="/bibliography">View full Bibliography →</a></p></div></div></section>';page('/resume','Resume',body)
# Gallery archive and stable individual album routes.
body=intro(gallery_archive.get('label') or 'Photo galleries',gallery_archive.get('heading') or 'My favourite photos.',gallery_archive.get('lead') or '')+'<section class="section"><div class="wrap"><div class="filters"><label for="gallery-search">Search the gallery<input type="search" id="gallery-search" placeholder="Search the gallery…" aria-controls="gallery-results"></label>'+topic_select('gallery-category')+'</div>'
body+=f'<p class="result-count" id="gallery-result-count" role="status" aria-live="polite">{len(galleries)} '+('gallery' if len(galleries)==1 else 'galleries')+'</p><div class="journal-grid" id="gallery-results">'+''.join(gallery_card(album,'h2') for album in galleries)+'</div><p class="empty" id="no-galleries"'+(' hidden' if galleries else '')+'>No galleries found. Try another search or select all topics.</p></div></section>'
page('/galleries','Galleries',body)
for album in galleries:
 body='<article class="article"><div class="wrap"><header class="article-head"><a class="textlink" href="/galleries">← Back to galleries</a><h1>'+E(album['title'])+'</h1><p class="article-meta">'+E(album['date_display'])+(' · '+E(album['topic']) if album.get('topic') else '')+'</p></header>'
 related_projects=[project for project in project_entries if any(key=='galleries' and any(item['href']==album['path'] for item in items) for key,_,items in selected_content(project,related_catalog))]
 if related_projects:body+='<div class="gallery-projects prose"><p><strong>'+('Related project' if len(related_projects)==1 else 'Related projects')+':</strong></p><ul class="related-list">'+''.join('<li><a href="'+E(project_path(project))+'">'+E(project['title'])+'</a></li>' for project in related_projects)+'</ul></div>'
 body+=gallery_description(album)+'<div class="gallery-grid">'
 for photo in album['photos']:
  caption=photo.get('caption') or photo.get('title') or album['title']
  variants=gallery_images.prepare(photo['image'])
  enlarged=variants['large']['url'] if variants else photo['image']
  body+=f'<button class="gallery-button" type="button" data-gallery data-src="{E(enlarged)}" data-caption="{E(caption)}" aria-label="Enlarge {E(photo.get("title") or album["title"])}">{gallery_image(photo["image"],caption)}<span>{E(photo.get("title") or "View photo")} ↗</span></button>'
 body+='</div></div></article><dialog class="gallery-dialog" id="gallery-dialog" aria-label="Photo viewer" aria-describedby="gallery-caption"><div class="gallery-toolbar"><span class="gallery-counter" data-gallery-counter role="status" aria-live="polite" aria-atomic="true"></span><button type="button" data-gallery-close autofocus aria-label="Close photo viewer">Close ×</button></div><div class="gallery-stage"><img alt="" draggable="false"></div><p id="gallery-caption"></p><div class="gallery-controls"><button type="button" data-gallery-previous aria-label="Previous photo">← Previous</button><button type="button" data-gallery-next aria-label="Next photo">Next →</button></div></dialog>'
 page(album['path'],album['title'],body,album.get('summary'))
# Render genuine archive pages; fetch the compact global index only for filtering/navigation.
journal_archive=json.loads((ROOT/'content/cms/journal.json').read_text())
JOURNAL_PAGE_SIZE=12
journal_pages=max(1,(len(M['posts'])+JOURNAL_PAGE_SIZE-1)//JOURNAL_PAGE_SIZE)
journal_index=[{'year':p['date_iso'][:4],'topic':p.get('topic') or '', 'search':post_search(p),'html':post_card(p,'h2',False)} for p in M['posts']]
journal_json=json.dumps(journal_index,ensure_ascii=False,separators=(',',':'))
journal_version=hashlib.sha256(journal_json.encode()).hexdigest()[:12]
(DIST/'blog').mkdir(exist_ok=True)
(DIST/'blog/archive-index.json').write_text(journal_json)
# Remove obsolete numbered pages if entries were removed or unpublished.
if (DIST/'blog/page').exists():shutil.rmtree(DIST/'blog/page')
def journal_page_url(number):return '/blog/' if number==1 else f'/blog/page/{number}/'
def journal_page_numbers(current,total):
 return sorted({1,total,*range(max(1,current-1),min(total,current+1)+1)}) if total>7 else list(range(1,total+1))
def journal_pagination(current,total):
 if total<=1:return ''
 parts=[]
 def link(number,label,extra=''):
  return f'<a href="{journal_page_url(number)}" data-journal-page="{number}"{extra}>{label}</a>'
 parts.append(link(current-1,'Previous') if current>1 else '<span aria-disabled="true">Previous</span>')
 previous=0
 for number in journal_page_numbers(current,total):
  if previous and number>previous+1:parts.append('<span class="pagination-gap" aria-hidden="true">…</span>')
  parts.append(link(number,str(number),' aria-current="page" aria-label="Page '+str(number)+'"' if number==current else ' aria-label="Page '+str(number)+'"'))
  previous=number
 parts.append(link(current+1,'Next') if current<total else '<span aria-disabled="true">Next</span>')
 return ''.join(parts)
years=sorted({p['date_iso'][:4] for p in M['posts']},reverse=True)
for current in range(1,journal_pages+1):
 start=(current-1)*JOURNAL_PAGE_SIZE;subset=M['posts'][start:start+JOURNAL_PAGE_SIZE]
 counter=f'Showing {start+1}–{start+len(subset)} of {len(M["posts"])} articles' if subset else '0 articles'
 body=intro(journal_archive.get('label') or '',journal_archive['heading'],journal_archive.get('lead') or '')
 body+=f'<section class="section journal-archive" id="journal-archive" data-page="{current}" data-total="{len(M["posts"])}" data-page-size="{JOURNAL_PAGE_SIZE}" data-index="/blog/archive-index.json?v={journal_version}" style="padding-top:0"><div class="wrap"><div class="filters journal-filters"><label for="post-search">Search the journal<input type="search" id="post-search" name="search" placeholder="Search articles…" aria-controls="post-results"></label>'+topic_select('post-category')+'<label for="post-year">Year<select id="post-year" aria-controls="post-results"><option value="">All years</option>'+''.join(f'<option value="{year}">{year}</option>' for year in years)+'</select></label></div>'
 body+=f'<p class="result-count" id="result-count" role="status" aria-live="polite" tabindex="-1">{counter}</p><div class="journal-grid" id="post-results">'+''.join(post_card(p,'h2') for p in subset)+'</div><p class="empty" id="no-results"'+(' hidden' if subset else '')+'>No articles found. Try another search, topic or year.</p><div class="journal-error" id="journal-error" role="alert" hidden><p>Could not update the archive. Previous results are still shown.</p><button type="button" class="textlink" id="journal-retry">Try again</button></div>'
 body+='<nav class="journal-pagination" id="journal-pagination" aria-label="Journal pages">'+journal_pagination(current,journal_pages)+'</nav><noscript><p>Use the numbered pages to browse all articles. Enable JavaScript to search or filter the archive.</p></noscript></div></section>'
 page('/blog' if current==1 else f'/blog/page/{current}','Journal' if current==1 else f'Journal — Page {current}',body)
for i,p in enumerate(M['posts']):
 body=f'<article class="article"><div class="wrap"><header class="article-head"><a class="textlink" data-journal-back href="/blog">← Back to journal</a><h1>{E(p["title"])}</h1><p class="article-meta">Radoje Laušević · {E(p["date"])}'+(' · '+E(p['topic']) if p.get('topic') else '')+'</p></header><div class="prose">'+render_all(p['blocks'])
 if p['cover'] and p['cover'] not in p.get('body',''):body+=image(p['cover'],p['title'])
 body+='<div class="article-nav">'
 if i>0:body+=f'<a href="{M["posts"][i-1]["path"]}">← Newer article</a>'
 if i+1<len(M['posts']):body+=f'<a href="{M["posts"][i+1]["path"]}">Older article →</a>'
 body+='</div></div></div></article>';page(p['path'],p['title'],body,p['excerpt'])
# Contact sends through the server endpoint; the email link remains available.
CONTACT_EMAIL=S['email']
body=intro('Contact','Let’s talk.','Have a project in mind, need guidance, or want to explore a collaboration? Get in touch.')+f'''<section class="section"><div class="wrap contact-grid"><div class="contact-info"><span class="eyebrow">Partner Consulting</span><h2>Start a conversation.</h2><p>{S['location']}</p><a href="mailto:{S['email']}">{S['email']}</a><br><a href="tel:{E(re.sub(r'[^+0-9]','',S['phone']))}">{S['phone']}</a><p><a class="textlink" href="{S['linkedin']}" target="_blank" rel="noopener noreferrer">Connect on LinkedIn ↗</a></p></div><form class="contact-form" id="contact-form" action="/api/contact" method="post" data-email="{E(CONTACT_EMAIL)}" aria-describedby="contact-status" aria-busy="false"><fieldset disabled><legend class="visually-hidden">Send a message</legend><label>Your name<input name="name" autocomplete="name" required maxlength="150"></label><label>Your email<input type="email" name="email" autocomplete="email" required maxlength="200"></label><label>Subject<input name="subject" required maxlength="200"></label><label>Message<textarea name="message" required maxlength="4000"></textarea></label><div class="contact-trap" aria-hidden="true"><label>Leave this field empty<input name="website" tabindex="-1" autocomplete="off"></label></div><div id="contact-security"></div><button class="button" type="submit" disabled>Send message</button></fieldset><p class="form-note" id="contact-status" role="status" aria-live="polite" tabindex="-1">Loading the secure contact form…</p><p class="form-note">You can also email <a href="mailto:{E(CONTACT_EMAIL)}">{E(CONTACT_EMAIL)}</a>.</p><noscript><p>Please enable JavaScript to use the form, or use the email link above.</p></noscript></form></div></section>''';page('/contact','Contact',body)
# Legal-neutral error page and infrastructure.
page('/404','Page not found',intro('404','This page could not be found.','Explore the main pages or return to the journal archive.')+'<section class="section"><div class="wrap"><a class="button" href="/">Return home →</a></div></section>')
(DIST/'404.html').write_text((DIST/'404/index.html').read_text());(DIST/'404/index.html').unlink();(DIST/'404').rmdir()
(DIST/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(S['domain']+p)+'</loc></url>' for p in written if p!='/404')+'</urlset>')
(DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+S['domain']+'/sitemap.xml\n')
(DIST/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n/assets/*\n  Cache-Control: public, max-age=86400\n/media/gallery/*\n  Cache-Control: public, max-age=31536000, immutable\n')
redirects=['/home / 301','/index.html / 301','/blog/hashtags/:tag /blog?search=:tag 301']
for source,target in project_redirects.items():
 redirects.extend([source+' '+target+' 301',source+'/ '+target+' 301'])
# Preserve old category URLs without retaining obsolete topic metadata.
redirects.append('/blog/categories/* /blog 301')
for original,localpath in json.loads((ROOT/'content/asset-map.json').read_text()).items():
 if '/_files/ugd/' in original:redirects.append(urllib.parse.urlsplit(original).path+' '+localpath+' 301')
(DIST/'_redirects').write_text('\n'.join(dict.fromkeys(redirects))+'\n')
(DIST/'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#193d3b"/><text x="32" y="44" text-anchor="middle" fill="#f7f6ef" font-family="Georgia,serif" font-size="32">RL</text></svg>')
print(f'Built {len(written)-1} pages, {len(M["posts"])} blog articles and custom 404.')

print(gallery_images.summary()+f' Build time: {time.perf_counter()-BUILD_STARTED:.2f}s.')
