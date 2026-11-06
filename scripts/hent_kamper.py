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
def last_ned_excel(fiks_id: str, navn: str, fra: dt.date, til: dt.date) -> bytes:
    qs = urllib.parse.urlencode({"stadiumId": fiks_id, "heading": f"Kamper for {navn}",
                                 "fromDate": fra.isoformat(), "toDate": til.isoformat()})
    req = urllib.request.Request(f"{FOTBALL_NO}?{qs}", headers={"User-Agent": USER_AGENT})
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
    bane = next((b for b in anlegg["baner"] if b.get("kobling") == "fotball.no"), anlegg["baner"][0])
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
    return 1 if feil else 0


if __name__ == "__main__":
    sys.exit(main())
