#!/usr/bin/env python3
"""Build the portable static website. Python standard library only."""
from pathlib import Path
import json,html,re,urllib.parse,datetime,hashlib,shutil
ROOT=Path(__file__).resolve().parent; DIST=ROOT/'dist'
from cms_data import load_cms
M=load_cms(ROOT,json.loads((ROOT/'content/site.json').read_text())); S=M['site']; written=[]
E=lambda s:html.escape(str(s),quote=True)
NAV=[('/', 'Home'),('/about','About'),('/work-experience','Experience'),('/projects','Projects'),('/resume','Resume'),('/blog','Journal'),('/video','Video')]
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

def page(path,title,body,desc=None):
 def fixlink(match):
  value=html.unescape(match.group(1))
  if value.startswith('/blog/hashtags/'):
   return 'href="/blog?search='+E(urllib.parse.quote(urllib.parse.unquote(value.split('/')[-1])))+'"'
  if value.startswith('/blog/categories/'):
   slug=value.split('/')[-1]
   category=next((CAT.get(c,c) for post in M['posts'] for c in post['categories'] if c.lower().replace(' ','-')==slug),'')
   return 'href="/blog?category='+E(urllib.parse.quote(category))+'"'
  return match.group(0)
 body=re.sub(r'href="([^"]+)"',fixlink,body)
 active='/blog' if path.startswith('/post/') else '/video' if path.startswith('/video/') else path
 nav=''.join(f'<a href="{u}"'+(' aria-current="page"' if active==u else '')+f'>{t}</a>' for u,t in NAV)
 schema={'@context':'https://schema.org','@type':'Person','name':S['name'],'url':S['domain'],'jobTitle':'Senior Environmental Consultant','email':S['email'],'sameAs':[S['linkedin'],S['twitter']]}
 if path.startswith('/post/'):
  post=next(p for p in M['posts'] if p['path']==path);schema={'@context':'https://schema.org','@type':'BlogPosting','headline':post['title'],'author':{'@type':'Person','name':S['name']},'mainEntityOfPage':S['domain']+path}
  try:schema['datePublished']=datetime.datetime.strptime(post['date'],'%b %d, %Y').date().isoformat()
  except ValueError:pass
 fulltitle=title+' | '+S['name'] if path!='/' else S['name']+' — Senior Environmental Consultant'
 data=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(fulltitle)}</title><meta name="description" content="{E(desc or S['description'])}"><meta name="theme-color" content="#193d3b"><link rel="canonical" href="{E(S['domain']+path)}"><meta property="og:type" content="{'article' if path.startswith('/post/') else 'website'}"><meta property="og:title" content="{E(fulltitle)}"><meta property="og:description" content="{E(desc or S['description'])}"><meta property="og:url" content="{E(S['domain']+path)}"><meta property="og:image" content="{E(S['domain']+S['portrait'])}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css"><script src="/assets/site.js" defer></script><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script></head><body><a class="skip" href="#main">Skip to content</a><div class="topline"><div class="wrap"><span>ENVIRONMENT · PEOPLE · SUSTAINABILITY</span><a href="mailto:{S['email']}">{S['email']} &nbsp; ↗</a></div></div><header class="site-header"><div class="wrap header-row"><a class="brand" href="/" aria-label="Radoje Laušević home"><strong>{E(S['name'])}<span style="color:var(--accent);font-size:inherit;letter-spacing:0;display:inline">.</span></strong><span>{E(S['brand'])}</span></a><button class="menu-toggle" type="button" aria-controls="primary-nav" aria-expanded="false">Menu ☰</button><nav id="primary-nav" aria-label="Main navigation">{nav}<a class="nav-contact" href="/contact">Let's talk ↗</a></nav></div></header><main id="main">{body}</main><section class="cta"><div class="wrap"><div><h2>Let’s make progress together.</h2><p>Explore a project, exchange ideas, or discuss your next challenge.</p></div><a class="button" href="/contact">Get in touch <span aria-hidden="true">↗</span></a></div></section><footer class="footer"><div class="wrap"><div class="footer-top"><div><strong>{S['name']}</strong><p>Senior Environmental Consultant<br>Partner Consulting · {S['location']}</p></div><div class="footer-links"><a href="/galleries">Galleries</a><a href="/resume">Download CV</a><a href="{S['linkedin']}" target="_blank" rel="noopener noreferrer">LinkedIn ↗</a><a href="{S['twitter']}" target="_blank" rel="noopener noreferrer">X / Twitter ↗</a><a href="mailto:{S['email']}">Email ↗</a></div></div><div class="footer-bottom"><span>© {datetime.date.today().year} Radoje Laušević. All rights reserved.</span><span>Leadership · Project management · Environmental research</span></div></div></footer></body></html>'''
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
expertise=M['about'].get('services') or []
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
 youtube_id=parsed.path.strip('/') if parsed.hostname in {'youtu.be','www.youtu.be'} else urllib.parse.parse_qs(parsed.query).get('v',[''])[0] if parsed.hostname in {'youtube.com','www.youtube.com','m.youtube.com'} else ''
 thumbnail='https://i.ytimg.com/vi/'+youtube_id+'/hqdefault.jpg' if re.fullmatch(r'[A-Za-z0-9_-]{11}',youtube_id) else S['landscape']
 video['cover']=video.get('cover') or thumbnail
 videos.append(video)
# Rebuild detail routes so removed videos do not leave stale pages behind.
if (DIST/'video').exists():shutil.rmtree(DIST/'video')
def video_card(video,heading='h3'):
 search=' '.join([video['title'],video['date_display'],video['date_iso'],video['excerpt'],video['content']['text']]).lower()
 return f'<article class="post-card video-card" data-video data-search="{E(search)}"><a class="video-detail-link" href="{E(video["path"])}"><div class="image-wrap">{image(video["cover"],video["title"])}</div><span class="date"><time datetime="{E(video["date_iso"])}">{E(video["date_display"])}</time> · VIDEO</span><{heading}>{E(video["title"])}</{heading}><p>{E(video["excerpt"])}</p></a><div class="video-actions"><a class="textlink" href="{E(video["path"])}">Read more →</a><a class="textlink" href="{E(video["link"])}" target="_blank" rel="noopener noreferrer">Watch video ↗</a></div></article>'
projects=sections('/projects')
# Home: compact editorial introduction; detailed source content on inner pages.
home=f'''<div class="wrap"><section class="hero"><div><span class="eyebrow">Senior Environmental Consultant</span><h1>{E(M["home"]["heading"])}</h1><p class="lead">{E(M["home"]["lead"])}</p><div class="actions"><a class="button" href="/projects">Explore my work <span aria-hidden="true">↗</span></a><a class="textlink" href="/about">Meet Radoje →</a></div><p class="hero-foot">Biologist · Project manager · Environmental leader</p></div><div class="hero-art"><div class="accent-block"></div>{image(S['portrait'],S['name']+' — environmental consultant','portrait',True)}<div class="photo-note"><span>PhD</span><span>IN BIOLOGY<br>UNIVERSITY OF BELGRADE</span></div></div></section></div><div class="stat-strip"><div class="wrap stats"><div class="stat"><strong>100+</strong><span>Projects managed<br>or supervised</span></div><div class="stat"><strong>€50m+</strong><span>Total project<br>portfolio</span></div><div class="stat"><strong>3</strong><span>Connected fields<br>of consultancy</span></div></div></div>'''
home+='<section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">How I can help</span><h2>Experience that moves<br>ideas into action.</h2></div><a class="textlink" href="/about#my-services">View all expertise →</a></div><div class="services">'
for i,item in enumerate(expertise[:3]):
 home+=f'<article class="service"><span class="num">0{i+1} / EXPERTISE</span><h3>{E(item["title"])}</h3><p class="motto">{E(item.get("motto") or "")}</p><p>{E(item.get("summary") or "")}</p><a class="textlink" href="/about#expertise-{i+1}">Learn more →</a></article>'
home+='</div></div></section>'
home+=f'<div class="landscape">{image(S["landscape"],"Aerial view of islands from the original website")}<div class="caption">{E(M["home"]["landscape_quote"])}<small>Connecting with nature</small></div></div>'
home+='<section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Selected work</span><h2>From research to impact.</h2></div><a class="textlink" href="/projects">View all projects →</a></div><div class="project-grid">'
for i,p in enumerate(projects[:2]):
 desc=M['project_summaries'].get(p['title'],'')
 title=p['title']
 home+=f'<a class="project-card" href="/projects#project-{i+1}"><div class="image-wrap">{image(p["image"]["src"],p["title"])}</div><span class="eyebrow">{E(p["blocks"][0]["text"])}</span><h3>{title}</h3><p>{E(desc[:180])}…</p></a>'
home+='</div></div></section>'
# The first two full recommendations in About provide the home excerpts.
home+=f'<section class="section testimonials"><div class="wrap"><div class="section-head"><div><span class="eyebrow">{E(M["home"].get("recommendations_label", "Recommendations"))}</span><h2>{E(M["home"].get("recommendations_heading", "Trusted by colleagues."))}</h2></div><a class="textlink" href="/about#recommendations">View all recommendations →</a></div><div class="quotes">'
for recommendation in recommendations[:2]:
 home+=f'<blockquote><div class="quote-mark">“</div><p>{E(recommendation["summary"])}</p><cite>{E(recommendation["author"])}</cite></blockquote>'
home+='</div></div></section>'
home+='<section class="section"><div class="wrap"><div class="section-head"><div><span class="eyebrow">The journal</span><h2>Notes from the field.</h2></div><a class="textlink" href="/blog">Explore the archive →</a></div><div class="journal-grid">'+''.join(post_card(p) for p in M['posts'][:3])+'</div></div></section>'
# The home video preview uses the same ordered archive as /video.
home+=f'<section class="section" style="padding-top:0"><div class="wrap"><div class="section-head"><div><span class="eyebrow">{E(M["home"].get("videos_label", "Video resources"))}</span><h2>{E(M["home"].get("videos_heading", "Conversations on sustainability."))}</h2></div><a class="textlink" href="/video">View all videos →</a></div><div class="journal-grid">'+''.join(video_card(video) for video in videos[:3])+'</div></div></section>';page('/','Home',home)
# About, complete recommendations and service descriptions.
bs=M['pages']['/about']['blocks'];body=intro('About','Experience, with purpose.','A biologist’s perspective. An environmental leader’s experience. A practical approach to sustainability.')
body+=f'<section class="section"><div class="wrap two-col"><aside class="side-note">{image(S["portrait"],S["name"])}<p>PhD in Biology<br>University of Belgrade</p><a class="textlink" href="/resume">Explore my CV →</a></aside><div class="prose">'+render_all(b for b in bs if b['type'] in ['p','html'] and b['text']!='Here to Serve You')+'<h2 id="my-services">My services</h2>'
for i,item in enumerate(expertise):
 body+=f'<article class="expertise-detail" id="expertise-{i+1}"><h3>{E(item["title"])}</h3><p class="motto">{E(item.get("motto") or "")}</p>'+render(__import__('cms_data').body(item.get('description') or ''))+'</article>'
body+='</div></div></section><section class="section testimonials" id="recommendations"><div class="wrap prose"><span class="eyebrow">Professional recommendations</span><h2>What colleagues say</h2>'
for item in recommendations:
 body+='<blockquote class="recommendation-detail">'+render(__import__('cms_data').body(item.get('body') or ''))+f'<cite>{E(item["author"])}</cite></blockquote>'
body+='</div></section>';page('/about','About',body)
# Video archive shares Journal typography, card layout and search behavior.
body=intro(video_archive.get('label','Video archive'),video_archive.get('heading','Conversation on sustainability'),video_archive.get('lead','Project updates, environmental insights and personal observations'))+'<section class="section" style="padding-top:0"><div class="wrap"><div class="filters"><label for="video-search">Search video archive<input type="search" id="video-search" placeholder="Search video archive…" aria-controls="video-results"></label></div>'
body+=f'<p class="result-count" id="video-result-count" role="status" aria-live="polite">{len(videos)} {"video" if len(videos)==1 else "videos"}</p><div class="journal-grid" id="video-results">'+''.join(video_card(video,'h2') for video in videos)+'</div><p class="empty" id="no-videos"'+(' hidden' if videos else '')+'>No videos found. Try another search.</p></div></section>'
page('/video','Video',body,video_archive.get('lead'))
for video in videos:
 body=f'<article class="article"><div class="wrap"><header class="article-head"><a class="textlink" href="/video">← Back to video archive</a><h1>{E(video["title"])}</h1><p class="article-meta"><time datetime="{E(video["date_iso"])}">{E(video["date_display"])}</time> · VIDEO</p></header><div class="prose">'
 body+=image(video['cover'],video['title'])+f'<p class="lead">{E(video["excerpt"])}</p>'+render(video['content'])+f'<p><a class="button" href="{E(video["link"])}" target="_blank" rel="noopener noreferrer">Watch video ↗</a></p>'
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
# All projects.
body=intro('Selected portfolio','Projects.','A selection from more than 100 projects managed or supervised, with a total portfolio exceeding €50 million.')+'<section class="section"><div class="wrap">'
for i,p in enumerate(projects):
 body+=f'<article class="project-detail" id="project-{i+1}"><div>{image(p["image"]["src"],p["title"])}</div><div><h2>{E(p["title"])}</h2><p class="date">{E(p["blocks"][0]["text"])}</p>'+render_all(p['blocks'][1:])+'</div></article>'
body+='</div></section>';page('/projects','Projects',body)
# Resume files and publication attachments managed through Pages CMS.
resume=json.loads((ROOT/'content/cms/resume.json').read_text())
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
def document_downloads(value,label='Download'):
 links=[]
 for value in document_files(value):
  url=document_link(value)
  extension=Path(urllib.parse.urlsplit(url).path).suffix.lstrip('.').upper() or 'FILE'
  filename=urllib.parse.unquote(Path(urllib.parse.urlsplit(url).path).name)
  links.append(f'<p><a class="textlink" href="{E(url)}" download>{E(label)} {E(extension)} ↓</a> <small>{E(filename)}</small></p>')
 return ''.join(links)
def download_card(title,description,value):
 links=document_downloads(value)
 if not links:return ''
 return f'<article class="download"><span>Documents</span><h2>{E(title)}</h2><p>{E(description)}</p>{links}</article>'
body=intro(resume.get('label','Qualifications & publications'),resume.get('heading','Resume.'),resume.get('lead','Explore my academic background, download a CV and read selected publications.'))+'<section class="section"><div class="wrap"><div class="download-grid">'
for key,title,description in [('brief_cv','Brief CV','Concise overview of work experience and skills.'),('europass_cv','Europass CV','Detailed experience, education, skills, projects and publications.'),('assortis_cv','Assortis CV','Professional experience and project record in Assortis format.')]:
 body+=download_card(resume.get(key+'_title',title),resume.get(key+'_description',description),resume.get(key))
body+=download_card(resume.get('bibliography_title','Complete bibliography'),'',resume.get('bibliography_file'))
body+='</div><div class="prose"><h2>Education</h2>'+render(__import__('cms_data').body(resume.get('education','')))+'<h2>Selected Publications</h2>'
if 'publication_items' in resume:
 for publication in resume['publication_items']:
  body+='<article><h3>'+E(publication['title'])+'</h3>'+render(__import__('cms_data').body(publication.get('description','')))
  body+=document_downloads(publication.get('file'),'Download publication')
  body+='</article>'
body+=render(__import__('cms_data').body(resume.get('publications','')))
body+='</div></div></section>';page('/resume','Resume',body)
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
