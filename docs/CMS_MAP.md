# CMS mapa — forme, izvori i prikaz

Provereno prema `.pages.yml` i generatoru na commitu `ba06d42ccdf026b90317a5f7d107db27f44d7863`, 03.11.2026. Koristiti samo odeljak relevantan za zadatak. Projekti, Journal, galerije i Video (više oblasti), projektne adrese, PDF mreže i automatski redosled radnog iskustva dopunjeni 14.11.2026; Video oblasti dopunjene 15.11.2026. Pravila su u [AGENTS.md](../AGENTS.md), operativni sažetak u [PROJECT_HANDOFF.md](../PROJECT_HANDOFF.md).

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
| Journal | `date` opadajuće, zatim naslov opadajuće kod istog datuma. `published=false` isključuje objavu. | 12; naslov, excerpt, tekst i sve izabrane oblasti; Topic i Year. Stare Teme nisu izvor filtera. |
| Video | `date` opadajuće; stabilne izjednačene vrednosti. | 12; naslov, datum, excerpt, tekst i sve izabrane oblasti; Topic i Year. |
| Galleries | `date` opadajuće. | 12; tekstualna pretraga uključuje sve izabrane oblasti i sadržaj galerije i fotografija; Topic i Year. Prva fotografija je naslovna. |
| Professional network | `items[].date` opadajuće; nedatirani iza datiranih, stabilno. | 4; tekstualna pretraga i Year; View details otvara saradnju i vezu. |
| Recommendations | `recommendations[].date` opadajuće; nedatirani na kraju. | 4; tekstualna pretraga i Year; sažetak i View full recommendation. Home uzima prve dve. |
| Bibliography | Publications, Articles, Conferences, Invited lectures; unutar svake opadajući prvi četvorocifreni broj iz `year`. | 3 po kategoriji, ukupno do 12 vidljivih; zajednički tekst, Category, Year i zasebne stranice kategorija. |
| Resume / Selected Bibliography | Isti redosled kao Bibliography. | Prve tri iz svake kategorije, bez paginacije; View full Bibliography. |
| Experience | `ongoing=true` prvo, po `start` opadajuće; završena po `end` opadajuće. Jednaki datumi zadržavaju redosled izvora; nedatirani su poslednji u svojoj grupi. | Career history i izabrani Career highlights koriste isti sortirani spisak. |
| Expertise | Redosled `services`. | Pet oblasti; kartice sa nazivom, sažetkom i detaljima. Povezani projekti imaju naziv oblasti u svojoj `topic` listi. |

Bibliografske godine mogu biti rasponi, npr. `1993/94`: sortiranje uzima 1993, a filter prepoznaje obe godine. Nedatirane jedinice su poslednje. CMS pregled sortira string polje Year; složeni rasponi nisu nužno poređani potpuno kao javni generator.

`dist/assets/journal.js` koristi kompletan `archive-index.json` za Journal, Video, Galleries i Projects; postoje i statičke `/page/2/` stranice. `section-archives.js` obrađuje About i Bibliography, njihove query parametre, broj rezultata i otkrivanje ciljanog sidra van trenutne stranice. Bez JavaScript-a ove sekcije prikazuju sve unose. Broj rezultata arhive nije brojač poseta.

## 3. Polja i odnosi koji zahtevaju pažnju

**Radno iskustvo:** `start` = Početak radnog iskustva, `end` = Završetak radnog iskustva, `ongoing` = Radno iskustvo u toku. Datum se čuva kao `yyyy-MM`, jer postojeći izvori navode samo mesec i godinu; ne dodaje se izmišljeni dan. Nova datumska polja su inicijalno prazna. `period` je izveden engleski tekst za sajt, bez ručnog polja u CMS-u. `experience_data.py` deli ista pravila sortiranja i prikaza između generatora i `scripts/sync_experience.py`. Sync upisuje redosled posle Save; generator ga primenjuje i pre tog dodatnog commita. Stare stavke bez novih polja mogu zadržati tekst `period`, uz nedatirano sortiranje.

**Journal / Blog objave:** `topic` je višestruki izbor iz Expertise, isto kao za projekte. Postojeći izbor ostaje sačuvan kao jednočlana lista. Sve izabrane oblasti prikazuju se na karticama (Home, Insights, Journal) i u zaglavlju detalja; svaka je dostupna kroz Topic filter i tekstualnu pretragu. `cms_data.content_topics` prihvata i ranije string vrednosti, a `scripts/sync_related_content.py` upisuje liste i za nacrte bez izmene ostalih polja.

**Galerije:** `gallery_entries.topic` je višestruki izbor oblasti iz Expertise. Generator prihvata starije string vrednosti i liste; sync pretvara pojedinačni izbor u jednočlanu listu. Sve oblasti prikazuju se na karticama Home/Insights/Galleries i u zaglavlju detaljne galerije, a svaka radi u Topic filteru i pretrazi. Fotografije, opisi, datumi, putanje i projektne reference ostaju isti. Polje može ostati prazno.

**Video:** `video_entries.topic` je višestruki izbor iz Expertise. Sve izabrane oblasti prikazuju se na karticama Home/Insights/Video i u zaglavlju detaljne video stranice; svaka radi u Topic filteru i tekstualnoj pretrazi. Sync pretvara stare string izbore u liste uz očuvane spoljne video linkove, naslovne fotografije, datume i tekstove. Prazno polje ostaje podržano. Promena oblasti ne menja hash adrese ili projektne reference jer se oni zasnivaju na polju `link`.

**Projekti:** `title` znači Akronim, `full_name` pun naziv. `topic` je višestruki izbor oblasti; postojeće pojedinačne vrednosti se pretvaraju u liste bez promene izbora. Projekat se prikazuje pod svakom izabranom oblasti na Expertise, a Projects pretraga i Topic filter obuhvataju sve izabrane oblasti. Ne mešati `assignment_start/end/ongoing` sa `project_start/end`. Na detaljima slede Back to projects, akronim, Full project name, Project duration, My role, My assignment, fotografija, Project overview, My contribution, Selected results i Related content. Prazni opcioni odeljci se izostavljaju.

| Veza | Sačuvana vrednost | Kako se prikazuje |
|---|---|---|
| `projects.items[].related_content.journal` | `posts.path` | Link ka objavi; objava automatski vraća Related project(s). |
| `…related_content.videos` | Video `link` | Link ka generisanom detalju; povratna veza ka projektu. Stare reference po javnoj video putanji i dalje se prihvataju. |
| `…related_content.galleries` | Gallery `path` | Link ka galeriji i automatska povratna veza. |
| `…related_content.bibliography` | Bibliography `id` / UUID | Link ka `#bibliography-UUID`; cilj se otkriva i kada nije na prvoj stranici. |
| `about.recommendations[].related_contents` | `network.items[].id` / UUID | Related collaborations vodi ka `/about/#network-UUID` i otvara karticu. |

Za Journal i Galleries izbor koristi sačuvani `path`; unos bez tog polja može biti objavljen kroz build, ali još nije dostupan za izbor u CMS-u. Sačekati uspešan sync i ponovo učitati Projekti. Ako sync padne pri obradi fotografija, proveriti `gallery_images.py`: inicijalizacija Pillow-a zaštićena je zaključavanjem da dva radnika ne pokrenu istovremenu instalaciju zavisnosti.

Reference projekata su višestruki izbor iz stvarnih CMS kolekcija. Reference preporuka koriste automatski generisan indeks saradnika jer je original mreže u listi jedne forme. Posle izmene mreže sačekati `sync` i ponovo otvoriti Biografiju da se učita osvežen izbor. Obrisane ili nepostojeće reference se ne prikazuju; nacrti Journal objava nisu javni povezani sadržaji.

Nazivi ekspertiza i izabranih Career highlights služe kao tekstualni ključevi. Pre njihovog preimenovanja proveriti postojeće `topic` vrednosti i izbor angažmana: osvežavanje padajuće liste nije migracija svih starih selekcija.

**Adrese:** novi post/gallery unos bez `path` dobija slug naslova; postojeći `path` se ne menja promenom naslova. Projekat bez adrese dobija `/project/AKRONIM` (npr. `/project/REDEEM`, uz očuvanje velikih i malih slova). CMS polje je opciono, a `sync_projects.py` upisuje adresu posle Save. Po izričito odobrenoj migraciji 22.11.2026. svih 16 postojećih projekata dobilo je adresu iz polja Akronim (razmaci → crtice); svih 26 istorijskih adresa ima direktni 301 na konačan cilj u EN i `/sr/`, sa i bez završne kose crte. Kasnije izmene akronima i dalje ne menjaju već sačuvani `path`. `metrics_id` je zajednički tehnički identitet brojanja u istom unosu i ne uređuje se u CMS-u. Canonical, hreflang, sitemap i povratne reference koriste novi `path`; odobrenja prevoda se ne menjaju migracijom adrese. Za sudare sa postojećim ili starim adresama dodaje se `-2`, `-3` itd. Video koristi hash HTTPS linka. Ne preimenovati fizičke fajlove kolekcija samo radi urednosti: nazivi utiču na identitet brojača poseta. Promene adresa, UUID-a i linkova proveravati i kroz `related_content.py`, `content_paths.py`, `metrics.py` i projektna preusmerenja.

**PDF mreže:** `network.document` je izbor PDF fajlova sa Upload/Select dostupnim i uz postojeću verziju. Poslednji PDF iz liste je jedini aktivan link na About i Career history; oba dugmeta koriste stil Download CV. Posle otpremanja nove verzije prethodnu možete ukloniti iz izbora preko Remove pa Save. Bez izabranog PDF-a nema dugmeta; stara string vrednost ostaje podržana.

**Rich text i dokumenti:** HTML prolazi kroz `cms_data.body`; slike u tekstu su podržane, proizvoljni skriptovi i iframe nisu. Bibliography čuva integralni `reference` odvojeno od strukturiranih polja. Vidljivi citat nastaje iz tih polja; Description se otvara na klik, a prilozi imaju oznaku Download bez naziva fajla.

## 4. Mediji, automatizacija i ciljane provere

CMS mediji koriste `dist/assets` → `/assets`. Fotografije: JPG/JPEG/PNG/WebP; dokumenti: PDF/DOC/DOCX/ODT/RTF/PPTX. `gallery_images.py` upravlja izvedenim slikama i `media/gallery-cache`, bez menjanja originala. Detaljna galerija prikazuje tekst pre mreže, po 12 novih fotografija i pregledač cele liste. Ne mešati ovu funkciju sa paginacijom arhive galerija.

`.github/workflows/sync-expertise.yml` pokreće redom `scripts/sync_experience.py`, `scripts/sync_expertise.py`, `scripts/sync_related_content.py`, `scripts/sync_projects.py` i `scripts/prepare_gallery_cache.py`. Time održava izbore oblasti i karijere, ID-jeve, prazne post/gallery putanje, liste oblasti Journal objava, galerija i video unosa, indeks saradnika, sortiranje radnog iskustva i izvedene periode, sortiranje projekata, njihove prazne adrese iz akronima, liste oblasti i keš. Save može prethoditi dodatnom sync commitu i deploymentu. Pri problemu proveriti konkretan izvorni unos, sync, zatim najnoviji Pages deployment; ne praviti paralelnu listu sadržaja kao zaobilazno rešenje.

| Promena | Relevantni testovi / dokumentacija |
|---|---|
| Radno iskustvo, Career highlights | `test_experience.py`, `test_cms.py`, `test_navigation.py` |
| Mreža, preporuke, grupisana paginacija | `test_section_archives.py`, `tests/section-archives.cjs`, `section_archives.py` |
| Projects, URL-ovi, reference | `test_projects.py`, `test_related_content.py`, `test_content_paths.py`, `test_project_network_editing.py` |
| Journal i arhive medija | `test_video.py`, `test_gallery_topics.py`, `test_journal.py`, `test_journal_pagination.py`, `test_media_pagination.py`, `tests/journal-pagination.cjs` |
| Bibliography | `test_bibliography.py`, `test_section_archives.py` |
| Fotografije i pregledač | `test_gallery_images.py`, `tests/gallery-viewer.cjs` |
| Contact | [CONTACT-SETUP.md](../CONTACT-SETUP.md), `tests/contact*.test.mjs` |
| Brojači | [METRICS-SETUP.md](../METRICS-SETUP.md), `test_metrics.py`, `tests/metrics*.test.mjs` |

Izabrati provere prema promeni, ne pokretati celu tabelu za svaki zadatak. Aktuelne nazive i ponašanje uvek potvrditi u izvoru. Ova mapa ne sadrži tajne niti zamenjuje stanje Cloudflare bindinga.

## 5. Višejezično uređivanje u istom unosu (22.11.2026)

| Podatak | Engleski | Srpski — ćirilica |
|---|---|---|
| Naslov, sažetak, tekst, SEO opis | Postojeća polja; dodat je `seo_description` | Odgovarajuća polja u grupi `sr` |
| Projekat | `title` je zajednički akronim; `full_name`, `summary`, `role`, `body`, `contribution`, `results` su engleski | Prevodi istih tekstualnih polja u `items[].sr`; nema drugog akronima |
| Datum, fotografije, putanja i reference | Zajednički izvori | Isti podaci, bez dupliranja |
| Odobrenje | Postojeći `published` za objavu ostaje glavni uslov | `sr.approved` + odgovarajući izvorni i odobreni otisci teksta |
| Stanje prevoda | Nema dodatnog engleskog unosa | `sr.status`, readonly, osvežava sync nakon Save |

`sr.source_hash` čuva verziju originala. `sr.approved_hash` čuva odobreni prevod. AI/import ih postavlja bez odobrenja. Nakon ručne provere uključiti **Проверио сам превод — објави српску верзију**, Save, sačekati uspešan sync i deployment. Izmena originala odmah čini prevod nevažećim za javni build; sync upisuje stanje potrebnog ažuriranja. Posle ručnog usklađivanja uključiti **Ускладио сам превод са измењеним оригиналом**, Save i ponovo učitati formu; zatim proveriti i odobriti. Izmena već odobrenog prevoda takođe zahteva novo odobrenje.

Dugme AI nacrta postoji na podržanim file formama i stranicama kolekcijskog unosa. Za Projects koristite repozitorijumsku akciju **Припреми AI нацрт пројекта (српски)** u levom meniju; dijalog traži tačan postojeći `path` projekta. Akcija u zaglavlju Projects fajla uklonjena je jer slanje celog `context.data` prelazi GitHub ograničenje i izaziva „Inputs are too large“. Repo akcija šalje mali kontekst, a workflow čita samo odabrani sačuvani projekat iz Git-a. Akcija radi sa sačuvanim sadržajem, ne sa nečuvanim izmenama u editoru. Nedostajući API ključ daje jasnu grešku u Actions, bez izmene sadržaja. Detalji i alternativa preko ChatGPT-a su u [MULTILINGUAL.md](MULTILINGUAL.md).

Pojedinačni tekstualni podzapisi Expertise, Experience, Network i preporuka imaju svoje `sr` grupe i svoje odobrenje. Naslovi/identifikatori korišćeni za reference ostaju zajednički gde je to potrebno. Bibliografski citat ostaje u izvornom obliku; prevodi se opis. `i18n-fields.json` je eksplicitna lista dozvoljenih prevodivih tekstova; AI ne može upisati datum, medij, putanju, referencu ili odobrenje.

**Potvrđen stvarni tok, 22.11.2026:** Pages CMS AI akcija uspešno je napravila BLUECONNECT nacrt (run `45062777181`); vlasnik ga je pregledao, odobrio i objavio. Kontrolna tačka `127c5441772ea7534a42f305b46144522c2081ff` potvrđuje obe javne verzije i SEO. Glavni **Objavljeno** (`published`) i srpsko odobrenje su nezavisni; oba moraju biti uključena za srpsku Blog objavu. `refresh_source` i odobrenje ne čuvati u istom koraku: prvo sačekati uspešan sync usklađivanja, ponovo otvoriti unos i proveriti da je usklađivanje isključeno, pa sačuvati odobrenje. Čuvanje engleskog SEO opisa takođe zahteva ponovno usklađivanje. Polje `SEO opis — English — српски` nalazi se u grupi `sr` i čuva srpski SEO opis; gornje `SEO opis — English` čuva engleski.

**Oznake početne strane:** fiksna dugmad, naslovi sekcija i tekstovi tri statistička polja prevode se kroz `i18n-ui.json`. Ovo uključuje Explore my work, Meet Radoje, How I can help, Selected work i View all recommendations. Tekstovi odvojeni sa `<br>` imaju zasebne ključeve u rečniku. Naslov i uvod početne strane uređuju se u Home → `sr`; tri kartice usluga u Expertise → `services[].sr`; opisi izabranih projekata u Projects → `items[].sr`; sažeci preporuka u About → `recommendations[].sr`. To su postojeći zajednički izvori i svaki prevod čeka vlasničko odobrenje. Dopuna rečnika interfejsa ne odobrava sadržaj i ne menja podatke ili iznose u statističkim poljima.
