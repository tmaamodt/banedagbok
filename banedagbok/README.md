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

**Kamp går foran trening.** Treningstidene settes opp først. En trening som overlapper en kamp (fra fotball.no eller treningskamp) på samme del av banen, viker:

- I uka vises den stiplet og overstreket.
- Den listes under «Kamp går foran», og regnes ikke som en kollisjon.

Rødt kollisjonsvarsel gis bare når to treninger, to kamper eller en booking krasjer.

## Planlegging

Fanen **Planlegging** (bare for admin) er verktøyet for å sette opp standard treningstider for en periode, på samme måte som i treningsarket.

1. Velg en periode fra–til, eller bruk et hurtigvalg som «Høstsesong».
2. Velg ukedag. Rutenettet har én rad per 30 minutter og én kolonne per kvarter (A–D) på hver bane, gruppert per anlegg. Baner uten kvarter vises som halvdeler eller hel bane.
3. Velg et lag og mal rutene laget skal ha. Klikk og dra for flere ruter, og klikk på en rute med samme lag for å viske den ut. Velg «Partallsuker» eller «Oddetallsuker» for treninger annenhver uke.
4. Kamper og bookinger i perioden vises med ⚽ og antall i rutene. Ruter der et lag kolliderer med kamper, får rød kant og listes i oppsummeringen.
5. Trykk **Lagre planen**:
   - Ruter som henger sammen blir én fast trening.
   - Et lag med A og B samtidig får halvdelen, og et lag med alle fire kvarterene får hele banen.
   - Bare treninger som tilhører samme plan blir erstattet. Andre faste treninger vises skravert og røres ikke.

**Import fra treningsarket:** velg Excel-fila under «Importer treningsark». Importen fyller rutenettet, og du ser over hver dag og lagrer etterpå.

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
