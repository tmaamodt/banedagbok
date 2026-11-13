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
| Besøkende (ikke innlogget) | Se ukevisning og kampliste. Merknader er skjult. |
| Trener | Slette faste treninger, enkelttreninger, treningskamper og bookinger for egne lag, og avlyse enkeltdager. Søke om banetid og om treningskamper. |
| Trener+ | Alt en trener kan, og i tillegg legge inn og endre enkelttreninger og treningskamper for egne lag. Faste treningstider må søkes om. |
| Admin | Alt: brukere og lag, faste treningstider, bookinger, anlegg, import, og godkjenne eller avslå forespørsler. |

Det finnes to typer treninger:

- **Fast hver uke:** en ukedag og en periode fra–til. Den stopper av seg selv når perioden er over, og har hurtigvalg for vår- og høstsesong.
- **Enkelttrening:** én dato.

Faste treningstider legges bare inn av admin, eller ved at admin godkjenner en forespørsel.

En forespørsel gjelder enten fast tid eller én dag. Trener+ søker bare om fast tid, siden enkelttreninger legges inn direkte. Både treneren og admin ser med en gang om tiden kolliderer med noe. Når admin godkjenner, blir forespørselen automatisk en treningstid, og treneren ser svaret under Forespørsler.

**Treningskamper** finnes ikke på fotball.no og legges inn i banedagboken av admin eller Trener+. En trener søker om treningskamp under Forespørsler, og den legges inn når admin godkjenner. De vises som kamper i lilla. Henteskriptet rører dem aldri.

**Kamp går foran trening.** Treningstidene settes opp først. En trening som overlapper en kamp eller booking på samme del av banen, viker. Det gjelder uansett hvordan kampen er lagt inn: fra fotball.no, importert, som treningskamp eller som booking for hånd.

- I uka vises den stiplet og overstreket.
- Den listes under «Kamp eller booking går foran», og regnes ikke som en kollisjon.

Rødt kollisjonsvarsel gis bare når to treninger krasjer, eller når kamper og bookinger krasjer med hverandre.

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

Fanen **Planlegging** (bare for admin) er verktøyet for å sette opp standard treningstider. Det gjøres i to steg: først lager du en **mal** for en hel uke, som i treningsarket, og så legger du malen inn i ukene den skal gjelde for. Du kan ha flere maler, for eksempel én for sommersesongen og én for vinteren.

**1. Lag en mal**

- Velg mal i lista, eller trykk **Ny tom mal**. **Lag kopi** lager en ny mal ut fra den du har oppe.
- **Hent inn plan fra uke** fyller malen med planen som ligger i en uke fra før.
- Hele uka vises nedover, mandag til søndag. Ukedagsknappene hopper til dagen.
  - Rutenettet har én rad per 30 minutter og én kolonne per kvarter (A–D) på hver bane, gruppert per anlegg. Baner uten kvarter vises som halvdeler eller hel bane.
  - Kryss av under «Vis baner» for hvilke baner som skal vises. Treninger på skjulte baner er likevel med i malen.
- Velg et lag og mal rutene laget skal ha. Klikk og dra for flere ruter, og klikk på en rute med samme lag for å viske den ut.
- Faste treninger som ikke hører til planen, vises skravert.
- Gi malen et navn og trykk **Lagre malen**. Malen er ikke knyttet til noen uke.
- **Slett malen** fjerner bare malen. Ukene den er lagt inn i, beholder treningene.

**2. Legg malen inn i uker**

- Velg **Fra uke** og **Til uke**. Lista går fra starten av i fjor til slutten av neste år, og ukene kan gå over nyttår.
- Under «Hvilke uker» kan du velge bare partalls- eller bare oddetallsuker, for treninger annenhver uke.
- Trykk **Legg … inn i ukene**. Malen må være lagret først.
- Har noen av ukene allerede en plan, får du et varsel som viser hvilke uker det gjelder og hvilken mal de har. Du velger da **Overskriv** eller **Avbryt**.
- **Fjern planen i ukene** tar bort treningene fra planen i de valgte ukene. Du får spørsmål før noe fjernes.
- **Planlagte uker** viser hvilke uker som har hvilken mal. Uker som er endret på annen måte, står som «Egen plan».

**Hva som røres**

- Bare treninger fra planen i de valgte ukene byttes ut. Andre faste treninger og enkelttreninger røres ikke.
- Kamper, treningskamper og bookinger røres aldri, uansett om de kommer fra fotball.no, er importert eller er lagt inn for hånd.
- En trening som kolliderer med en kamp eller booking, viker og faller bort den dagen. Etter at malen er lagt inn, får du vite hvor mange treningsøkter som viker.
- Like treninger i flere uker blir én trening med en liste over uker. Treningstider-fanen viser den som for eksempel «Uke 14–43 2026».
- Avlysninger og merknader følger med når en trening får nye uker.
- Planer som ble laget med datoperiode før, gjøres om til ukenummer første gang en mal legges inn i et av årene de gjelder. Ukene ellers i året beholder de samme treningene.

**Import fra treningsarket:** velg Excel-fila under «Importer treningsark». Importen fyller malen som er oppe. Økter merket «annenhver» legges i malen hver uke. Skal de bare gjelde annenhver uke, lag en egen mal for dem og legg den inn med «Bare partallsuker» eller «Bare oddetallsuker». Se over hver dag og lagre malen etterpå.

- **Formatet:** én blokk per ukedag med kolonnene «Tid» og «BANEDEL A–D», og anleggsnavnet øverst.
- **Sammenslåtte celler:** gir flere kvarter.
- **«annenhver»** blir partallsuker.
- **Lagnavn:** skrivemåter som «G 19» og «G19» slås sammen.
- **Andre ark:** ark i et annet format, som hallen, hoppes over.

Med «Kopier inn fra» kan forrige sesong brukes som utgangspunkt.

Trenere knyttes til ett eller flere lag under **Brukere**. Laglista vedlikeholdes samme sted, og siden foreslår lag ut fra hjemmelagene i kampene fra fotball.no.

## Oppsett med Supabase

Regn med rundt en halvtime. Du trenger en Supabase-konto (gratis), tilgang til dette GitHub-repoet og en konto hos Netlify eller Cloudflare (gratis) for publisering.

### 1. Opprett databasen

1. Gå til [supabase.com](https://supabase.com) og velg **New project**. Velg region **Stockholm (eu-north-1)**, så ligger dataene i EU.
2. Åpne **SQL Editor**, lim inn hele `supabase/schema.sql` og trykk **Run**.
3. Gjør det samme med `supabase/seed.sql`. Den legger inn Høland idrettsanlegg og Bjørkelangen kunstgress med delbaner.
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
