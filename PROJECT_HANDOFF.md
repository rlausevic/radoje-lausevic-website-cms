# Radoje Laušević web site — handoff

Datum provere: **3. novembar 2026.** Glavna verzija ovog dokumenta je u repozitorijumu. Ovo je sažetak važećeg stanja, ne dnevnik razvoja. Za pravila pročitajte [AGENTS.md](AGENTS.md); zatim samo potreban odeljak [CMS mape](docs/CMS_MAP.md).

## 1. Merodavni izvori i kontrolna tačka

Aktivan je javni repozitorijum [rlausevic/radoje-lausevic-website-cms](https://github.com/rlausevic/radoje-lausevic-website-cms), grana `main`. Kanonski domen je [www.radojelausevic.com](https://www.radojelausevic.com/); povezani su i `radojelausevic.com` i [radoje-lausevic-website-cms.pages.dev](https://radoje-lausevic-website-cms.pages.dev/). CMS se otvara kroz [Pages CMS](https://app.pagescms.org/rlausevic/radoje-lausevic-website-cms/main).

Poslednja potvrđena produkciona objava pri pripremi handoffa je commit [`ba06d42ccdf026b90317a5f7d107db27f44d7863`](https://github.com/rlausevic/radoje-lausevic-website-cms/commit/ba06d42ccdf026b90317a5f7d107db27f44d7863). GitHub provera **Cloudflare Pages** završena je uspešno 03.11.2026. u 17:44:58, Europe/Belgrade. Uspešni su i `sync` i zaseban Workers build. Pregled te objave: [6dee1941.pages.dev](https://6dee1941.radoje-lausevic-website-cms.pages.dev/). Ova kontrolna tačka ne zamenjuje proveru najnovijeg `main` pre sledećeg rada.

Aktuelni kod i CMS fajlovi imaju prednost nad razgovorima i starim uputstvima. `README.md`, `README-sr.md` i delovi `CMS-UPUTSTVO.md` opisuju ranije faze; ne preuzimati iz njih stari naziv repozitorijuma, Direct Upload postupak ili tvrdnju da Contact samo otvara email aplikaciju.

## 2. Tehnologije i granice izvornog sadržaja

Sajt generiše Python `build.py`, uz `cms_data.py`, `content_archives.py`, `content_paths.py`, `related_content.py`, `network_data.py`, `section_archives.py`, `gallery_images.py` i `metrics.py`. Koristiti Python 3.12+; zavisnost za slike je verzija Pillow iz `requirements.txt`. Interfejs koristi običan CSS i JavaScript, bez frontend frameworka. Pages CMS konfiguracija `.pages.yml` zapisana je kao JSON, što je validan YAML.

`content/cms/` sadrži uređivačke podatke; `content/site.json` ostaje migraciona osnova koju generator još učitava. `dist` je izlaz builda, ali **`dist/assets/` sadrži i prave izvore**: CSS, JavaScript, originale fotografija i dokumente. Ne brisati ceo `dist` i ne koristiti ručno izmenjen HTML kao trajnu popravku. Menjati generator, relevantan modul ili izvorni asset. Build ponovo pravi HTML, indekse, sitemap, zaglavlja i preusmerenja.

## 3. Struktura i važeće odluke

Glavna navigacija je About, Expertise, Projects, Bibliography, Insights, Contact. Ime vodi na Home, a Download CV je izdvojeno dugme. Insights ima svoj link i zasebno otvaranje podmenija Journal, Video, Galleries. `/work-experience` i `/resume` ostaju dostupni iz podnožja kao Career history i CV & documents. Spoljni HTTP(S) linkovi otvaraju novu karticu; unutrašnji ostaju u istoj.

About prikazuje profil, izabranu karijeru, mrežu saradnika, preporuke i CV. Expertise je jedini izvor pet oblasti usluga. Home automatski uzima prve tri oblasti, prva dva sortirana projekta, prve dve sortirane preporuke i po jedan najnoviji Journal, Video i Gallery unos. Insights uzima do tri najnovija unosa iz svake od te tri kolekcije. Nema ručno kopiranih paralelnih verzija.

Projekti u toku imaju prednost, zatim se sortiraju po početku angažmana opadajuće; završeni po završetku angažmana opadajuće. Journal, Video, Galleries i Projects prikazuju 12 kartica po stranici. Network i Recommendations prikazuju po četiri, po datumu opadajuće. Bibliography prikazuje po tri jedinice u svakoj kategoriji, sortirane po godini opadajuće, sa nezavisnom paginacijom. Pretraga obuhvata cele arhive, ne samo vidljive stavke.

## 4. Centralni CV, adrese i povezivanje

Jedini izvor za zajednička Download CV dugmad je `content/cms/resume.json` → `brief_cv`. Trenutni dokument je `/assets/radojelauseviccveuropassshort20261019.pdf`, Europass Brief CV. Generator preferira PDF ako polje sadrži više fajlova. Zadržati ovu centralnu vezu u zaglavlju, About i podnožju; detaljni CV dokumenti ostaju posebni.

Projekti koriste eksplicitni `path`, nezavisan od naslova. `content/project-redirects.json` čuva stare projektne adrese; generator emituje 301 pravila, uključujući varijante sa završnom kosom crtom. Journal i Galleries dobijaju `/post/slug` odnosno `/gallery/slug` samo kada `path` nedostaje; postojeći put ostaje sačuvan. Ručna promena adrese zahteva proveru referenci i preusmerenje: opšti automatski registar promena tih putanja nije implementiran.

Video detaljna adresa nastaje iz hash-a spoljnog `link` polja. Promena tog linka može promeniti javni URL i CMS reference. Bibliography koristi UUID i sidro `bibliography-UUID`. Projekti biraju povezane objave, videe, galerije i bibliografiju iz kolekcija; Journal, Video i Gallery detalji automatski prikazuju povratne veze ka projektima. Preporuke biraju saradnike preko njihovog UUID-a i izvedene liste `network_references`; originali ostaju samo u `network.json`.

## 5. Fotografije

Originali ostaju u `dist/assets/`. Generator galerija pravi WebP prikaze do 480, 960 i 1920 piksela po dužoj stranici, čuva proporcije, ispravlja EXIF orijentaciju i ne uvećava male slike. `media/gallery-cache/` je trajan keš u Git-u, vezan za sadržaj slike i verziju recepta/enkodera. Build kopira potrebne varijante u generisani `dist/media/gallery/`; ne kodira ponovo validan keš.

Galerija prikazuje tekst pre fotografija; duži tekst se otvara preko Read more. Mreža otkriva po 12 fotografija preko Show more photos. Pregledač fotografija uvek obuhvata celu galeriju, sa Previous/Next, brojačem, strelicama, prevlačenjem i vraćanjem fokusa. Slike unutar teksta Journal objave podržane su rich-text editorom i HTML sanitizacijom.

## 6. Contact i posete

Contact koristi Pages funkcije `/api/contact-config` i `/api/contact`, koje preko bindinga `CONTACT_SERVICE` prosleđuju zahtev email Worker-u. Zajednička logika je `server/contact.mjs`. Worker koristi `EMAIL`, `CONTACT_RATE_LIMITER`, `CONTACT_RECIPIENT`, `TURNSTILE_SITE_KEY` i `TURNSTILE_SECRET_KEY`. Ovde se navode samo nazivi; vrednosti ostaju van Git-a. Posetiočev email je Reply-To, primalac nije izbor klijenta. Vlasnik je ranije potvrdio prijem i ispravan Reply-To; tokom pripreme dokumentacije nije slata nova test poruka. Detalji: [CONTACT-SETUP.md](CONTACT-SETUP.md).

Posete koristi zaseban Pages binding `METRICS_DB`, D1 šema `migrations/0001_metrics.sql` i `/api/metrics`. Journal i galerije prikazuju preglede; Video prikazuje preglede stranice, ne reprodukcije. Projekti i klikovi Download CV/Bibliography imaju privatne agregate. To nisu jedinstveni posetioci. Identitet objava, videa i galerija vezan je za naziv fajla, projekata za putanju, bibliografije za UUID; takve promene zahtevaju pažnju prema kontinuitetu brojanja. Ponovni deployment sam po sebi ne prazni D1. Web Analytics je zasebno uključen prema potvrdi vlasnika; njegov dashboard nije ponovo proveren. Detalji: [METRICS-SETUP.md](METRICS-SETUP.md).

## 7. Rad, objavljivanje i nastavak

Pre promene proveriti najnoviji commit i lokalne izmene. CMS Save upisuje u `main`. GitHub Actions `sync-expertise.yml` osvežava oblasti, reference, trajne identifikatore, redosled projekata i keš slika; može napraviti dodatni commit. Zato proveriti završni head, odgovarajući Pages deployment i javnu stranicu. Email Worker ima zasebnu build proveru. Cloudflare dashboard bindinge ne zaključivati samo iz `wrangler.jsonc`.

Standardna kontrola koda je `python3 build.py && python3 validate.py`, zatim relevantni testovi i ciljana provera interakcija. Ovom prilikom generisano je 113 stranica plus 404, validator je prijavio nula grešaka, a 247 slika je ponovo iskorišćeno bez kodiranja. Sortiranje, reference, pretraga i paginacija dokumentovani su prema aktuelnom kodu; nije izvršen probni Save kroz prijavljeni CMS niti fizičko mobilno testiranje. Nema potvrđenog blokirajućeg kvara, ali ovo nije nov potpuni audit.

Sledeći rad početi jednim ograničenim zadatkom u novom razgovoru. Pročitati ovaj sažetak i relevantnu CMS mapu, proveriti aktuelne fajlove, izvršiti potrebne provere i ažurirati samo promenjene činjenice. Eventualno usaglašavanje starih README uputstava ostaje zaseban zadatak. Ovaj dokumentacioni commit ne menja funkcionalnost sajta.
