#!/usr/bin/env python3
"""Henter kampoppsett fra fotball.no for alle anlegg i banedagboken og oppdaterer Supabase.

Kjøres hver natt av GitHub Actions (.github/workflows/hent-kamper.yml), men kan også kjøres lokalt:

    pip install openpyxl
    export SUPABASE_URL=https://<prosjekt>.supabase.co
    export SUPABASE_SERVICE_ROLE_KEY=<service_role-nøkkel>
    python scripts/hent_kamper.py                 # standard periode: 60 dager tilbake, 365 dager fram
    python scripts/hent_kamper.py --fra 2026-01-01 --til 2026-12-31
    python scripts/hent_kamper.py --tørrkjøring   # vis hva som ville blitt endret, uten å skrive

Hva skriptet gjør:
  1. Leser oppsettet (anlegg med fotball.no-ID og delbaner) fra tabellen config.
  2. Laster ned Excel-eksporten for hvert anlegg fra fotball.no for perioden.
  3. Kobler hver kamp til en delbane via «Navn på fotball.no». Ukjente baner får en
     ny delbane med plass gjettet fra navnet (f.eks. «kg 7er B» → 7er B).
  4. Lagrer nye og endrede kamper. Delbane og varighet som noen har endret for hånd beholdes.
  5. Sletter kamper fra fotball.no i perioden som ikke lenger finnes i eksporten
     (flyttet til et anlegg vi ikke følger, eller strøket). Manuelle bookinger røres aldri.
  6. Henter alle kampene (også bortekamper) for klubbene i oppsettet (config.klubber) og lagrer
     dem samlet per klubb og måned i tabellen lagkamper. Brukes av treningsgruppene og til å
     se om et lag har kamp et annet sted i treningstiden.
  8. Henter dommere fra kampsidene på fotball.no for kommende kamper på egne anlegg, og lagrer
     dem på kampen med rolle og navn (åpen informasjon på fotball.no).
  7. Henter treninger og bookinger for gjesteanlegg fra Hoopit (anlegg med gjest = true og en
     Hoopit-kalender, baner med Hoopit-bane-ID) og lagrer dem per bane og måned i tabellen gjest.
     Kampene som Hoopit har hentet fra fotball.no, hoppes over: de kommer fra fotball.no i punkt 2.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import openpyxl

FOTBALL_NO = "https://www.fotball.no/footballapi/Calendar/DownloadArenaExcelCalendar"
USER_AGENT = "banedagbok-kamphenter/1.0"


# ---------------------------------------------------------------- Supabase (PostgREST)
class Supabase:
    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _req(self, method: str, path: str, body=None, extra_headers=None):
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={**self.headers, **(extra_headers or {})})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")
                if e.code >= 500 and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise SystemExit(f"Supabase svarte {e.code} på {method} {path}: {msg}")
            except urllib.error.URLError as e:
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise SystemExit(f"Får ikke kontakt med Supabase: {e}")

    def get_all(self, table: str, query: str):
        rows, offset, page = [], 0, 1000
        while True:
            batch = self._req("GET", f"/{table}?{query}&limit={page}&offset={offset}")
            rows += batch
            if len(batch) < page:
                return rows
            offset += page

    def upsert(self, table: str, rows: list[dict]):
        for i in range(0, len(rows), 200):
            self._req("POST", f"/{table}?on_conflict=id", rows[i:i + 200],
                      {"Prefer": "resolution=merge-duplicates,return=minimal"})

    def delete_ids(self, table: str, ids: list[str]):
        for i in range(0, len(ids), 100):
            chunk = ",".join(f'"{x}"' for x in ids[i:i + 100])
            self._req("DELETE", f"/{table}?id=in.({urllib.parse.quote(chunk, safe=',')})", extra_headers={"Prefer": "return=minimal"})


# ---------------------------------------------------------------- fotball.no
FOTBALL_NO_KLUBB = "https://www.fotball.no/footballapi/Calendar/DownloadClubExcelCalendar"


FOTBALL_NO_LAG = "https://www.fotball.no/footballapi/Calendar/DownloadTeamExcelCalendar"


def last_ned_excel(fiks_id: str, navn: str, fra: dt.date, til: dt.date, klubb: bool = False, lag: bool = False) -> bytes:
    nokkel, url = ("teamId", FOTBALL_NO_LAG) if lag else ("clubId", FOTBALL_NO_KLUBB) if klubb else ("stadiumId", FOTBALL_NO)
    qs = urllib.parse.urlencode({nokkel: fiks_id, "heading": f"Kamper for {navn}",
                                 "fromDate": fra.isoformat(), "toDate": til.isoformat()})
    req = urllib.request.Request(f"{url}?{qs}", headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 3:
                raise
            print(f"  fotball.no svarte ikke ({e}), prøver igjen …")
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def _tid(v) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, dt.time):
        return f"{v.hour:02d}:{v.minute:02d}"
    if isinstance(v, (int, float)) and 0 <= v < 1:
        m = round(v * 1440)
        return f"{m // 60:02d}:{m % 60:02d}"
    m = re.search(r"(\d{1,2})[:.](\d{2})", str(v))
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def _dato(v) -> tuple[str | None, str | None]:
    if isinstance(v, dt.datetime):
        return v.date().isoformat(), (f"{v.hour:02d}:{v.minute:02d}" if v.hour or v.minute else None)
    if isinstance(v, dt.date):
        return v.isoformat(), None
    s = str(v or "").strip()
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}[:.]\d{2}))?", s)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}", _tid(m.group(4))
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return (m.group(0), None) if m else (None, None)


def les_kamper(xlsx: bytes) -> list[dict]:
    """Leser fotball.no sin Excel-eksport. Kolonnene finnes via overskriftene, ikke posisjon."""
    if not xlsx.startswith(b"PK"):
        raise ValueError("fotball.no returnerte ikke en Excel-fil")
    ws = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hi = next((i for i, r in enumerate(rows) if r and any(str(c or "").strip().lower() == "dato" for c in r)
               and any("hjemme" in str(c or "").lower() for c in r)), None)
    if hi is None:
        raise ValueError("fant ikke kolonnene Dato og Hjemmelag i eksporten")
    head = [str(c or "").strip().lower() for c in rows[hi]]

    def col(pattern):
        return next((i for i, h in enumerate(head) if re.search(pattern, h)), -1)

    c = {"dato": col(r"^dato"), "tid": col(r"^(tid|avspark|klokkeslett)"), "hjemme": col(r"hjemme"),
         "borte": col(r"borte"), "bane": col(r"^(bane|arena|spillested)"), "turn": col(r"(turnering|serie|konkurranse)"),
         "nr": col(r"kamp ?n(umme)?r"), "sf": col(r"spillform"), "res": col(r"resultat"), "runde": col(r"runde")}

    def g(r, k):
        i = c[k]
        return str(r[i]).strip() if i >= 0 and i < len(r) and r[i] is not None else ""

    out = []
    for r in rows[hi + 1:]:
        if not r:
            continue
        dato, tid_fra_dato = _dato(r[c["dato"]] if c["dato"] < len(r) else None)
        tid = (_tid(r[c["tid"]]) if 0 <= c["tid"] < len(r) else None) or tid_fra_dato
        if not dato or not tid:
            continue
        out.append({"dato": dato, "tid": tid, "hjemmelag": g(r, "hjemme"), "bortelag": g(r, "borte"),
                    "baneNavn": g(r, "bane"), "turnering": g(r, "turn"), "kampnr": g(r, "nr"),
                    "spillform": g(r, "sf"), "resultat": g(r, "res"), "runde": g(r, "runde")})
    return out


# ---------------------------------------------------------------- domene (samme regler som nettsiden)
def gjett_delbane(navn: str) -> dict:
    """Plassering på banen i tolvdeler. Banen er fire kvarter à 3: 9er = halvdel, 7er og 5er = kvarter.
    «5er A–H» ligger to per kvarter (A,B → 1. kvarter, C,D → 2. …), slik kampdataene fra fotball.no viser."""
    m = re.search(r"(\d{1,2})\s*er\s*([A-L])\b", navn, re.I)
    if m:
        size, idx = int(m.group(1)), ord(m.group(2).upper()) - 65
        if size >= 9:
            return {"start": min(1, idx) * 6, "bredde": 6}
        if size >= 7:
            return {"start": min(3, idx) * 3, "bredde": 3}
        return {"start": min(3, idx // (2 if size >= 5 else 3)) * 3, "bredde": 3}
    return {"start": 0, "bredde": 12}


def ny_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6)}"


def kamp_id(k: dict) -> str:
    base = k["kampnr"] or f'{k["dato"]}-{k["tid"]}-{k["hjemmelag"]}-{k["bortelag"]}'
    return "k-" + re.sub(r"[^a-zA-Z0-9_.~:@+-]", "", base)[:120]


def normaliser_anlegg(a: dict) -> dict:
    """Samme regel som nettsiden: eldre oppsett uten `baner` blir én bane med alle deler aktive."""
    a.setdefault("delbaner", [])
    if not a.get("baner"):
        a["baner"] = [{"id": "b-1", "navn": "Kunstgress" if a.get("fiksId") else "Hovedbane", "underlag": "kunstgress",
                       "storrelse": "11", "kobling": "fotball.no" if a.get("fiksId") else "fri"}]
    for d in a["delbaner"]:
        d.setdefault("baneId", a["baner"][0]["id"])
        d.setdefault("aktiv", True)
        d.setdefault("alias", [])
    return a


def velg_bane(anlegg: dict, banenavn: str) -> dict | None:
    """Banen der et kjent fotball.no-navn, uten størrelse og del til slutt, er starten på banenavnet.
    F.eks. går «Aursmoen KG 2 5er B» til banen som har «Aursmoen KG 2 9er». Lengste treff vinner."""
    n, best, lengde = banenavn.strip().lower(), None, 0
    for d in anlegg.get("delbaner", []):
        for al in d.get("alias", []):
            al = al.strip().lower()
            # sammenlign uten siste ord (størrelse og del, f.eks. «9er», «7er A»)
            stamme = re.sub(r"\s+(\d+er|kg)(\s+[a-d]\d?)?$", "", al)
            if stamme and n.startswith(stamme) and len(stamme) > lengde:
                best, lengde = d.get("baneId"), len(stamme)
    return next((b for b in anlegg.get("baner", []) if b["id"] == best), None)


def finn_delbane(cfg: dict, anlegg: dict, banenavn: str) -> tuple[dict, dict, bool]:
    """Returnerer (anlegg, delbane, oppsett_endret). Søker etter koblingen i alle anlegg.
    Ukjente baner kobles til riktig del av anleggets første bane som er knyttet til fotball.no,
    eller til hele den banen hvis delen ikke finnes (slått av)."""
    n = banenavn.strip().lower()
    for a in cfg["anlegg"]:
        for d in a.get("delbaner", []):
            if any(x.strip().lower() == n for x in d.get("alias", [])):
                return a, d, False
    normaliser_anlegg(anlegg)
    bane = velg_bane(anlegg, banenavn) or next((b for b in anlegg["baner"] if b.get("kobling") == "fotball.no"), anlegg["baner"][0])
    g = gjett_delbane(banenavn)
    deler = [x for x in anlegg["delbaner"] if x["baneId"] == bane["id"]]
    d = next((x for x in deler if x["start"] == g["start"] and x["bredde"] == g["bredde"] and x.get("aktiv", True)), None) \
        or next((x for x in deler if x["bredde"] == 12), None)
    if d is None:
        d = {"id": ny_id("d"), "baneId": bane["id"], "navn": "Hele banen", "start": 0, "bredde": 12, "alias": [], "aktiv": True}
        anlegg["delbaner"].append(d)
    d["alias"] = sorted(set(d.get("alias", [])) | {banenavn})
    return anlegg, d, True


# ---------------------------------------------------------------- hovedløp
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--fra", type=dt.date.fromisoformat, help="første dato (YYYY-MM-DD)")
    p.add_argument("--til", type=dt.date.fromisoformat, help="siste dato (YYYY-MM-DD)")
    p.add_argument("--tørrkjøring", "--dry-run", dest="dry", action="store_true", help="ikke skriv til databasen")
    args = p.parse_args()

    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Mangler SUPABASE_URL eller SUPABASE_SERVICE_ROLE_KEY.", file=sys.stderr)
        return 2
    idag = dt.date.today()
    fra = args.fra or idag - dt.timedelta(days=60)
    til = args.til or idag + dt.timedelta(days=365)
    if til < fra:
        print("--til må være etter --fra.", file=sys.stderr)
        return 2
    print(f"Periode: {fra} – {til}{' (tørrkjøring)' if args.dry else ''}")

    db = Supabase(url, key)
    rader = db.get_all("config", "select=id,data&id=eq.oppsett")
    if not rader:
        print("Fant ikke oppsettet (config/oppsett). Kjør supabase/seed.sql eller legg til et anlegg på nettsiden først.", file=sys.stderr)
        return 1
    cfg = rader[0]["data"]
    original_cfg = json.dumps(cfg, sort_keys=True)

    hentet: dict[str, dict] = {}
    fullstendig: set[str] = set()   # anlegg der nedlastingen gikk bra og ga kamper (trygt å rydde)
    feil = 0
    for a in list(cfg.get("anlegg", [])):
        fiks = str(a.get("fiksId") or "").strip()
        if not fiks:
            print(f"- {a['navn']}: mangler fotball.no-ID, hopper over")
            continue
        try:
            kamper = les_kamper(last_ned_excel(fiks, a["navn"], fra, til))
        except Exception as e:  # noqa: BLE001 – ett anlegg som feiler skal ikke stoppe de andre
            print(f"- {a['navn']} ({fiks}): FEIL ved henting: {e}")
            feil += 1
            continue
        print(f"- {a['navn']} ({fiks}): {len(kamper)} kamper")
        if kamper:
            fullstendig.add(a["id"])
        for k in kamper:
            an, d, _ = finn_delbane(cfg, a, k["baneNavn"])
            hentet[kamp_id(k)] = {**k, "kilde": "fotball.no", "anleggId": an["id"], "delbaneId": d["id"]}

    eksisterende = {r["id"]: r["data"] for r in db.get_all(
        "kamper", f"select=id,data&kilde=eq.fotball.no&dato=gte.{fra.isoformat()}&dato=lte.{til.isoformat()}")}
    # Kamper som er hentet men lå utenfor perioden i databasen (f.eks. flyttet dato) slås opp enkeltvis
    mangler = [i for i in hentet if i not in eksisterende]
    for i in range(0, len(mangler), 100):
        chunk = ",".join(f'"{x}"' for x in mangler[i:i + 100])
        for r in db.get_all("kamper", f"select=id,data&id=in.({urllib.parse.quote(chunk, safe=',')})"):
            eksisterende[r["id"]] = r["data"]

    endringer = []
    for kid, ny in hentet.items():
        gammel = eksisterende.get(kid)
        doc = dict(ny)
        doc["varighet"] = (gammel or {}).get("varighet") or 0
        if gammel and gammel.get("delbaneManuell"):
            doc["delbaneId"], doc["delbaneManuell"] = gammel["delbaneId"], True
        if gammel and gammel.get("dommere") is not None:  # hentes i eget steg (hent_dommere)
            doc["dommere"] = gammel["dommere"]
        if gammel != doc:
            endringer.append({"id": kid, "data": doc})

    slett = [kid for kid, k in eksisterende.items()
             if kid not in hentet and k.get("kilde", "fotball.no") == "fotball.no"
             and k.get("anleggId") in fullstendig and fra.isoformat() <= k.get("dato", "") <= til.isoformat()]

    cfg_endret = json.dumps(cfg, sort_keys=True) != original_cfg
    nye = sum(1 for e in endringer if e["id"] not in eksisterende)
    print(f"Resultat: {nye} nye, {len(endringer) - nye} endret, {len(slett)} fjernet, "
          f"{len(hentet) - len(endringer)} uendret{', nye baner fra fotball.no koblet i oppsettet' if cfg_endret else ''}")
    for kid in slett:
        k = eksisterende[kid]
        print(f"  fjernes: {k.get('dato')} {k.get('tid')} {k.get('hjemmelag')} – {k.get('bortelag')}")

    if not args.dry:
        if cfg_endret:
            db.upsert("config", [{"id": "oppsett", "data": cfg}])
        if endringer:
            db.upsert("kamper", endringer)
        if slett:
            db.delete_ids("kamper", slett)
        print("Lagret.")

    feil += hent_lagkamper(db, cfg, fra, til, args.dry)
    feil += hent_hoopit(db, cfg, fra, til, args.dry)
    feil += hent_dommere(db, cfg, args.dry)
    return 1 if feil else 0


# ---------------------------------------------------------------- klubbenes kamper (også borte)
def klasse(turnering: str) -> str:
    """Årsklasse fra turneringsnavnet: «G16 2. div» → G16, «G08 avd. 9» → G8, ellers Herrer/Damer."""
    m = re.match(r"\s*([GJ])\s?0?(\d{1,2})\b", turnering or "", re.I)
    if m:
        return m.group(1).upper() + m.group(2)
    return "Damer" if re.search(r"kvinne|dame|jente", turnering or "", re.I) else "Herrer"


def vare_lag(kamper: list[dict]) -> str:
    """Klubbens lagnavn-prefiks er det første ordet som går igjen i (nesten) alle kampene, f.eks. «Bjørkelangen»."""
    from collections import Counter
    c = Counter()
    for k in kamper:
        for side in {k["hjemmelag"].split(" ")[0], k["bortelag"].split(" ")[0]}:
            if side:
                c[side] += 1
    return c.most_common(1)[0][0] if c else ""


def hent_lagkamper(db: Supabase, cfg: dict, fra: dt.date, til: dt.date, dry: bool) -> int:
    klubber = cfg.get("klubber") or []
    # lag som er lagt til med lag-ID på en treningsgruppe (f.eks. samarbeidslag fra en annen klubb)
    lag_ider = sorted({str(i) for r in db.get_all("grupper", "select=id,data") for i in (r["data"].get("lagIder") or []) if str(i).isdigit()})
    if not klubber and not lag_ider:
        return 0
    fra_m, til_m = fra.replace(day=1), (til.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    maneder = []
    d = fra_m
    while d <= til_m:
        maneder.append(d.strftime("%Y-%m"))
        d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    rader, feil = [], 0
    for kl in klubber:
        kid = str(kl.get("fiksId") or "").strip()
        if not kid:
            continue
        try:
            kamper = les_kamper(last_ned_excel(kid, kl.get("navn", kid), fra_m, til_m, klubb=True))
        except Exception as e:  # noqa: BLE001
            print(f"- klubb {kl.get('navn', kid)} ({kid}): FEIL ved henting: {e}")
            feil += 1
            continue
        pre = vare_lag(kamper)
        per_mnd = {m: [] for m in maneder}
        for k in kamper:
            vare = [{"lag": f"{klasse(k['turnering'])} {navn}", "hjemme": side == "h"}
                    for side, navn in (("h", k["hjemmelag"]), ("b", k["bortelag"])) if pre and navn.startswith(pre)]
            if k["dato"][:7] in per_mnd:
                per_mnd[k["dato"][:7]].append({"kampnr": k["kampnr"], "dato": k["dato"], "tid": k["tid"], "hjem": k["hjemmelag"],
                                               "borte": k["bortelag"], "bane": k["baneNavn"], "turnering": k["turnering"],
                                               "spillform": k["spillform"], "resultat": k["resultat"], "vare": vare})
        print(f"- klubb {kl.get('navn', kid)} ({kid}): {len(kamper)} kamper, lagnavn «{pre}»")
        rader += [{"id": f"{kid}-{m}", "data": {"klubbId": kid, "klubb": kl.get("navn", ""), "maned": m, "kamper": v}} for m, v in per_mnd.items()]
    for lid in lag_ider:
        try:
            kamper = les_kamper(last_ned_excel(lid, f"lag {lid}", fra_m, til_m, lag=True))
        except Exception as e:  # noqa: BLE001
            print(f"- lag {lid}: FEIL ved henting: {e}")
            feil += 1
            continue
        from collections import Counter
        navn = (Counter(n for k in kamper for n in {k["hjemmelag"], k["bortelag"]} if n).most_common(1) or [("", 0)])[0][0]
        per_mnd = {m: [] for m in maneder}
        for k in kamper:
            vare = [{"lag": f"{klasse(k['turnering'])} {n}", "hjemme": side == "h"}
                    for side, n in (("h", k["hjemmelag"]), ("b", k["bortelag"])) if navn and n == navn]
            if k["dato"][:7] in per_mnd:
                per_mnd[k["dato"][:7]].append({"kampnr": k["kampnr"], "dato": k["dato"], "tid": k["tid"], "hjem": k["hjemmelag"],
                                               "borte": k["bortelag"], "bane": k["baneNavn"], "turnering": k["turnering"],
                                               "spillform": k["spillform"], "resultat": k["resultat"], "vare": vare})
        print(f"- lag {lid}: {len(kamper)} kamper, lagnavn «{navn}»")
        rader += [{"id": f"lag{lid}-{m}", "data": {"lagId": lid, "klubb": navn, "maned": m, "kamper": v}} for m, v in per_mnd.items()]
    if rader and not dry:
        db.upsert("lagkamper", rader)
        print(f"Lagkamper lagret: {len(rader)} klubb-måneder.")
    return feil


# ---------------------------------------------------------------- dommere fra fotball.no
FOTBALL_NO_SIDE = "https://www.fotball.no/fotballdata"


def hent_side(sti: str) -> str:
    req = urllib.request.Request(f"{FOTBALL_NO_SIDE}/{sti}", headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def les_dommere(side: str) -> list[dict]:
    """Dommerfanen på kampsiden: rader med rolle, navn og klubb."""
    import html as _html
    m = re.search(r'data-tab="dommere".*?<table[^>]*>(.*?)</table>', side, re.S)
    if not m:
        return []
    ut = []
    for rad in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
        celler = [_html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", rad, re.S)]
        if len(celler) >= 2 and celler[1]:
            ut.append({"rolle": celler[0] or "Dommer", "navn": celler[1]})  # åpen informasjon på fotball.no
    return ut


def hent_dommere(db: Supabase, cfg: dict, dry: bool, dager_bak: int = 3, dager_fram: int = 28) -> int:
    """Dommere for kommende kamper fra fotball.no på egne anlegg (ikke gjesteanlegg).
    Kampnummeret kobles til kampsiden via lagsidene til klubbene i oppsettet (og lag lagt til med lag-ID)."""
    idag = dt.date.today()
    egne = {a["id"] for a in cfg.get("anlegg", []) if not a.get("gjest")}
    kamper = db.get_all("kamper", f"select=id,data&kilde=eq.fotball.no&dato=gte.{(idag - dt.timedelta(days=dager_bak)).isoformat()}"
                                  f"&dato=lte.{(idag + dt.timedelta(days=dager_fram)).isoformat()}")
    trenger = {r["data"]["kampnr"]: r for r in kamper if r["data"].get("kampnr") and r["data"].get("anleggId") in egne}
    if not trenger:
        return 0
    lag = set()
    for kl in cfg.get("klubber") or []:
        kid = str(kl.get("fiksId") or "").strip()
        if not kid:
            continue
        try:
            lag |= set(re.findall(r"lag/hjem/\?fiksId=(\d+)", hent_side(f"klubb/hjem/?fiksId={kid}")))
        except Exception as e:  # noqa: BLE001
            print(f"- dommere: klubbsiden {kid} feilet: {e}")
    lag |= {str(i) for r in db.get_all("grupper", "select=id,data") for i in (r["data"].get("lagIder") or []) if str(i).isdigit()}
    kampside: dict[str, str] = {}
    for lid in sorted(lag):
        if len(kampside) == len(trenger):
            break
        try:
            side = hent_side(f"lag/hjem/?fiksId={lid}")
        except Exception as e:  # noqa: BLE001
            print(f"- dommere: lagsiden {lid} feilet: {e}")
            continue
        for rad in re.findall(r"<tr[^>]*>(.*?)</tr>", side, re.S):
            fid = re.search(r"kamp/\?fiksId=(\d+)", rad)
            nr = re.search(r">\s*(\d{9,12})\s*<", rad)
            if fid and nr and nr.group(1) in trenger:
                kampside[nr.group(1)] = fid.group(1)
        time.sleep(0.3)
    endret, feil = [], 0
    for nr, rad in trenger.items():
        if nr not in kampside:
            continue
        try:
            dommere = les_dommere(hent_side(f"kamp/?fiksId={kampside[nr]}"))
        except Exception as e:  # noqa: BLE001
            print(f"- dommere: kamp {nr} feilet: {e}")
            feil += 1
            continue
        if rad["data"].get("dommere") != dommere:
            endret.append({"id": rad["id"], "data": {**rad["data"], "dommere": dommere}})
        time.sleep(0.3)
    print(f"Dommere: {len(trenger)} kommende kamper, {len(kampside)} funnet på fotball.no, "
          f"{sum(1 for e in endret if e['data']['dommere'])} med dommer fra kretsen, {len(endret)} endret.")
    if endret and not dry:
        db.upsert("kamper", endret)
    return 1 if feil else 0


# ---------------------------------------------------------------- gjesteanlegg fra Hoopit
HOOPIT_API = "https://api.hoopit.io/web/organizations/public-calendars"
HOOPIT_TYPE = {"training": "trening", "match": "kamp"}


def hoopit_hendelser(kalender: str, venue: int, fra: dt.date, til: dt.date) -> list[dict]:
    """Hendelser for én bane i Hoopit sin offentlige kalender. Til-datoen tas med."""
    qs = urllib.parse.urlencode({"from_date": fra.isoformat(), "to_date": (til + dt.timedelta(days=1)).isoformat()})
    req = urllib.request.Request(f"{HOOPIT_API}/{urllib.parse.quote(kalender)}/venues/{int(venue)}/?{qs}",
                                 headers={"User-Agent": USER_AGENT, "Accept": "application/json; version=3"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 3:
                raise
            print(f"  Hoopit svarte ikke ({e}), prøver igjen …")
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def hoopit_rad(e: dict) -> dict | None:
    """Gjør en Hoopit-hendelse om til det banedagboken trenger. Kamper fra fotball.no hoppes over."""
    if e.get("import_source") == "fotballdata" or e.get("has_fotballdata_match"):
        return None
    start, slutt = e.get("start") or "", e.get("end") or ""
    if len(start) < 16:
        return None
    sek = e.get("section") or {}
    return {"id": e.get("id"), "dato": start[:10], "fra": start[11:16],
            "til": slutt[11:16] if slutt[:10] == start[:10] and len(slutt) >= 16 else "23:59",
            "tittel": (e.get("title") or "").strip(), "gruppe": ((e.get("group") or {}).get("name") or "").strip(),
            "type": HOOPIT_TYPE.get(e.get("event_type"), "annet"), "del": sek.get("part"), "seksjon": sek.get("name") or "",
            "avlyst": bool(e.get("cancelled"))}


def hent_hoopit(db: Supabase, cfg: dict, fra: dt.date, til: dt.date, dry: bool) -> int:
    baner = [(a, b) for a in cfg.get("anlegg", []) if a.get("gjest") and (a.get("hoopit") or {}).get("kalender")
             for b in a.get("baner", []) if str(b.get("hoopit") or "").isdigit()]
    if not baner:
        return 0
    fra_m, til_m = fra.replace(day=1), (til.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    maneder, d = [], fra_m
    while d <= til_m:
        maneder.append(d.strftime("%Y-%m"))
        d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    hentet = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    rader, feil = [], 0
    for a, b in baner:
        venue = int(b["hoopit"])
        try:
            hendelser = hoopit_hendelser(a["hoopit"]["kalender"], venue, fra_m, til_m)
        except Exception as e:  # noqa: BLE001 – én bane som feiler skal ikke stoppe de andre
            print(f"- Hoopit {a['navn']} · {b['navn']} ({venue}): FEIL ved henting: {e}")
            feil += 1
            continue
        per_mnd = {m: [] for m in maneder}
        hoppet = 0
        for e in hendelser:
            r = hoopit_rad(e)
            if r is None:
                hoppet += 1
            elif r["dato"][:7] in per_mnd:
                per_mnd[r["dato"][:7]].append(r)
        print(f"- Hoopit {a['navn']} · {b['navn']} ({venue}): {sum(map(len, per_mnd.values()))} hendelser, "
              f"{hoppet} kamper fra fotball.no hoppet over")
        rader += [{"id": f"h{venue}-{m}", "data": {"kilde": "hoopit", "venueId": venue, "anleggId": a["id"], "baneId": b["id"],
                                                   "maned": m, "hentet": hentet, "hendelser": sorted(v, key=lambda x: (x["dato"], x["fra"]))}}
                  for m, v in per_mnd.items()]
    if rader and not dry:
        db.upsert("gjest", rader)
        print(f"Gjesteanlegg lagret: {len(rader)} bane-måneder.")
    return feil


if __name__ == "__main__":
    sys.exit(main())
