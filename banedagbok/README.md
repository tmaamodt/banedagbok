# Banedagbok

Nettside som viser kamper fra fotball.no og faste treningstider på klubbens baner, med varsel når to aktiviteter bruker samme del av banen samtidig.

Siden er én fil (`index.html`) og har tre lagringsmåter. Den velger selv:

| Når | Lagring |
|---|---|
| Supabase-adresse og nøkkel er fylt inn i `index.html` | Delt database i Supabase. Alle kan se, innloggede redaktører kan endre. Kamper hentes automatisk hver natt. |
| Siden er publisert som Claude-artefakt | Delt lagring i artefakten |
| Ellers (fila åpnet direkte) | Bare i nettleseren på denne maskinen |

## Oppsett med Supabase

Regn med rundt en halvtime. Du trenger en Supabase-konto (gratis), tilgang til dette GitHub-repoet og en konto hos Netlify eller Cloudflare (gratis) for publisering.

### 1. Opprett databasen

1. Gå til [supabase.com](https://supabase.com) og velg **New project**. Velg region **Stockholm (eu-north-1)**, så ligger dataene i EU.
2. Åpne **SQL Editor**, lim inn hele `supabase/schema.sql` og trykk **Run**.
3. Gjør det samme med `supabase/seed.sql`. Den legger inn Høland idrettsanlegg og Bjørkelangen kunstgress med delbaner.
4. Legg inn redaktørene, altså de som skal kunne endre. Kjør én linje per person i SQL Editor:
   ```sql
   insert into public.redaktorer (epost, navn) values ('navn@eksempel.no', 'Banekoordinator');
   ```
   Redaktører fjernes med `delete from public.redaktorer where epost = 'navn@eksempel.no';`.

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

- **Ny redaktør:** legg til e-postadressen i tabellen `redaktorer`, som i steg 1.
- **Nytt anlegg:** en redaktør legger det inn under **Baner** på nettsiden, med anleggs-ID fra fotball.no. Neste natt hentes kampene.
- **Feil i hentingen:** GitHub sender e-post når en kjøring feiler. Loggen ligger under Actions.
- **Pause i gratisprosjekter:** Supabase pauser gratisprosjekter som ikke er brukt på en uke. Den nattlige hentingen bruker databasen hver dag.

## Personvern

Banedagboken skal bare inneholde lagnavn, tider og baner. Ikke skriv telefonnumre, navn på spillere eller annen personinformasjon i merknadsfeltene. Redaktørenes e-postadresser ligger i Supabase og vises ikke for andre.
