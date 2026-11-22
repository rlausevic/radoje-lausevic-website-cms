# Uređivanje engleske i srpske verzije

Engleski je osnovni jezik. Postojeće adrese se ne menjaju. Srpska ćirilica koristi istu putanju sa `/sr/` prefiksom. Jedan sadržaj ostaje jedan unos u Pages CMS-u.

## Svakodnevni rad

1. Uredite i sačuvajte engleski original u postojećim poljima.
2. Otvorite **Српски — ћирилица** u istom unosu. Prevedite naslov, sažetak, tekst i SEO opis. Za projekat akronim ostaje zajednički; prevode se pun naziv, sažetak, uloga, pregled, doprinos i rezultati. Sva popunjena engleska tekstualna polja moraju imati prevod pre objave; SEO opis je opcioni, sa sažetkom kao rezervnim opisom.
3. Za AI pripremu kliknite **Припреми AI нацрт (српски)** u zaglavlju podržanog sačuvanog unosa. Za Projects koristite **Припреми AI нацрт пројекта (српски)** u levom meniju repozitorijuma; dijalog traži stvarnu trajnu adresu odabranog projekta iz polja `path` (REDEEM trenutno `/project/REDEEM`). Sačekajte uspešan GitHub Actions rezultat i ponovo otvorite/učitajte unos. Projektna akcija šalje samo adresu; workflow učitava sačuvan tekst iz Git-a.
4. Proverite tačnost i stil prevoda, imena, terminologiju i veze. Nacrti se ne prikazuju posetiocima.
5. Proverite da je glavni prekidač **Objavljeno** uključen za celu objavu. U srpskoj grupi uključite **Проверио сам превод — објави српску верзију**, kliknite Save i sačekajte uspešan sync i Cloudflare Pages deployment. Ovo su dva odvojena prekidača: odobrenje prevoda samo ne uključuje Objavljeno. Odobrenje važi samo za proverenu verziju izvornog i prevedenog teksta.

Za potpuno ručni novi prevod prvi Save uspostavlja izvorni otisak i ostavlja nacrt. Ponovo učitajte formu, zatim proverite i odobrite. AI nacrt već ima izvorni otisak.

## Kada se tekst promeni

- Izmena engleskog teksta odmah sprečava javni prikaz starog prevoda. Sync prikazuje **Потребно ажурирање** i uklanja odobrenje. Deljeni datum, akronim, fotografija ili reference sami po sebi ne menjaju tekstualni otisak.
- Ponovna AI priprema koristi novi original i pravi neodobreni nacrt. Postojeći srpski tekst biće zamenjen novim nacrtom; prethodna verzija ostaje u Git istoriji.
- Kod ručnog ažuriranja, uskladite prevod, uključite **Ускладио сам превод са измењеним оригиналом**, Save i sačekajte da GitHub Actions **Sync CMS content choices** završi uspešno. Zatvorite i ponovo otvorite unos; opcija usklađivanja mora biti isključena. Zatim ponovo proverite i odobrite. Ako se obe opcije sačuvaju istovremeno, usklađivanje ima prednost i odobrenje se vraća na isključeno. Ovo sprečava da staro odobrenje postane odobrenje novog teksta.
- Promena već odobrenog srpskog teksta vraća ga u nacrt. Potrebno je novo odobrenje nakon sync-a.
- Engleski `published=false` povlači obe jezičke verzije objave.

## Prvo podešavanje AI dugmeta

GitHub repository Settings → Secrets and variables → Actions: dodajte secret **OPENAI_API_KEY**. Ne upisujte ključ u CMS, izvorne fajlove, javni repozitorijum ili razgovor. API poziv ide iz GitHub Actions-a; ključ se ne šalje browseru. Model je podrazumevano `gpt-4.1-mini`; repository variable **OPENAI_TRANSLATION_MODEL** može postaviti drugi model koji podržava strukturirani JSON izlaz. Potrebni su omogućen GitHub Actions i pravo Pages CMS GitHub veze da pokreće workflow.

Vlasnik je 22.11.2026. postavio secret i završio potrebno API podešavanje. Stvarni poziv preko Pages CMS-a uspešno je pripremio neodobreni BLUECONNECT nacrt ([potvrđen workflow](https://github.com/rlausevic/radoje-lausevic-website-cms/actions/runs/45062777181)). Vrednost ključa nije čitana ni sačuvana u repozitorijumu. Raniji HTTP 429 pokazao je da za početni rad treba proveriti API kredit i kvotu; sam ključ ne obezbeđuje kredit.

Nije potreban API ključ kada u ChatGPT-u zatražite, na primer: **„Pripremi srpski ćirilični nacrt za BLUECONNECT u postojećem CMS unosu, bez odobravanja prevoda.“** AI priprema tekst i čuva ga u istoj `sr` grupi; zatim ga proveravate u CMS-u.

Za tehnički export/import koristi se `scripts/translate_sr.py --path content/cms/posts/IME.json --export --output /tmp/draft.json`. Za Projects dodaje se `--project-path /project/STVARNA-ADRESA`. U export se doda `translation` objekat sa istim tekstualnim ključevima, pa `--apply /tmp/draft.json`. Import proverava nepromenjen original i srpski nacrt, dozvoljena polja i očuvane URL-ove. Uvek čuva `approved=false`.

## Šta posetilac vidi

EN/СР vodi na isti sadržaj. Bez odobrenog prevoda srpska adresa daje obaveštenje sa vezom na engleski original, `noindex,follow` i engleski canonical. Srpske arhive prikazuju prevedene unose i jasno označene engleske originale. Odobrene srpske stranice imaju `lang="sr-Cyrl"`, sopstveni canonical i uzajamne `hreflang` veze; pojavljuju se u sitemap-u. Datumi, fotografije, akronimi, projektne reference i identitet brojača su zajednički.

BLUECONNECT projekat ostaje početni nacrt. Vlasnik je pregledao i odobrio vest o početku rada centra za akvakulturu; engleska i srpska verzija, jezičke veze, SEO opisi, canonical URL-ovi i sitemap potvrđeni su javno 22.11.2026.

## Tehničke zavisnosti i provere

Pages CMS [Actions](https://pagescms.org/docs/configuration/actions/) pokreću workflow sa JSON `payload` ulazom. AI koristi OpenAI [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create) sa strukturiranim JSON izlazom i `store=false`. Tajne ostaju u okruženju. Nema novog frontend frameworka ili drugog CMS-a.

Pokrenuti `python3 build.py`, `python3 validate.py` i `python3 -m unittest test_i18n` uz relevantne postojeće testove. Za testove koji stvaraju nove slike instalirati tačnu verziju Pillow-a iz `requirements.txt`. Produkcioni uspeh potvrditi za odgovarajući commit kroz Cloudflare Pages, pa javnu englesku i srpsku stranicu. Tok koji je vlasnik sproveo u prijavljenom CMS-u i AI poziv sa stvarnim ključem potvrđeni su 22.11.2026. kroz workflow, sačuvani unos i javni rezultat. Ne predstavljati ranije simulacije kao proveru novih servisa.

Projektno AI dugme je premešteno u levi meni jer file akcija šalje ceo `projects.json` u `context.data`. Posle rasta fajla to prelazi GitHub workflow_dispatch ograničenje od 65.535 znakova i daje „Inputs are too large“ pre pokretanja workflow-a. Repo akcija nema telo svih projekata u kontekstu. Ne skraćivati projektne tekstove niti menjati trajne adrese radi ovog ograničenja.
