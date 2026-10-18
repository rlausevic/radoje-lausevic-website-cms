# Pages CMS — povezivanje i svakodnevno uređivanje

Pripremljena je CMS konfiguracija za postojeći sajt i sve blog objave. Izvorni kod je pripremljen za GitHub. Za aktivaciju prijavite se u Pages CMS i povežite Cloudflare projekat sa repozitorijumom; `.pages.yml` se nalazi na korenu i mora biti uključen.

## 1. Izvorni kod na GitHub-u

Kompletan sajt je postavljen u privatni repozitorijum `rlausevic/radoje-lausevic-website`, grana `main`. Konfiguracija `.pages.yml` je na korenu. Nije potrebno ručno postavljanje fajlova.

## 2. Novi Cloudflare Pages projekat sa automatskim objavljivanjem

Postojeći Direct Upload projekat ne može naknadno da se pretvori u Git-integrated projekat. Napravite novi Pages projekat dok postojeći nastavlja da radi.

- Otvorite Workers & Pages i napravite novi Pages projekat preko Git integracije.
- Povežite GitHub i izaberite svoj repozitorijum.
- Production branch: `main` (ili naziv vaše glavne grane).
- Framework preset: `None`.
- Build command: `python3 build.py && python3 validate.py`.
- Build output directory: `dist`.
- Root directory: ostavite prazno.
- Pokrenite prvo objavljivanje i proverite adresu novog projekta.

Ako ste `www.radojelausevic.com` već povezali sa starim projektom, prvo proverite novu verziju, zatim prebacite Custom domain na novi projekat. Ako DNS ostaje na Wix-u, promenite `www` CNAME na novu `.pages.dev` adresu. Ako je DNS na Cloudflare-u, sledite Custom domains postupak novog projekta. Ovaj paket sam nije promenio vaš domen.

## 3. Aktivirajte Pages CMS

1. Otvorite https://app.pagescms.org/ i prijavite se svojim GitHub nalogom.
2. Dozvolite Pages CMS GitHub aplikaciji pristup samo repozitorijumu sajta.
3. Izaberite repozitorijum i granu `main`.
4. CMS čita postojeći `.pages.yml`; ne morate praviti novu konfiguraciju.

## 4. Kako uređujete sajt

- **Podešavanja sajta:** ime, kontakt, domen, opis za pretraživače, portret i panorama.
- **Početna strana:** naslov, uvod i kratki opisi usluga.
- **Biografija:** Profile, izbor Career highlights iz Radnog iskustva, kratak uvod za Expertise i preporuke. Profesionalna mreža ima svoj postojeći CMS izvor.
- **Expertise — oblasti usluga:** jedini izvor pet oblasti, njihovih kratkih uvoda, Services i detaljnih opisa. Selected projects se povezuju automatski prema polju Izbor oblasti u Projektima. Prve tri ekspertize prikazuju se na početnoj strani.
- **Radno iskustvo:** dodajte/uredite angažman i prevucite stavke radi promene redosleda. Puna istorija ostaje na `/work-experience`; izabrani angažmani se prikazuju na About.
- **Projekti:** dodajte/uredite projekat, period, fotografiju, kratak i detaljan opis; redosled određuje prikaz, prva dva se prikazuju i na početnoj strani.
- **Profesionalna mreža:** tekst i PDF dokument.
- **CV i publikacije:** jedno polje **Download CV — Europass Brief CV** kontroliše dokument u zaglavlju, na About i u podnožju. Detaljni CV ostaje zaseban dokument. Obrazovanje se uređuje ovde; Selected Bibliography se automatski preuzima iz Bibliography.
- **Galerija:** postojeća galerija je jedan album; uređujte njegov naslov, datum, kratak opis, fotografije i tekst. Insights prikazuje jedan pregled ovog albuma, bez kopiranja fotografija u nove zapise.
- **Blog objave:** kreirajte ili uredite tekst, datum, naslovnu fotografiju, opis i teme.

Za novu blog objavu unesite adresu poput `/post/novi-projekat`. Koristite mala latinična slova bez dijakritika, brojeve i crtice. **Kod postojećih objava sačuvajte adresu**, kako spoljne veze ne bi prestale da rade. Naziv JSON fajla je nezavisan od javne adrese.

Polje **Objavljeno**:
- isključeno: nacrt; ne pojavljuje se na javnom sajtu;
- uključeno: objava se prikazuje na sajtu nakon uspešnog Cloudflare build-a.

Novi datum ne zakazuje buduću objavu: uključena opcija Objavljeno objavljuje tekst odmah nakon build-a. Najnovije objavljene objave se prikazuju prve.

Insights automatski prikazuje do tri najnovije Journal objave, do tri najnovija videa i postojeću galeriju. Pregledi nemaju zasebne kopije sadržaja.

Posle izmene Expertise, GitHub Actions automatski ažurira izbor oblasti u CMS Projektima. Posle izmene Radnog iskustva ažurira izbor Career highlights. Osvežite CMS nakon završetka workflow-a.

Klikom na Save sačuvate promenu na GitHub-u. Cloudflare zatim automatski gradi i objavljuje sajt. Sačekajte uspešan deployment i osvežite javni sajt. Ako build prijavi grešku, prethodna uspešna verzija ostaje aktivna; otvorite deployment log da vidite razlog.

Fotografije i dokumenti učitavaju se kroz CMS; preporučene su optimizovane fotografije ispod nekoliko MB, a pojedinačan fajl mora biti ispod Cloudflare limita od 25 MiB.

## Šta se uređuje u CMS-u

Ovo je editor sadržaja: tekst, fotografije, dokumenti i redosled stavki. Raspored stranica, boje i fontovi ostaju u šablonu; za te promene se uređuje CSS/izvorni kod. Kontakt forma i dalje priprema email poruku u korisnikovoj aplikaciji za e-poštu.

## Lokalna provera

Sa instaliranim Python-om pokrenite:

```
python3 build.py
python3 validate.py
```

Nisu potrebni dodatni Python paketi. Blog nacrti i uklonjene objave brišu se iz generisanog javnog izlaza pri narednom build-u. Ako dve objave imaju istu adresu, build namerno prijavljuje grešku.

## Zvanična uputstva

- https://pagescms.org/docs/quick-start/
- https://developers.cloudflare.com/pages/get-started/git-integration/
- https://developers.cloudflare.com/pages/get-started/direct-upload/
