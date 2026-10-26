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
- **Projekti:** redosled u CMS-u, na Projects i u Homepage / Selected work je automatski, od najnovijeg ka najstarijem. Završeni angažmani koriste **Završetak angažmana**, a oni označeni **Angažman u toku** koriste **Početak angažmana**. Tekući angažmani su uvek prvi i sortiraju se po početku od najnovijeg ka najstarijem; zatim slede završeni po završetku od najnovijeg ka najstarijem. Za iste datume ostaje postojeći redosled, a unosi bez odgovarajućeg datuma su na kraju svoje grupe. Posle Save sačekajte automatsku obradu i ponovo učitajte CMS. Selected work prikazuje prva dva projekta.
- **Profesionalna mreža:** tekst i PDF dokument.
- **CV i publikacije:** jedno polje **Download CV — Europass Brief CV** kontroliše dokument u zaglavlju, na About i u podnožju. Detaljni CV ostaje zaseban dokument. Obrazovanje se uređuje ovde; Selected Bibliography se automatski preuzima iz Bibliography.
- **Galerije:** uređujte svaki album zasebno: naslov, datum, oblast, kratak opis, fotografije i tekst. Insights prikazuje do tri najnovije galerije.
- **Blog objave:** kreirajte ili uredite tekst, datum, naslovnu fotografiju, opis i teme.

Za novu blog objavu ostavite adresu praznu za automatski slug ili unesite adresu poput `/post/novi-projekat`. Koristite mala latinična slova bez dijakritika, brojeve i crtice. **Kod postojećih objava sačuvajte adresu**, kako spoljne veze ne bi prestale da rade. Naziv JSON fajla je nezavisan od javne adrese.

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

### Oblasti objava, videa i galerija

Polje **Oblast** u Blog objavama, Video arhivi i Galeriji koristi nazive iz **Expertise — oblasti usluga / My services**. Nakon izmene naziva oblasti, GitHub workflow automatski osvežava izbore u CMS-u. Ponovo otvorite CMS da vidite nove izbore. Raniji unosi bez izabrane oblasti ostaju vidljivi uz **All topics**; oblast im dodelite uređivanjem unosa. Pretraga članaka koristi naslov, kratak opis, tekst i oblast.

### Galerije

U **Galerije** svaki album je zaseban unos, automatski sortiran po datumu od najnovijeg. Prva fotografija je naslovna fotografija kartice. Klik na **View full gallery** otvara album, a klik na fotografiju uvećan prikaz sa kretanjem kroz fotografije.

### Automatska priprema fotografija galerije

U CMS unesite jednu fotografiju (JPEG, PNG ili WebP), uz očuvan odnos stranica. Preporuka je duža stranica 1920 px, npr. 1920 × 1440 px ili 1440 × 1920 px. Pri svakom objavljivanju sajt automatski pravi WebP verzije do 480 i 960 px za kartice i mrežu, i do 1920 px za uvećanje. Manje originale ne uvećava. Fotografije sa telefona pravilno se okreću prema EXIF orijentaciji. Velika verzija se učitava tek kada posetilac klikne fotografiju.

Original ostaje u CMS-u. Obrađene verzije se trajno čuvaju u `media/gallery-cache` u repozitorijumu, odvojeno od CMS originala. CMS automatizacija dopunjava keš samo za nove ili promenjene fotografije. Svaki novi Cloudflare checkout dobija gotove verzije; Python/Pillow nije potreban za njihovo ponovno korišćenje. Izlaz za objavljivanje ostaje `dist/media/gallery` i sadrži samo fotografije koje se trenutno koriste.

Keš koristi sadržaj originala i verziju recepta/enkodera kao identifikator, proverava SHA-256 svih sačuvanih verzija i automatski obnavlja nedostajuću ili oštećenu verziju. Promena originala ili recepta daje novu adresu, dok postojeće fotografije zadržavaju svoje URL-ove i kvalitet. Automatski se uklanjaju samo zastarele verzije u kešu, nikada originalne fotografije. `media/gallery-cache` ne uređujte ručno i nemojte ga stavljati u `.gitignore`.

Ako nedostaje keš, običan build ga automatski popunjava; objavljivanje zato ne zavisi od uspeha pomoćnog workflow-a. Za ručno održavanje pokrenite `python3 scripts/prepare_gallery_cache.py`. Svaki build ispisuje broj ponovo upotrebljenih i novoobrađenih slika i ukupno vreme. Workflow čuva keš u Git-u; commit koji menja samo keš koristi `[CF-Pages-Skip]` da ne bi pokrenuo još jednu Pages izgradnju. CMS izmene i dalje normalno pokreću objavljivanje. Paralelne CMS izmene se čuvaju: workflow pri konfliktu ponavlja pripremu nad najnovijim stanjem grane main.

Obrada se obavlja nakon uspešnog uploada i ne menja ograničenje veličine uploada u Pages CMS-u. Veći broj upload-a i dalje može pokrenuti više Cloudflare izgradnji; ova dorada ubrzava njihov rad, ali ne menja Cloudflare red čekanja ili tarifni plan.

## Direktan izbor povezanih sadržaja

U Projekti → Related contents sve četiri liste pretražuju stvarne kolekcije.
Unose uređujte u **Blog objave**, **Video**, **Galerije** i **Bibliography**.
Svaki od ovih odeljaka prikazuje jednu kolekciju. Blog, video i galerije imaju
podrazumevani redosled po datumu od najnovijeg; Bibliography po godini od najnovije.
Ručni redosled više nije izložen u CMS-u. Postojeći redosled za iste godine ostaje sačuvan.

Naslovi arhiva i njihovi uvodni tekstovi uređuju se u **Podešavanja sajta →
Naslovi i uvodni tekstovi arhiva**. Tu su i opisi bibliografskih kategorija.
Unosi se ne dupliraju u podešavanjima.

### Automatska adresa blog objave i galerije

**Naslov** uvek ostaje izmenljiv. Polje **Adresa unosa** možete ostaviti prazno.
Pri objavljivanju sajt odmah koristi `/post/slug-iz-naslova` ili
`/gallery/slug-iz-naslova`, a workflow nakon čuvanja upisuje istu adresu u CMS.
Osvežite formu nakon završetka obrade da vidite generisanu adresu.
Ako naslov već postoji, dodaje se jedinstveni sufiks. I nacrti rezervišu adresu.

Polje adrese ostaje ručno izmenljivo. Promena naslova ne menja postojeću adresu.
Postojeće adrese nisu regenerisane. Ručna promena već objavljene adrese zahteva
posebno preusmerenje ako želite da sačuvate ranije podeljene linkove.
Video zadržava postojeću adresu; Bibliography koristi trajne UUID oznake.

Video, galerije i bibliografske jedinice čuvaju se pojedinačno u odgovarajućim
kolekcijama. Stari zajednički JSON fajlovi čuvaju samo interni redosled za
izjednačene godine/datume, bez druge kopije sadržaja. Ranije javne adrese i
prilozi su sačuvani.

### Journal: stranice, pretraga i filter godine

Journal prikazuje 12 objava po stranici, od najnovije ka najstarijoj. Kartice imaju datum, oblast i kratak opis ograničen na tri reda; puni tekst i opis u CMS-u ostaju sačuvani. Godine u filteru Year automatski se preuzimaju iz datuma objavljenih unosa.

Generator pravi zasebne HTML stranice `/blog/`, `/blog/page/2/`, itd. Numerisane stranice rade i bez JavaScript-a. Za pretragu svih objava i kombinovanje Topic + Year postoji generisani `dist/blog/archive-index.json`, koji se preuzima tek kada je potreban. Nije dovoljno samo sakriti dodatne kartice: svaka statička stranica zaista sadrži najviše 12 unosa.

URL može da čuva `search`, `category`, `year` i `page`. Pretraga koristi naslov, kratak opis, tekst i oblast celog arhiva pre podele na stranice. Promena pretrage ili filtera vraća prikaz na prvu stranicu rezultata. Povratak iz objave čuva prethodni izbor i poziciju u okviru istog taba, kada je sessionStorage dostupan. Bez čuvanja podataka u pregledaču Back i URL i dalje ostaju funkcionalni.

Novi unosi, promene datuma i uklanjanje objava automatski ažuriraju indeks i broj stranica pri sledećem uspešnom objavljivanju; CMS forma nije menjana. Za JavaScript provere: `node tests/journal-pagination.cjs dist/blog/archive-index.json`.
