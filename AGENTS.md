# Pravila rada — radojelausevic web site

Ova pravila važe za ceo repozitorijum `rlausevic/radoje-lausevic-website-cms`. Za početno stanje pročitaj `PROJECT_HANDOFF.md`, a iz `docs/CMS_MAP.md` samo odeljak potreban za konkretan zadatak. Glavne verzije dokumentacije su u Git-u; kratke projektne instrukcije u ChatGPT-u mogu upućivati na njih bez kopiranja celog sadržaja.

## Izvori i opseg

- Aktuelni repozitorijum ima prednost nad starim opisima iz razgovora i istorijskim uputstvima. Proveri najnoviji `main`, lokalne izmene i relevantne izvore pre uređivanja.
- Sačuvaj CMS izmene nastale u međuvremenu. Pre upisa ponovo proveri head; pri konkurentnoj izmeni prilagodi svoju promenu novom stanju. Ne koristi force push i ne prepisuj tuđi rad.
- Sprovodi traženi zadatak. Ne uvodi usput redizajn, preimenovanja, migracije ili dodatne funkcije. Traži pojašnjenje samo kada nedostaje podatak koji bitno utiče na rezultat ili ovlašćenje.

## Sadržaj i kontinuitet

- Zadrži vizuelni identitet, boje, tipografiju, kompaktan raspored, postojeće adrese i jedinstvene izvore podataka. Promenu URL-a prati odgovarajućim preusmerenjem i proverom referenci i brojača.
- Javni sadržaj i interfejs ostaju na engleskom; CMS oznake i uputstva mogu biti na srpskom. Odgovaraj na jeziku korisnikovog zahteva.
- Ne izmišljaj angažmane, rezultate, preporuke, datume ili profesionalne kvalifikacije. Nepoznate vrednosti ostavi prazne ili jasno označi nedostatak.
- Home, Insights i Resume preuzimaju sadržaj iz postojećih kolekcija. Ne pravi duple uređivačke verzije. Centralni Download CV potiče iz `resume.json` → `brief_cv`.
- Ne uređuj generisani HTML kao trajno rešenje. `dist/assets/` sadrži izvorne stilove, skripte, dokumente i fotografije; ne briši ceo `dist`. Sačuvaj originale i postojeći keš obrađenih slika.
- Nikada ne upisuj tajne, pristupne tokene, lozinke ili privatne konfiguracione vrednosti u javni repozitorijum, dokumentaciju ili logove.

## Efikasan rad i provera

- Koristi ciljanu pretragu i čitaj relevantne delove fajlova. Ne ponavljaj celu istoriju projekta ili opširne izlaze alata. Nezavisne provere grupiši kada je to bezbedno.
- Testiraj promenjenu funkcionalnost i povezane delove. Za promene generatora ili renderovanja pokreni build i validator. Za izmene samo dokumentacije proveri činjenice, putanje i linkove; dodatne testove radi ako postoji konkretan razlog.
- Posle uspešnih provera ne ponavljaj ih bez nove izmene, greške ili nerazjašnjenog rizika. Za interakcije proveri stvarno ponašanje, uključujući tastaturu ili mobilni raspored kada ih promena dotiče.

## Objavljivanje i predaja

- Objavljivanje izvrši kada je odobreno za konkretan zadatak; ne traži ponovo već dato odobrenje. Uspeh upisa u Git nije potvrda uspešnog deploymenta.
- Za objavu sajta proveri odgovarajući Cloudflare Pages commit i rezultat, zatim relevantnu javnu stranicu. Razlikuj Pages, email Worker i CMS sync proveru.
- Za dokumentacione promene koristi `[CF-Pages-Skip]` kada nije potreban novi Pages deployment. Ne menjaj hosting, domene, bindinge ili baze radi dokumentacionog zadatka.
- Na kraju kratko navedi rezultat, relevantne provere, preostala ograničenja i vezu ka izmeni ili rezultatu. Ne tvrdi da je provereno ono što nije.
- Posle značajne promene ažuriraj odgovarajući deo handoffa i CMS mape; rešene pokušaje ostavi u Git istoriji. Novi razgovor neka ima jedan jasan cilj.
