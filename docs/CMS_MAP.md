# CMS mapa — forme, izvori i prikaz

Provereno prema `.pages.yml` i generatoru na commitu `ba06d42ccdf026b90317a5f7d107db27f44d7863`, 03.11.2026. Koristiti samo odeljak relevantan za zadatak. Pravila su u [AGENTS.md](../AGENTS.md), operativni sažetak u [PROJECT_HANDOFF.md](../PROJECT_HANDOFF.md).

## 1. Gde se šta uređuje

Sve putanje u tabeli su relativne prema `content/cms/`. `file` je jedna CMS forma; `collection` ima zaseban JSON fajl po unosu.

| CMS forma / tehničko ime | Izvor | Javni prikaz i zavisnosti |
|---|---|---|
| Podešavanja sajta / `settings` | `settings.json` | Ime, kontakt, domen, društvene mreže, portret, panorama. `archive_pages` uređuje naslove i uvode Bibliography, Galleries i Video. |
| Početna strana / `home` | `home.json` | Glavni naslov, uvod, panorama i oznake preporuka na `/`. Neke starije oznake video/galerijskih blokova ostaju u formi, ali zajednički Insights blok ima naslov u generatoru. |
| Biografija / `about` | `about.json` | Profile, izbor Career highlights, uvod za Expertise i preporuke na `/about`; dve preporuke na Home. `network_note` je uputstvo, ne izvor Network zapisa. |
| Expertise — oblasti usluga / `expertise` | `expertise.json` | `services` je jedini izvor oblasti za `/expertise`, prve tri na Home i Topic izbore u drugim formama. |
| Radno iskustvo / `experience` | `experience.json` → `items` | `/work-experience` i izabrane kartice Career highlights na About. |
| Saradnici i organizacije / `network` | `network.json` | `body` = Opis; `items` = saradnici; `document` = PDF liste. Primarni strukturirani prikaz na About; osnovni tekst i PDF koriste se i na Career history. |
| Saradnici — automatski izbor / `network_references` | `network_references/*.json` | Izveden indeks `id` + `name`, samo za čitanje i reference preporuka. Ne uređivati kao drugi izvor saradnika. |
| Projekti / `projects` | `projects.json` → `items` | `/projects`, `/project/...`, dva Selected work projekta na Home i veze iz Expertise. |
| CV i publikacije / `resume` | `resume.json` | `/resume`, Education i dokumenti; `brief_cv` napaja sva zajednička Download CV dugmad. Selected Bibliography dolazi iz bibliografskih unosa. |
| Bibliography / `bibliography_entries` | `bibliography_entries/*.json` | `/bibliography`, izabrane jedinice na Resume i projektne reference. |
| Journal / `journal` | `journal.json` | Samo nadnaslov, naslov i uvod arhive `/blog`. |
| Blog objave / `posts` | `posts/*.json` | Journal kartice, `/post/...`, Home, Insights i projektne reference. |
| Video / `video_entries` | `video_entries/*.json` | `/video`, `/video/<hash>`, Home, Insights i projektne reference. |
| Galerije / `gallery_entries` | `gallery_entries/*.json` | `/galleries`, `/gallery/...`, Home, Insights i projektne reference. |

Insights nema posebnu ručnu listu. Contact nema posebnu CMS kolekciju: javni kontaktni podaci dolaze iz settings, a forma iz generatora i serverskih modula.

`bibliography.json`, `gallery.json` i `videos.json` zadržavaju metapodatke i kompatibilni `entry_order`. Unosi su u kolekcijama, a aktuelni naslovi arhiva u `settings.archive_pages` imaju prednost. `entry_order` može odrediti redosled izjednačenih stavki; ne nadjačava sortiranje po datumu/godini. `content/site.json` i stare fascikle pojedinačnih projekata nisu primarni editori kada postoje aktuelni CMS izvori.

## 2. Sortiranje, izbor i paginacija

| Prikaz | Redosled / kriterijum | Obim i filteri |
|---|---|---|
| Projects | `assignment_ongoing=true` prvo; za njih `assignment_start` opadajuće, za završene `assignment_end` opadajuće. Jednaki datumi zadržavaju redosled izvora. | 12 po stranici; tekst, Topic, Year. Year je godina početka za tekuće, završetka za završene angažmane. |
| Journal | `date` opadajuće, zatim naslov opadajuće kod istog datuma. `published=false` isključuje objavu. | 12; naslov, excerpt, tekst i oblast; Topic i Year. Stare Teme nisu izvor filtera. |
| Video | `date` opadajuće; stabilne izjednačene vrednosti. | 12; naslov, datum, excerpt, tekst i oblast; Topic i Year. |
| Galleries | `date` opadajuće. | 12; tekstualna pretraga uključuje sadržaj galerije i fotografija; Topic i Year. Prva fotografija je naslovna. |
| Professional network | `items[].date` opadajuće; nedatirani iza datiranih, stabilno. | 4; tekstualna pretraga i Year; View details otvara saradnju i vezu. |
| Recommendations | `recommendations[].date` opadajuće; nedatirani na kraju. | 4; tekstualna pretraga i Year; sažetak i View full recommendation. Home uzima prve dve. |
| Bibliography | Publications, Articles, Conferences, Invited lectures; unutar svake opadajući prvi četvorocifreni broj iz `year`. | 3 po kategoriji, ukupno do 12 vidljivih; zajednički tekst, Category, Year i zasebne stranice kategorija. |
| Resume / Selected Bibliography | Isti redosled kao Bibliography. | Prve tri iz svake kategorije, bez paginacije; View full Bibliography. |
| Experience | Redosled `items`; stari `order` se ignoriše. | Career highlights filtrira isti spisak prema izabranim nazivima. |
| Expertise | Redosled `services`. | Pet oblasti; kartice sa nazivom, sažetkom i detaljima. Povezani projekti imaju isti `topic`. |

Bibliografske godine mogu biti rasponi, npr. `1993/94`: sortiranje uzima 1993, a filter prepoznaje obe godine. Nedatirane jedinice su poslednje. CMS pregled sortira string polje Year; složeni rasponi nisu nužno poređani potpuno kao javni generator.

`dist/assets/journal.js` koristi kompletan `archive-index.json` za Journal, Video, Galleries i Projects; postoje i statičke `/page/2/` stranice. `section-archives.js` obrađuje About i Bibliography, njihove query parametre, broj rezultata i otkrivanje ciljanog sidra van trenutne stranice. Bez JavaScript-a ove sekcije prikazuju sve unose. Broj rezultata arhive nije brojač poseta.

## 3. Polja i odnosi koji zahtevaju pažnju

**Projekti:** `title` znači Akronim, `full_name` pun naziv. Ne mešati `assignment_start/end/ongoing` sa `project_start/end`. Na detaljima slede Back to projects, akronim, Full project name, Project duration, My role, My assignment, fotografija, Project overview, My contribution, Selected results i Related content. Prazni opcioni odeljci se izostavljaju.

| Veza | Sačuvana vrednost | Kako se prikazuje |
|---|---|---|
| `projects.items[].related_content.journal` | `posts.path` | Link ka objavi; objava automatski vraća Related project(s). |
| `…related_content.videos` | Video `link` | Link ka generisanom detalju; povratna veza ka projektu. Stare reference po javnoj video putanji i dalje se prihvataju. |
| `…related_content.galleries` | Gallery `path` | Link ka galeriji i automatska povratna veza. |
| `…related_content.bibliography` | Bibliography `id` / UUID | Link ka `#bibliography-UUID`; cilj se otkriva i kada nije na prvoj stranici. |
| `about.recommendations[].related_contents` | `network.items[].id` / UUID | Related collaborations vodi ka `/about/#network-UUID` i otvara karticu. |

Reference projekata su višestruki izbor iz stvarnih CMS kolekcija. Reference preporuka koriste automatski generisan indeks saradnika jer je original mreže u listi jedne forme. Posle izmene mreže sačekati `sync` i ponovo otvoriti Biografiju da se učita osvežen izbor. Obrisane ili nepostojeće reference se ne prikazuju; nacrti Journal objava nisu javni povezani sadržaji.

Nazivi ekspertiza i izabranih Career highlights služe kao tekstualni ključevi. Pre njihovog preimenovanja proveriti postojeće `topic` vrednosti i izbor angažmana: osvežavanje padajuće liste nije migracija svih starih selekcija.

**Adrese:** novi post/gallery unos bez `path` dobija slug naslova; postojeći `path` se ne menja promenom naslova. Projekat zahteva eksplicitni `/project/...`. Video koristi hash HTTPS linka. Ne preimenovati fizičke fajlove kolekcija samo radi urednosti: nazivi utiču na identitet brojača poseta. Promene adresa, UUID-a i linkova proveravati i kroz `related_content.py`, `content_paths.py`, `metrics.py` i projektna preusmerenja.

**Rich text i dokumenti:** HTML prolazi kroz `cms_data.body`; slike u tekstu su podržane, proizvoljni skriptovi i iframe nisu. Bibliography čuva integralni `reference` odvojeno od strukturiranih polja. Vidljivi citat nastaje iz tih polja; Description se otvara na klik, a prilozi imaju oznaku Download bez naziva fajla.

## 4. Mediji, automatizacija i ciljane provere

CMS mediji koriste `dist/assets` → `/assets`. Fotografije: JPG/JPEG/PNG/WebP; dokumenti: PDF/DOC/DOCX/ODT/RTF/PPTX. `gallery_images.py` upravlja izvedenim slikama i `media/gallery-cache`, bez menjanja originala. Detaljna galerija prikazuje tekst pre mreže, po 12 novih fotografija i pregledač cele liste. Ne mešati ovu funkciju sa paginacijom arhive galerija.

`.github/workflows/sync-expertise.yml` pokreće redom `scripts/sync_expertise.py`, `scripts/sync_related_content.py`, `scripts/sync_projects.py` i `scripts/prepare_gallery_cache.py`. Time održava izbore oblasti i karijere, ID-jeve, prazne post/gallery putanje, indeks saradnika, sortiranje projekata i keš. Save može prethoditi dodatnom sync commitu i deploymentu. Pri problemu proveriti konkretan izvorni unos, sync, zatim najnoviji Pages deployment; ne praviti paralelnu listu sadržaja kao zaobilazno rešenje.

| Promena | Relevantni testovi / dokumentacija |
|---|---|
| Mreža, preporuke, grupisana paginacija | `test_section_archives.py`, `tests/section-archives.cjs`, `section_archives.py` |
| Projects, URL-ovi, reference | `test_projects.py`, `test_related_content.py`, `test_content_paths.py` |
| Journal i arhive medija | `test_journal_pagination.py`, `test_media_pagination.py`, `tests/journal-pagination.cjs` |
| Bibliography | `test_bibliography.py`, `test_section_archives.py` |
| Fotografije i pregledač | `test_gallery_images.py`, `tests/gallery-viewer.cjs` |
| Contact | [CONTACT-SETUP.md](../CONTACT-SETUP.md), `tests/contact*.test.mjs` |
| Brojači | [METRICS-SETUP.md](../METRICS-SETUP.md), `test_metrics.py`, `tests/metrics*.test.mjs` |

Izabrati provere prema promeni, ne pokretati celu tabelu za svaki zadatak. Aktuelne nazive i ponašanje uvek potvrditi u izvoru. Ova mapa ne sadrži tajne niti zamenjuje stanje Cloudflare bindinga.
