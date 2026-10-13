# Radoje Laušević — sajt za Cloudflare Pages

Ovaj paket sadrži novu statičku verziju sajta www.radojelausevic.com, zasnovanu na javno dostupnom Wix sajtu preuzetom 12. oktobra 2026.

## Šta je urađeno

- Početna strana, About, Work experience, Projects, Resume, Galleries i Blog.
- Nova stranica Contact, 20 pojedinačnih blog objava i stranica 404.
- Prilagođavanje mobilnim uređajima, navigacija, pretraga i tematsko filtriranje bloga, galerija sa uvećanjem fotografija.
- Fotografije i dostupni PDF dokumenti čuvaju se u paketu, bez zavisnosti od Wix hostinga.
- Postojeće putanje glavnih stranica i blog objava su sačuvane. Za stare PDF adrese i blog kategorije pripremljena su preusmerenja.
- Sitemap, osnovni metapodaci, strukturirani podaci i bezbednosna zaglavlja.

## Postavljanje bez pretplate

1. Raspakujte ZIP na računar.
2. Otvorite https://dash.cloudflare.com/ i prijavite se ili napravite besplatan nalog.
3. U Workers & Pages izaberite kreiranje Pages projekta i opciju za direktno učitavanje fajlova (Direct Upload / Drag and drop).
4. Kao naziv unesite npr. `radoje-lausevic`.
5. Učitajte **sadržaj direktorijuma `dist`** ili prevucite sam direktorijum `dist` prema uputstvu na ekranu. Njegov `index.html` mora biti na korenu sajta. Ne učitavajte ceo izvorni paket kao sajt.
6. Izaberite Deploy i proverite adresu koju Cloudflare vrati, oblika `<naziv-projekta>.pages.dev`.
7. Otvorite nekoliko stranica, proverite blog, PDF preuzimanja, galeriju i kontakt.

Alternativno, uz instaliran Node.js, možete koristiti zvanični Wrangler:

```
npx wrangler login
npx wrangler pages deploy dist --project-name radoje-lausevic
```

Nije potreban build na Cloudflare-u: sajt je već pripremljen u `dist`.

## Povezivanje postojećeg domena

U Pages projektu otvorite Custom domains i dodajte `radojelausevic.com` i `www.radojelausevic.com`. Pratite dobijene DNS instrukcije. Za osnovni domen Cloudflare traži da njegova DNS zona bude kod Cloudflare-a; to ne zahteva automatski promenu registrara domena. Sačuvajte postojeće zapise za e-poštu ako ih imate. Domen nastavite da obnavljate kod izabranog registrara.

Wix pretplatu isključite tek kada nova verzija radi na oba domena i provere su završene. Nalog, pretplata i DNS postojećeg sajta nisu menjani tokom izrade ovog paketa.

## Kontakt i ranije Wix funkcije

Kontakt forma **ne šalje poruku na server**. Dugme „Prepare email“ otvara korisnikovu aplikaciju za e-poštu sa pripremljenim sadržajem; korisnik zatim šalje poruku. Direktne email i telefonske veze su takođe dostupne. Ako korisnik nema podešenu aplikaciju za e-poštu, koristi prikazanu adresu.

Wix pretplatnička baza, slanje newsletter-a, korisnički nalozi i komentari nisu migrirani; u novoj verziji nema lažne potvrde da su poruke ili pretplate primljene. Za te funkcije potrebno je posebno rešenje i po potrebi izvoz podataka iz Wix naloga.

Video sadržaj i spoljne reference ostaju veze ka originalnim servisima. Istorijske spoljne veze nisu sve proverene za dostupnost. Tekstovi biografije, radnog iskustva, projekata, CV-a i arhive preneti su sa postojećeg sajta; nisu ažurirani prema novijim angažmanima.

## Izmene sadržaja

Za ovu verziju preporučen je Pages CMS. Aktuelni sadržaj nalazi se u `content/cms`; detaljno povezivanje i uređivanje opisani su u `CMS-UPUTSTVO.md`. Stari `content/site.json` je sačuvan kao migraciona osnova i nije primarni editor novih tekstova.

## Raniji način izmene fajlova

Za malu izmenu otvorite odgovarajući HTML fajl u `dist` u tekst editoru, sačuvajte i ponovo učitajte direktorijum `dist` na Cloudflare Pages.

Za ponovno generisanje sajta:

1. Uredite sadržaj u `content/cms` i, za tekst/raspored početne strane, `build.py`.
2. Pokrenite `python3 build.py` (ili `python build.py` na Windows-u).
3. Pokrenite `python3 validate.py`.
4. Ponovo postavite `dist`.

Python skripte koriste samo standardnu biblioteku. Fotografije dodajte u `dist/assets`, a u sadržaju navedite putanju `/assets/ime-fajla.webp` ili odgovarajući format.

Izgled se uređuje u `dist/assets/site.css`; ponašanje navigacije, pretrage, galerije i kontakt forme u `dist/assets/site.js`.

Ovo nije Wix vizuelni editor. Sajt se može održavati kroz datoteke, a kasnije se može povezati sa posebnim sistemom za jednostavnije uređivanje.

## Provera

Provereni su svi lokalni resursi i interne veze, jedna glavna H1 oznaka po stranici, jezik dokumenata, sintaksa JavaScript-a i veličine fajlova za Cloudflare Pages. U ovoj sesiji nije bio dostupan alat za vizuelno testiranje sajta u pregledaču, pa responsivni prikaz i interakcije treba dodatno pregledati na računaru i telefonu pre promene domena.

## Zvanična uputstva

- Direct Upload: https://developers.cloudflare.com/pages/get-started/direct-upload/
- Custom domains: https://developers.cloudflare.com/pages/configuration/custom-domains/
- Limits: https://developers.cloudflare.com/pages/platform/limits/
