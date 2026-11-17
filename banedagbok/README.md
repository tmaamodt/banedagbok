# Banedagbok

Nettside som viser kamper fra fotball.no og faste treningstider på klubbens baner, med varsel når to aktiviteter bruker samme del av banen samtidig.

Siden er én fil (`index.html`) og har tre lagringsmåter. Den velger selv:

| Når | Lagring |
|---|---|
| Supabase-adresse og nøkkel er fylt inn i `index.html` | Delt database i Supabase. Rollene under håndheves av databasen. Kamper hentes automatisk hver natt. |
| Siden er publisert som Claude-artefakt | Delt lagring i artefakten. **Testmodus**: velgeren «Vis som» viser siden slik hver rolle ser den, men rollene håndheves ikke. |
| Ellers (fila åpnet direkte) | Bare i nettleseren på denne maskinen, også i testmodus |

## Roller

| Rolle | Kan |
|---|---|
| Besøkende (ikke innlogget) | Se ukevisningen, og velge bane og lag. Merknader er skjult. |
| Trener | Avlyse enkeltøkter av faste treninger, og avlyse (slette) enkelttreninger, treningskamper og bookinger for egne lag. Sende forespørsel om enkelttrening eller treningskamp. |
| Trener+ | Alt en trener kan, og i tillegg booke og endre enkelttreninger og treningskamper for egne lag direkte. |
| Admin | Alt: brukere og lag, faste treningstider, bookinger, anlegg, import, og godkjenne eller avslå forespørsler. |

Det finnes to typer treninger:

- **Fast hver uke:** en ukedag og en periode fra–til. Den stopper av seg selv når perioden er over, og har hurtigvalg for vår- og høstsesong.
- **Enkelttrening:** én dato.

Faste treningstider legges bare inn av admin. Trenere avtaler dem med admin, og kan ikke sende forespørsel om dem.

**Treningstider** er en visning som er lik for alle: treningstidene samlet per lag, med dag, tid, bane og hvilken periode eller hvilke uker de gjelder. Velg ett lag eller alle, og filtrer på anlegg. Trenere kan krysse av for «Bare mine lag». Faste treninger med periode som er over, vises ikke. Klikk på en trening for å se mer, og for å avlyse, endre eller slette hvis du har lov.

**Avlysning:** trenere kan bare avlyse én økt om gangen av en fast treningstid, ikke slette eller endre den fremover i tid. Det gjør admin i planen. Klikk på økta i uka for å avlyse den dagen, eller på treningen i Treningstider og velg økt i lista. En avlyst økt kan gjeninnføres på samme måte. Enkelttreninger kan trenere avlyse helt. Databasen stopper også trenere fra å slette faste treningstider.

**Booking i ukevisningen.** Logget inn merker du først et område i uka:

- **Klikk** på en ledig flate for å merke halvannen time fra der du klikket, i det kvarteret du klikket i.
- **Dra** over tid og del av banen for å merke akkurat det du vil, også oppå treninger som ligger der fra før. Drar du over to kvarter, blir det halvdelen, og over hele bredden blir det hele banen.
- Det merkede vises med ramme i uka og i en linje over sesongstripa. Esc eller ✕ fjerner merkingen.

Et klikk åpner ikke noe skjema. Det gjør knappen **«Booking»**, som fyller ut dag, tid og del av banen fra det merkede. Skjemaet sier med en gang om tiden er ledig eller hva den kolliderer med.

- **Trener:** velger enkelttrening eller treningskamp og trykker **«Send forespørsel»**. Admin godkjenner eller avslår. Skjemaet sier fra om at man må ha rollen Trener+ for å booke direkte.
- **Trener+:** velger enkelttrening eller treningskamp og trykker **«Book»**. Da legges det inn med en gang.
- **Admin:** velger fast trening, enkelttrening, treningskamp eller annen booking (cup, banevedlikehold og liknende).

Velger man treningskamp, foreslås spillform ut fra hvor stor del av banen som er merket: hele banen gir 11er, halvdel 9er og kvart 7er.

Uten merking fungerer knappen også, men da må dag, tid og bane fylles ut i skjemaet. Gjesteanlegg kan ikke merkes.

Når admin godkjenner en forespørsel, blir den automatisk en treningstid. Fanen Forespørsler viser forespørslene og svarene.

**Treningskamper** finnes ikke på fotball.no og legges inn i banedagboken av admin eller Trener+. En trener sender forespørsel om treningskamp fra ukevisningen, og den legges inn når admin godkjenner. De vises som kamper i lilla. Henteskriptet rører dem aldri.

**Kamper fra fotball.no** kan bare vises. Ingen kan endre eller slette dem i banedagboken, heller ikke admin. Hvilken del av banen de havner på, styres av koblingene under Baner. Skal en kamp flyttes, søker man om omberamming hos fotball.no (lenke i kampvinduet). Banen er reservert fra 15 minutter før kampstart: en kamp med avspark 20:15 vises som opptatt fra 20:00, og kampvinduet viser både kampstart og tiden banen er opptatt.

**Kamp går foran trening.** Treningstidene settes opp først. En trening som overlapper en kamp eller booking på samme del av banen, viker. Det gjelder uansett hvordan kampen er lagt inn: fra fotball.no, importert, som treningskamp eller som booking for hånd.

- I uka vises den stiplet og overstreket.
- Den listes under «Kamp eller booking går foran», og regnes ikke som en kollisjon.

**Besøkende** ser en enkel side med bare uka: valg av bane og lag, uke fram og tilbake, ukevisningen og en forklaring på fargene. Fanene, sesongstripa og verktøyene for innloggede er skjult. Tidsaksen tilpasses aktivitetene, så tomme formiddager ikke tar plass.

**På mobil** vises én dag om gangen, med en rad med ukedagene over for å bytte dag. Dagen i dag er valgt når siden åpnes. Sesongstripa er skjult på mobil. Kryss av for **«Vis hele uka»** for å se alle sju dagene samtidig, som på PC. Da er kolonnene smale og uten kvartinndeling, men blokkene ligger fortsatt på riktig del av banen, så du ser hvor det er ledig. Kvartbokser vises bare med farge, og et trykk på en blokk viser detaljene. Trykk på et dagnavn for å gå tilbake til den dagen. Valget huskes til neste gang.

**Kollisjoner** vises i selve boksene, ikke som varsler over uka. Når to treninger krasjer, eller kamper og bookinger krasjer med hverandre, blir boksene røde. Boksene som overlapper, legges oppå hverandre med litt forskyvning, så alle kan klikkes.

**Bare ett lag:** alle, også besøkende, kan velge et lag i lista ved siden av banevalget. Da vises lagets treninger, treningskamper, forespørsler og kamper fra fotball.no (via koblingene under Lag). Det som overlapper med lagets tider på samme del av banen, vises også, men blekt. Trenere har sine egne lag øverst i lista. Valget huskes til neste gang.

## Lag og treningsgrupper

Treningstidene bruker ofte et fellesnavn, for eksempel «G16», mens gruppen spiller kamper som flere lag på fotball.no. Fanen **Lag** er stedet der lag opprettes og vedlikeholdes.

- **Nytt lag (admin):** navn, kjønn og årskull. Årskull er valgfritt og kan være flere fødselsår, for eksempel 2010 og 2011 for et G16-lag. Seniorlag (Herrer og Damer) har ikke årskull.
- **Trenere:** kryss av for hvilke trenere og Trener+ som har laget. En bruker kan ha flere lag, og det samme kan settes under Brukere.
- **Nytt navn:** endre navnet og lagre. Treninger, treningskamper, bookinger, forespørsler, brukere, koblingen til fotball.no og laglista oppdateres med en gang, så laget trenger ikke opprettes på nytt.
- **Bytt navn på flere lag:** brukes ved nyttår, når G10 blir G11. Skriv inn nye navn i lista og lagre alt på én gang. Navnebytte i kjede håndteres, så G16 → G17 går før G15 → G16. Ingenting endres automatisk ut fra årskull.
- **Slett laget:** fjerner laget fra lista, brukerne og koblingen. Lagets treninger slettes også, etter en ekstra bekreftelse.

Hvert lag kobles til lagene sine på fotball.no.

**Lag på fotball.no uten kobling (admin):** en liste med lag fra klubbene som gir forslag, som har hjemmekamper i år, men ikke er koblet til noe lag her. Lag som bare er med i turneringer eller spiller borte, er ikke med. Fra lista kan du **koble** laget til et eksisterende lag, med samme årsklasse foreslått først, eller **opprette** et nytt lag med navnet fra fotball.no. Lista er nyttig om våren, når fotball.no publiserer sesongens nye lag.

- **Koble lag:** admin kan koble alle grupper, Trener+ bare sine egne lag. Siden foreslår lag med samme årsklasse, gruppert per klubb.
- **Forslag per klubb:** i klubblista nederst krysser admin av hvilke klubber som skal gi forslag. En klubb som bare er hentet for enkelte kamper, kan slås av, så lagene dens ikke dukker opp.
- **Lag fra andre klubber**, for eksempel samarbeidslag, legges til på gruppen med **lag-ID** fra fotball.no. ID-en står i adressen til laget (`…/lag/hjem/?fiksId=4530`). Henteskriptet henter lagets kamper hver natt. Til da vises laget som «venter på henting». Admin kan også importere lagets Excel-fil for hånd.
- **Visning:** for valgt gruppe vises treninger, treningskamper og lagenes kamper, hjemme og borte, samlet per dato i fire uker om gangen.
- **Klubbenes kamper:** henteskriptet henter alle kampene til klubbene i lista nederst på siden hver natt. Kampene lagres samlet per klubb og måned i tabellen `lagkamper`. Admin kan også importere klubbens Excel-fil for hånd under «Hent fra fotball.no».
- **Filteret «Vis lagenes kamper»** i ukevisningen gjør to ting:
  - Det merker treninger der lagene har kamp et annet sted, eller samtidig på en annen del av banen. Har alle lagene i gruppen kamp, står det **«Trolig ledig»**. Har noen av dem kamp, står det **«Delvis borte»**.
  - Det lister ukens kamper for gruppene som trener på banen.

  Til bortekamper regnes det med en time før og etter for reise.

## Planlegging

Fanen **Planlegging** (bare for admin) er verktøyet for å sette opp standard treningstider. Siden er delt i tre nummererte steg, og stegene øverst viser hvor du er:

1. **Velg eller lag en mal.** En mal er én uke med treninger, som i treningsarket, og er ikke knyttet til noen uke.
2. **Mal inn treningene og lagre.**
3. **Kopier malen til uker.**

Du kan ha flere maler, for eksempel én for sommersesongen og én for vinteren.

**1. Velg eller lag en mal**

- Velg mal i lista, eller trykk **Ny tom mal**. **Lag kopi** lager en ny mal ut fra den du har oppe.
- **Hent inn plan fra uke** fyller malen med planen som ligger i en uke fra før.
- **Slett malen** fjerner bare malen. Ukene den er kopiert til, beholder treningene.

**2. Mal inn treningene og lagre**

- Hele uka vises nedover, mandag til søndag. Ukedagsknappene hopper til dagen.
  - Rutenettet har én rad per 30 minutter og én kolonne per kvarter (A–D) på hver bane, gruppert per anlegg. Baner uten kvarter vises som halvdeler eller hel bane.
  - Kryss av under «Vis baner» for hvilke baner som skal vises. Treninger på skjulte baner er likevel med i malen.
- Velg et lag og mal rutene laget skal ha. Klikk og dra for flere ruter, og klikk på en rute med samme lag for å viske den ut.
- Du kan bare male med lag som finnes på **Lag**-siden. Nye lag opprettes der. Har malen lag som ikke finnes der (for eksempel fra en import), får du beskjed, og de står med «?» i lista over økter.
- Faste treninger som ikke hører til planen, vises skravert.
- **Samme lag på flere baner samtidig** er lov, men gir et varsel under rutenettet med dag, tid og baner, og rutene får rød kant.
- **Samme lag med flere økter samme dag** (ikke sammenhengende, for eksempel 18:00–19:30 og 20:00–21:30) er også lov, men gir et varsel, uansett hvilke baner øktene er på.
- Gi malen et navn og trykk **Lagre malen**. Etterpå får du en knapp som tar deg til steg 3.

**3. Kopier malen til uker**

- Velg **Fra uke** og **Til uke**. Lista går fra starten av i fjor til slutten av neste år, og ukene kan gå over nyttår.
- Under «Hvilke uker» kan du velge bare partalls- eller bare oddetallsuker, for treninger annenhver uke.
- Teksten under viser hvilke uker malen blir kopiert til, for eksempel «9 uker: uke 47–53 2026 og uke 1–2 2027».
- Trykk **Kopier … til ukene**. Malen må være lagret først.
- Har noen av ukene allerede en plan, får du et varsel som viser hvilke uker det gjelder og hvilken mal de har. Du velger da **Overskriv** eller **Avbryt**.
- **Fjern planen i ukene** tar bort treningene fra planen i de valgte ukene. Du får spørsmål før noe fjernes.

**Økter per lag og planlagte uker**

Nederst på siden står to oversikter:

- **Økter per lag:** antall økter og timer per uke i malen, og hvilke dager. Sammenhengende tid samme dag regnes som én økt, også om laget bruker flere baner. Lag uten økter i malen står også med, så du ser om noen mangler.
- **Planlagte uker:** hvilke uker som har hvilken mal. Uker som er endret på annen måte, står som «Egen plan».

**Hva som røres**

- Bare treninger fra planen i de valgte ukene byttes ut. Andre faste treninger og enkelttreninger røres ikke.
- Kamper, treningskamper og bookinger røres aldri, uansett om de kommer fra fotball.no, er importert eller er lagt inn for hånd.
- En trening som kolliderer med en kamp eller booking, viker og faller bort den dagen. Etter kopieringen får du vite hvor mange treningsøkter som viker.
- Like treninger i flere uker blir én trening med en liste over uker. Treningstider-fanen viser den som for eksempel «Uke 14–43 2026».
- Avlysninger og merknader følger med når en trening får nye uker.
- Planer som ble laget med datoperiode før, gjøres om til ukenummer første gang en mal kopieres til et av årene de gjelder. Ukene ellers i året beholder de samme treningene.

**Import fra treningsarket:** velg Excel-fila under «Importer treningsark». Importen fyller malen som er oppe. Økter merket «annenhver» legges i malen hver uke. Skal de bare gjelde annenhver uke, lag en egen mal for dem og legg den inn med «Bare partallsuker» eller «Bare oddetallsuker». Lag som ikke finnes på Lag-siden, blir ikke lagt til automatisk. Opprett dem der, eller visk dem ut i malen. Se over hver dag og lagre malen etterpå.

- **Formatet:** én blokk per ukedag med kolonnene «Tid» og «BANEDEL A–D», og anleggsnavnet øverst.
- **Sammenslåtte celler:** gir flere kvarter.
- **Lagnavn:** skrivemåter som «G 19» og «G19» slås sammen.
- **Andre ark:** ark i et annet format, som hallen, hoppes over.

Trenere knyttes til ett eller flere lag under **Brukere**. Laglista vedlikeholdes samme sted, og siden foreslår lag ut fra hjemmelagene i kampene fra fotball.no.

## Gjesteanlegg (Hoopit)

Noen samarbeidslag trener på anlegg der en annen klubb fører banedagboken i Hoopit. Slike anlegg kan legges inn som **gjesteanlegg**. De vises i ukevisningen som de andre anleggene, med «(gjest)» etter navnet, men er bare til visning:

- Ingen kan legge inn treninger, bookinger, treningskamper eller forespørsler der, heller ikke admin. Databasen stopper det også.
- Treninger og andre aktiviteter hentes hver natt fra klubbens offentlige kalender i Hoopit. De vises skravert, og et klikk viser tid, bane, gruppe og kilde.
- Kampene hentes fra fotball.no, som for de andre anleggene. Kampene som Hoopit selv har hentet fra fotball.no, hoppes over, så ingen kamper vises to ganger.
- Samme økt registrert for flere grupper i Hoopit (for eksempel J15 og J17) vises som én blokk med begge gruppene.
- Hoopit-hendelser som overlapper, legges side om side. Det gis ikke kollisjonsvarsel for dem, siden det er den andre klubbens plan.
- Gjesteanlegg er ikke med i Planlegging, og kan ikke velges i skjemaene for treningstider og forespørsler.

**Aursmoen (Aurskog-Finstadbru SK)** er satt opp som gjesteanlegg med `supabase/gjesteanlegg_aursmoen.sql`:

| Anlegg | Bane | Hoopit bane-ID | Navn på fotball.no |
| --- | --- | --- | --- |
| Aursmoen (fotball.no 11991) | Kunstgress (9er A/B, 7er A–D) | 2263 | Aursmoen kunstgress … |
| | KG 2 (9er, 7er A/B) | 2264 | Aursmoen KG 2 9er, 7er A/B |
| | 5er | 2265 | Aursmoen mini kg |
| | Mini 3er-baner | 2558 | – |
| Aursmoen Sletta (fotball.no 17513) | 9er, 7er A, 7er B | 2847, 2848, 2849 | Aursmoen Sletta 9er, 7er A/B |

**Nytt gjesteanlegg:** legg til anlegget under **Baner** med anleggs-ID fra fotball.no. Kryss av for «Gjesteanlegg» og lim inn lenken til den offentlige Hoopit-kalenderen. Legg deretter inn Hoopit bane-ID på hver bane. Bane-ID-ene står i lenken til kalenderen (`venueId=`) når du velger én bane der. Neste natt hentes treningene.

Hoopit har ikke et offisielt, dokumentert grensesnitt for dette. Banedagboken bruker det samme som Hoopit sin egen offentlige kalenderside. Endrer Hoopit det, kan hentingen slutte å virke. Da står feilen i loggen under Actions, og resten av hentingen går som før.

## Oppsett med Supabase

Regn med rundt en halvtime. Du trenger en Supabase-konto (gratis), tilgang til dette GitHub-repoet og en konto hos Netlify eller Cloudflare (gratis) for publisering.

### 1. Opprett databasen

1. Gå til [supabase.com](https://supabase.com) og velg **New project**. Velg region **Stockholm (eu-north-1)**, så ligger dataene i EU.
2. Åpne **SQL Editor**, lim inn hele `supabase/schema.sql` og trykk **Run**.
3. Gjør det samme med `supabase/seed.sql`. Den legger inn Høland idrettsanlegg og Bjørkelangen kunstgress med delbaner. Kjør også `supabase/gjesteanlegg_aursmoen.sql` hvis Aursmoen skal være med som gjesteanlegg.
4. Legg inn den første admin. Bruk små bokstaver i e-postadressen, og kjør i SQL Editor:
   ```sql
   insert into public.brukere (id, data) values
     ('navn@eksempel.no', '{"epost": "navn@eksempel.no", "navn": "Banekoordinator", "rolle": "admin", "lag": []}');
   ```
   Flere admins og alle trenere legges deretter til fra nettsiden, under fanen **Brukere**. Databasen sørger for at det alltid finnes minst én admin.

### 2. Innlogging på e-post

1. Gå til **Authentication → URL Configuration**. Sett **Site URL** til adressen siden skal ligge på (se steg 4), og legg samme adresse inn under **Redirect URLs**.
2. **Viktig:** Supabase sin innebygde e-posttjeneste sender bare til medlemmer av Supabase-prosjektet, og bare noen få e-poster i timen. Før trenerne kan logge inn, må du koble til en egen e-posttjeneste under **Authentication → Emails → SMTP Settings**. Brevo og Resend har gratisnivå som holder for en klubb.

### 3. Automatisk henting fra fotball.no

1. I Supabase: åpne **Project Settings → API** og kopier **Project URL** og **service_role**-nøkkelen.
2. I GitHub-repoet: gå til **Settings → Secrets and variables → Actions → New repository secret** og legg inn:
   - `SUPABASE_URL`: Project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: service_role-nøkkelen. Den gir full tilgang til databasen og skal bare ligge her, aldri i nettsiden.
3. Arbeidsflyten `.github/workflows/hent-kamper.yml` kjører hver natt kl. 03:17 UTC. GitHub kjører bare planlagte arbeidsflyter fra hovedgrenen (`main`), så endringene må være slått sammen dit.
4. Første gang: åpne **Actions → Hent kamper fra fotball.no → Run workflow** og fyll inn hele sesongen, for eksempel `2026-01-01` til `2026-12-31`. Uten datoer henter den 60 dager tilbake og 365 dager fram.

Skriptet:

- henter Excel-eksporten for hvert anlegg som har fotball.no-ID
- legger inn nye kamper og oppdaterer flyttede kamper
- fjerner kamper som er strøket i perioden
- henter treninger og aktiviteter for gjesteanlegg fra Hoopit (se over)

Manuelle bookinger og treninger rører det aldri. Det samme gjelder delbane og varighet som er justert for hånd. Svikter nedlastingen for ett anlegg, blir ingenting slettet der.

Skriptet kan kjøres lokalt med `pip install openpyxl` og `python scripts/hent_kamper.py --tørrkjøring`, med de samme to miljøvariablene satt.

### 4. Publiser nettsiden

1. Åpne `banedagbok/index.html` og fyll inn øverst i skriptet:
   ```js
   window.BANEDAGBOK_SUPABASE = window.BANEDAGBOK_SUPABASE || { url: "https://<prosjekt>.supabase.co", anonKey: "<anon public-nøkkel>" };
   ```
   Bruk **anon public**-nøkkelen fra Project Settings → API. Den er laget for å ligge i nettsider, siden tilgangsreglene i databasen bestemmer hva den får gjøre.
2. Publiser mappa `banedagbok` med Netlify eller Cloudflare Pages. Repoet er privat, og GitHub Pages krever da betalt GitHub-konto.
   - **Netlify:** Add new site → Import from Git → velg repoet. Build command: tom. Publish directory: `banedagbok`.
   - **Cloudflare Pages:** Create → Pages → Connect to Git. Build command: tom. Build output directory: `banedagbok`.
3. Egen adresse som `baner.klubbnavn.no` settes opp hos Netlify eller Cloudflare. Husk å oppdatere Site URL i Supabase (steg 2).

## Drift

- **Ny admin eller trener:** en admin legger personen til under **Brukere** på nettsiden. Personen logger inn med e-postadressen sin.
- **Nytt anlegg:** en admin legger det inn under **Baner** på nettsiden, med anleggs-ID fra fotball.no. Neste natt hentes kampene.
- **Feil i hentingen:** GitHub sender e-post når en kjøring feiler. Loggen ligger under Actions.
- **Pause i gratisprosjekter:** Supabase pauser gratisprosjekter som ikke er brukt på en uke. Den nattlige hentingen bruker databasen hver dag.

## Personvern

Banedagboken skal bare inneholde lagnavn, tider og baner. Ikke skriv telefonnumre, navn på spillere eller annen personinformasjon i merknadsfeltene. Brukernes e-postadresser ligger i Supabase og vises bare for admins. Forespørsler vises bare for admins og den som sendte dem.
