# Bordoversikt

En enkel app for én iPad i liggende format. Kelnerne trykker på et bord når de har vært innom,
og appen viser hvor mange minutter det er siden hvert bord fikk besøk.

Ren HTML/CSS/JavaScript, ingen server. All data lagres i iPadens nettleser (localStorage),
og appen virker uten nett etter første åpning.

## Bruk

| Handling | Hva skjer |
| --- | --- |
| **Trykk** på et bord | «Besøkt nå»: tiden nullstilles. Et ledig bord blir samtidig opptatt. En melding med **Angre** vises i 5 sekunder. |
| **Hold** på et bord (ca. et halvt sekund) | Meny: Besøkt nå, Sett ledig / Sett opptatt, Angre siste trykk |
| Farger | Grønn under 10 min, gul 10–20 min, rød over 20 min (rød pulserer). Grå = ledig, teller ikke tid. |
| Topplinja | Klokke, hvor mange bord som er opptatt og hvor mange som er røde, og fargeforklaring. ☀︎ betyr at skjermen holdes våken. |

Tiden oppdateres automatisk hvert minutt.

### Redigeringsmodus

Trykk **Rediger** øverst til høyre og skriv PIN-koden. **Standard PIN er `1234`**. Bytt den under Innstillinger.

- **＋ Nytt bord**: legger til et bord med neste ledige nummer
- **Dra** et bord for å flytte det
- **Trykk** på et bord for å gi det nytt navn, velge rundt eller firkantet, endre størrelse eller fjerne det
- **Innstillinger**: når bordene blir gule og røde, bytt PIN, og **Nullstill dagen** (alle bord blir ledige, plantegningen beholdes)
- **Ferdig**: tilbake til vanlig visning

## Publisering

### Alternativ A: GitHub Pages (allerede satt opp i dette repoet)

Arbeidsflyten `.github/workflows/publiser-nettsiden.yml` publiserer appen under `/bordoversikt/` hver gang
den endres på `main`. Adressen blir:

```
https://<github-brukernavn>.github.io/<repo-navn>/bordoversikt/
```

Hvis Pages ikke allerede er slått på: **Settings → Pages → Source: «GitHub Actions»**.

### Alternativ B: Netlify Drop (uten GitHub)

1. Gå til <https://app.netlify.com/drop> og lag en gratis konto.
2. Dra hele mappa `bordoversikt` inn på siden.
3. Du får en adresse som `https://noe-tilfeldig.netlify.app`. Den kan endres under *Site settings*.

Appen må ligge på **https** for at service worker (offline) og «hold skjermen våken» skal virke. Begge alternativene gir https.

## Legg appen til på iPadens hjemskjerm

1. Åpne adressen i **Safari** på iPaden.
2. Trykk på **Del**-knappen (firkant med pil opp) øverst til høyre.
3. Velg **Legg til på Hjem-skjerm**, gi den et navn (f.eks. «Bord») og trykk **Legg til**.
4. Åpne appen fra ikonet på hjemskjermen. Den starter i fullskjerm uten adressefelt.
5. Trykk én gang på skjermen etter at appen er åpnet, så slås «hold skjermen våken» på (☀︎ vises øverst).

Tips for iPaden:

- **Innstillinger → Skjerm og lysstyrke → Autolås → Aldri**: ekstra sikring mot at skjermen slukker.
- **Innstillinger → Tilgjengelighet → Guidet tilgang**: låser iPaden til denne appen, så ingen går ut av den ved et uhell.
- Ha iPaden på lader.

Merk: Data lagres i appen på hjemskjermen, ikke i Safari. Plantegningen lages derfor i appen etter at den er lagt
til på hjemskjermen. Hvis appen slettes fra hjemskjermen, forsvinner plantegningen.

### Oppdatere appen

Når filene endres, øk `VERSJON` i `sw.js` (f.eks. `bordoversikt-v2`). iPaden henter den nye versjonen
neste gang appen åpnes med nett. Plantegning og innstillinger beholdes.
