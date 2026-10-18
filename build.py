#!/usr/bin/env python3
"""Build the portable static website. Python standard library only."""
from pathlib import Path
from html.parser import HTMLParser
import json,html,re,urllib.parse,datetime,hashlib,shutil
ROOT=Path(__file__).resolve().parent; DIST=ROOT/'dist'
from cms_data import load_cms
M=load_cms(ROOT,json.loads((ROOT/'content/site.json').read_text())); S=M['site']; written=[]
resume=json.loads((ROOT/'content/cms/resume.json').read_text())
brief_files=resume.get('brief_cv') or []
if isinstance(brief_files,str):brief_files=[brief_files]
brief_cv_url=next((url for url in brief_files if urllib.parse.urlsplit(url).path.lower().endswith('.pdf')),brief_files[0] if brief_files else '')
E=lambda s:html.escape(str(s),quote=True)
ASSET_VERSION={name:hashlib.sha256((DIST/'assets'/name).read_bytes()).hexdigest()[:12] for name in ['site.css','site.js']}
NAV=[('/about','About'),('/expertise','Expertise'),('/projects','Projects'),('/bibliography','Bibliography'),('/insights','Insights'),('/contact','Contact')]
def cv_download(cls='button'):
 return f'<a class="{E(cls)}" href="{E(brief_cv_url)}" download aria-label="Download CV — Europass Brief CV">Download CV</a>' if brief_cv_url else ''
CAT={'Offical Development Assistance':'Official Development Assistance','Sustainable Consumption and Product':'Sustainable Consumption & Production','Sustainable lifestiles':'Sustainable Lifestyles','Data vizualization':'Data Visualization'}
def image(src,alt='',cls='',eager=False):
 return f'<img src="{E(src)}" alt="{E(alt)}" class="{E(cls)}" loading="{"eager" if eager else "lazy"}" decoding="async">' if src else ''
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
   slug=value.split('/')[-1]
   category=next((CAT.get(c,c) for post in M['posts'] for c in post['categories'] if c.lower().replace(' ','-')==slug),'')
   return 'href="/blog?category='+E(urllib.parse.quote(category))+'"'
  return match.group(0)
 body=re.sub(r'href="([^"]+)"',fixlink,body)
 insights_paths=path in {'/insights','/blog','/video','/galleries'} or path.startswith(('/post/','/video/'))
 active='/insights' if insights_paths else '/projects' if path.startswith('/project/') else '/about' if path in {'/resume','/work-experience'} else path
 nav=''
 for url,label in NAV:
  current=(' aria-current="page"' if path==url else ' aria-current="true"') if active==url else ''
  if url=='/insights':
   sub=''.join(f'<a href="{href}"'+(' aria-current="page"' if path==href else ' aria-current="true"' if (href=='/blog' and path.startswith('/post/')) or (href=='/video' and path.startswith('/video/')) else '')+f'>{name}</a>' for href,name in [('/blog','Journal'),('/video','Video'),('/galleries','Galleries')])
   nav+=f'<div class="nav-insights"><div class="insights-controls"><a href="{url}"{current}>{label}</a><button class="insights-toggle" type="button" aria-label="Open Insights submenu" aria-expanded="false" aria-controls="insights-menu"><span aria-hidden="true">⌄</span></button></div><div class="insights-menu" id="insights-menu" hidden>{sub}</div></div>'
  else:nav+=f'<a href="{url}"{current}>{label}</a>'
 nav+=cv_download('button nav-download')
 schema={'@context':'https://schema.org','@type':'Person','name':S['name'],'url':S['domain'],'jobTitle':'Senior Environmental Consultant','email':S['email'],'sameAs':[S['linkedin'],S['twitter']]}
 if path.startswith('/post/'):
  post=next(p for p in M['posts'] if p['path']==path);schema={'@context':'https://schema.org','@type':'BlogPosting','headline':post['title'],'author':{'@type':'Person','name':S['name']},'mainEntityOfPage':S['domain']+path}
  try:schema['datePublished']=datetime.datetime.strptime(post['date'],'%b %d, %Y').date().isoformat()
  except ValueError:pass
 resume_styles='<style>.resume-education p,.resume-education li{line-height:1.4}.resume-education p{margin:0 0 6px}.resume-education h3{font-size:22px;line-height:1.3;margin:18px 0 6px}.resume-education h3:first-child{margin-top:0}</style>' if path=='/resume' else ''
 fulltitle=title+' | '+S['name'] if path!='/' else S['name']+' — Senior Environmental Consultant'
 data=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(fulltitle)}</title><meta name="description" content="{E(desc or S['description'])}"><meta name="theme-color" content="#193d3b"><link rel="canonical" href="{E(S['domain']+path)}"><meta property="og:type" content="{'article' if path.startswith('/post/') else 'website'}"><meta property="og:title" content="{E(fulltitle)}"><meta property="og:description" content="{E(desc or S['description'])}"><meta property="og:url" content="{E(S['domain']+path)}"><meta property="og:image" content="{E(S['domain']+S['portrait'])}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v={ASSET_VERSION['site.css']}">{resume_styles}<script src="/assets/site.js?v={ASSET_VERSION['site.js']}" defer></script><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script></head><body class="{'page-home' if path=='/' else 'page-inner page-about' if path=='/about' else 'page-inner'}"><a class="skip" href="#main">Skip to content</a><div class="topline"><div class="wrap"><span>ENVIRONMENT · PEOPLE · SUSTAINABILITY</span><a href="mailto:{S['email']}">{S['email']} &nbsp; ↗</a></div></div><header class="site-header"><div class="wrap header-row"><a class="brand" href="/" aria-label="Radoje Laušević home"><strong>{E(S['name'])}<span style="color:var(--accent);font-size:inherit;letter-spacing:0;display:inline">.</span></strong><span>{E(S['brand'])}</span></a><button class="menu-toggle" type="button" aria-controls="primary-nav" aria-expanded="false">Menu ☰</button><nav id="primary-nav" aria-label="Main navigation">{nav}</nav></div></header><main id="main">{body}</main><section class="cta"><div class="wrap"><div><h2>Let’s make progress together.</h2><p>Explore a project, exchange ideas, or discuss your next challenge.</p></div><a class="button" href="/contact">Get in touch <span aria-hidden="true">↗</span></a></div></section><footer class="footer"><div class="wrap"><div class="footer-top"><div><strong>{S['name']}</strong><p>Senior Environmental Consultant<br>Partner Consulting · {S['location']}</p></div><div class="footer-links"><a href="/galleries">Galleries</a>{cv_download("footer-download")}<a href="/work-experience">Career history</a><a href="/resume">CV &amp; documents</a><a href="{S['linkedin']}" target="_blank" rel="noopener noreferrer">LinkedIn ↗</a><a href="{S['twitter']}" target="_blank" rel="noopener noreferrer">X / Twitter ↗</a><a href="mailto:{S['email']}">Email ↗</a></div></div><div class="footer-bottom"><span>© {datetime.date.today().year} Radoje Laušević. All rights reserved.</span><span>Leadership · Project management · Environmental research</span></div></div></footer></body></html>'''
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
def post_card(p,heading='h3'):
 cats='|'.join(CAT.get(c,c) for c in p['categories'])
 return f'<a class="post-card" data-post data-categories="{E(cats)}" data-search="{E((p["title"]+" "+p["excerpt"]+" "+cats+" "+" ".join(b.get("text","") for b in p["blocks"])).lower())}" href="{p["path"]}"><div class="image-wrap">{image(p["cover"] or S["landscape"],p["title"])}</div><span class="date">{E(p["date"])} · JOURNAL</span><{heading}>{E(p["title"])}</{heading}><p>{E(p["excerpt"])}</p><span class="read">Read article &nbsp; ↗</span></a>'
# A shared ordered source powers About and the home previews.
expertise_page=M['expertise']
expertise=expertise_page.get('services') or []
recommendations=M['about'].get('recommendations') or []
video_archive=json.loads((ROOT/'content/cms/videos.json').read_text())
videos=[];video_paths=set()
for item in video_archive.get('items') or []:
 video=dict(item);link=video.get('link','').strip();parsed=urllib.parse.urlsplit(link)
 if parsed.scheme!='https' or not parsed.hostname or any(c.isspace() for c in link):raise ValueError('Invalid video link: '+link)
 video['link']=link
 path='/video/'+hashlib.sha256(link.encode()).hexdigest()[:16]
 if path in video_paths:raise ValueError('Duplicate video link: '+link)
 video_paths.add(path);video['path']=path
 video['date_iso']=datetime.date.fromisoformat(video['date'][:10]).isoformat()
 video['date_display']=datetime.date.fromisoformat(video['date_iso']).strftime('%b %d, %Y')
 video['content']=__import__('cms_data').body(video.get('body') or '')
 video['excerpt']=video.get('excerpt') or ''
 video['cover']=video.get('cover') or S['landscape']
 videos.append(video)
# Rebuild detail routes so removed videos do not leave stale pages behind.
if (DIST/'video').exists():shutil.rmtree(DIST/'video')
def video_card(video,heading='h3'):
 search=' '.join([video['title'],video['date_display'],video['date_iso'],video['excerpt'],video['content']['text']]).lower()
 return f'<article class="post-card video-card" data-video data-search="{E(search)}"><div class="video-detail-link"><div class="image-wrap">{image(video["cover"],video["title"])}</div><span class="date"><time datetime="{E(video["date_iso"])}">{E(video["date_display"])}</time> · VIDEO</span><{heading}>{E(video["title"])}</{heading}><p>{E(video["excerpt"])}</p></div><div class="video-actions"><a class="textlink" href="{E(video["path"])}">Read more →</a><a class="textlink" href="{E(video["link"])}" target="_blank" rel="noopener noreferrer">Watch video ↗</a></div></article>'
projects=sections('/projects')
project_entries=M['project_entries']
expertise_topics=list(dict.fromkeys([item['title'] for item in expertise]+[item['topic'] for item in project_entries if item.get('topic')]))
def project_path(project):
 return '/project/'+hashlib.sha256(project['title'].encode()).hexdigest()[:16]

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
 home+=f'<a class="project-card" href="{E(project_path(project_entries[i]))}"><div class="image-wrap">{image(p["image"]["src"],p["title"])}</div><span class="eyebrow">{E(p["blocks"][0]["text"])}</span><h3>{title}</h3><p>{E(desc[:180])}…</p></a>'
home+='</div></div></section>'
# The first two full recommendations in About provide the home excerpts.
home+=f'<section class="section testimonials"><div class="wrap"><div class="section-head"><div><span class="eyebrow">{E(M["home"].get("recommendations_label", "Recommendations"))}</span><h2>{E(M["home"].get("recommendations_heading", "Trusted by colleagues."))}</h2></div><a class="textlink" href="/about#recommendations">View all recommendations →</a></div><div class="quotes">'
for recommendation in recommendations[:2]:
 home+=f'<blockquote><div class="quote-mark">“</div><p>{E(recommendation["summary"])}</p><cite>{E(recommendation["author"])}</cite></blockquote>'
home+='</div></div></section>'
home+='<section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">The journal</span><h2>Notes from the field.</h2></div><a class="textlink" href="/blog">Explore the archive →</a></div><div class="journal-grid">'+''.join(post_card(p) for p in M['posts'][:3])+'</div></div></section>'
# The home video preview uses the same ordered archive as /video.
home+=f'<section class="section" style="padding-top:0"><div class="wrap"><div class="section-head"><div><span class="eyebrow">{E(M["home"].get("videos_label", "Video resources"))}</span><h2>{E(M["home"].get("videos_heading", "Conversations on sustainability."))}</h2></div><a class="textlink" href="/video">View all videos →</a></div><div class="journal-grid">'+''.join(video_card(video) for video in videos[:3])+'</div></div></section>';page('/','Home',home)
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
 body+=f'<details class="expertise-card" id="expertise-{i+1}"><summary><h2>{E(item["title"])}</h2><span class="textlink expertise-expand">View details →</span><span class="textlink expertise-collapse">Hide details ↑</span></summary><div class="prose expertise-content"><p class="motto">{E(item.get("motto") or "")}</p><p>{E(item.get("summary") or "")}</p>'
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
gallery_source=json.loads((ROOT/'content/cms/gallery.json').read_text())
# The existing gallery is one album, with photos stored in items, not separate albums.
if gallery_source.get('items'):
 cover=gallery_source['items'][0]
 body+='<section class="section"><div class="wrap"><div class="section-head"><h2>Galleries</h2><a class="textlink" href="/galleries">View all galleries →</a></div><div class="journal-grid"><a class="post-card" href="/galleries"><div class="image-wrap">'+image(cover.get('image') or S['landscape'],gallery_source.get('title') or cover.get('title',''))+'</div><span class="date">'+E(gallery_source.get('date') or '')+'</span><h3>'+E(gallery_source.get('title') or 'My favourite places')+'</h3><p>'+E(gallery_source.get('summary') or '')+'</p><span class="read">View gallery →</span></a></div></div></section>'
page('/insights','Insights',body)
# Video archive shares Journal typography, card layout and search behavior.
body=intro(video_archive.get('label','Video archive'),video_archive.get('heading','Conversation on sustainability'),video_archive.get('lead','Project updates, environmental insights and personal observations'))+'<section class="section" style="padding-top:0"><div class="wrap"><div class="filters"><label for="video-search">Search video archive<input type="search" id="video-search" placeholder="Search video archive…" aria-controls="video-results"></label></div>'
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
 if path in project_paths:raise ValueError('Duplicate project title: '+project['title'])
 project_paths.add(path)
 detail=__import__('cms_data').body(project.get('body') or '')
 topic=project.get('topic') or ''
 search=' '.join([project['title'],project['period'],project.get('summary') or '',topic,detail['text']]).lower()
 body+=f'<article class="post-card project-archive-card" id="project-{i+1}" data-project data-categories="{E(topic)}" data-search="{E(search)}"><div class="image-wrap">{image(project.get("image") or S["landscape"],project.get("image_alt") or project["title"])}</div><span class="date">{E(project["period"])}</span><h2>{E(project["title"])}</h2><p>{E(project.get("summary") or "")}</p><div class="project-actions"><a class="textlink" href="{E(path)}">View all details →</a></div></article>'
body+='</div><p class="empty" id="no-projects" hidden>No projects found. Try another search or select all topics.</p></div></section>';page('/projects','Projects',body)
for project in project_entries:
 body=f'<article class="article"><div class="wrap"><header class="article-head"><a class="textlink" href="/projects">← Back to projects</a><h1>{E(project["title"])}</h1><p class="article-meta">{E(project["period"])}</p></header><div class="prose">'+image(project.get('image') or S['landscape'],project.get('image_alt') or project['title'])+render(__import__('cms_data').body(project.get('body') or ''))+'</div></div></article>'
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
# Bibliography: fixed category groups, with entries in their CMS list order.
bibliography=json.loads((ROOT/'content/cms/bibliography.json').read_text())
bibliography_categories=['Publications','Articles','Conferences','Invited lectures']
bibliography_items=bibliography.get('items') or []
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
  body+=f'<li class="bibliography-item" data-bibliography data-categories="{E(category)}" data-search="{E(searchable.lower())}"><span class="bibliography-citation">{bibliography_citation(item)}</span>'
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
# Gallery.
gb=M['pages']['/galleries']['blocks'];body=intro('Connecting with nature','My favourite places.','Flowers of my Mediterranean garden in Montenegro — a personal connection with nature.')+'<section class="section"><div class="wrap"><div class="gallery-grid">';seen=set()
for i,b in enumerate(gb):
 if b['type']!='image' or b['src']==S['landscape'] or b['src'] in seen:continue
 seen.add(b['src']);caption=gb[i+1].get('text',b['alt']);label=b['alt']
 body+=f'<button class="gallery-button" type="button" data-gallery data-src="{E(b["src"])}" data-caption="{E(caption)}" aria-label="Enlarge {E(label)}">{image(b["src"],caption)}<span>{label} ↗</span></button>'
body+='</div><div class="prose" style="margin-top:50px">'
idx=next(i for i,b in enumerate(gb) if b.get('text')=='Flowers of My Mediterranean Garden');body+=render_all(gb[idx+1:])+'</div></div></section><dialog class="gallery-dialog" id="gallery-dialog"><button type="button" autofocus>Close ×</button><img alt=""><p></p></dialog>';page('/galleries','Galleries',body)
# Blog searchable archive.
cats=sorted(set(CAT.get(c,c) for p in M['posts'] for c in p['categories']));body=intro('Journal archive','Notes, ideas & field stories.','Project updates, environmental insights and personal observations from the original journal.')+f'<section class="section" style="padding-top:0"><div class="wrap"><div class="filters"><label>Search the journal<input type="search" id="post-search" placeholder="Search articles…"></label><label>Topic<select id="post-category"><option value="">All topics</option>'+''.join(f'<option value="{E(c)}">{E(c)}</option>' for c in cats)+f'</select></label></div><p class="result-count" id="result-count" role="status">{len(M["posts"])} articles</p><div class="journal-grid">'+''.join(post_card(p,'h2') for p in M['posts'])+'</div><p class="empty" id="no-results" hidden>No articles found. Try another search or select all topics.</p></div></section>';page('/blog','Journal',body)
for i,p in enumerate(M['posts']):
 body=f'<article class="article"><div class="wrap"><header class="article-head"><a class="textlink" href="/blog">← Back to journal</a><h1>{E(p["title"])}</h1><p class="article-meta">Radoje Laušević · {E(p["date"])}'+(' · '+E(', '.join(CAT.get(c,c) for c in p['categories'])) if p['categories'] else '')+'</p></header><div class="prose">'+render_all(p['blocks'])
 if p['cover'] and p['cover'] not in p.get('body',''):body+=image(p['cover'],p['title'])
 body+='<div class="article-nav">'
 if i>0:body+=f'<a href="{M["posts"][i-1]["path"]}">← Newer article</a>'
 if i+1<len(M['posts']):body+=f'<a href="{M["posts"][i+1]["path"]}">Older article →</a>'
 body+='</div></div></div></article>';page(p['path'],p['title'],body,p['excerpt'])
# Contact uses the visitor's email application; no simulated submissions.
body=intro('Contact','Let’s talk.','Have a project in mind, need guidance, or want to explore a collaboration? Get in touch.')+f'''<section class="section"><div class="wrap contact-grid"><div class="contact-info"><span class="eyebrow">Partner Consulting</span><h2>Start a conversation.</h2><p>{S['location']}</p><a href="mailto:{S['email']}">{S['email']}</a><br><a href="tel:{E(re.sub(r'[^+0-9]','',S['phone']))}">{S['phone']}</a><p><a class="textlink" href="{S['linkedin']}" target="_blank" rel="noopener noreferrer">Connect on LinkedIn ↗</a></p></div><form class="contact-form" id="contact-form" data-email="{E(S['email'])}"><label>Your name<input name="name" autocomplete="name" required maxlength="150"></label><label>Your email<input type="email" name="email" autocomplete="email" required maxlength="200"></label><label>Subject<input name="subject" required maxlength="200"></label><label>Message<textarea name="message" required maxlength="4000"></textarea></label><button class="button" type="submit">Prepare email ↗</button><p class="form-note" id="contact-status" role="status">This opens your email application with a prepared message. Send it there to complete your inquiry. You can also use the email link above.</p></form></div></section>''';page('/contact','Contact',body)
# Legal-neutral error page and infrastructure.
page('/404','Page not found',intro('404','This page could not be found.','Explore the main pages or return to the journal archive.')+'<section class="section"><div class="wrap"><a class="button" href="/">Return home →</a></div></section>')
(DIST/'404.html').write_text((DIST/'404/index.html').read_text());(DIST/'404/index.html').unlink();(DIST/'404').rmdir()
(DIST/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(S['domain']+p)+'</loc></url>' for p in written if p!='/404')+'</urlset>')
(DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+S['domain']+'/sitemap.xml\n')
(DIST/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n/assets/*\n  Cache-Control: public, max-age=86400\n')
redirects=['/home / 301','/index.html / 301','/blog/hashtags/:tag /blog?search=:tag 301']
for c in M['posts']:
 for cat in c['categories']:
  slug=cat.lower().replace(' ','-');redirects.append('/blog/categories/'+slug+' /blog?category='+urllib.parse.quote(CAT.get(cat,cat))+' 301')
for original,localpath in json.loads((ROOT/'content/asset-map.json').read_text()).items():
 if '/_files/ugd/' in original:redirects.append(urllib.parse.urlsplit(original).path+' '+localpath+' 301')
(DIST/'_redirects').write_text('\n'.join(dict.fromkeys(redirects))+'\n')
(DIST/'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#193d3b"/><text x="32" y="44" text-anchor="middle" fill="#f7f6ef" font-family="Georgia,serif" font-size="32">RL</text></svg>')
print(f'Built {len(written)-1} pages, {len(M["posts"])} blog articles and custom 404.')
