#!/usr/bin/env python3
"""Sender e-postvarsler fra banedagboken.

Varsler (hver bruker velger selv under «Varsler» på nettsiden):
  godkjenning   til admin: noen har logget inn og venter på godkjenning
  kampITrening  til trenere: en kamp fra fotball.no ligger i treningstiden til et av lagene deres

Hvert varsel sendes én gang. Det som er sendt, lagres i tabellen varsellogg.
E-post sendes med SMTP, gjerne den samme e-posttjenesten som Supabase bruker til innloggingslenker.

Miljøvariabler:
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
  SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASS, VARSEL_AVSENDER (avsenderadresse)
  NETTSIDE  adressen til banedagboken, brukes som lenke i e-posten

  python scripts/send_varsler.py [--tørrkjøring]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hent_kamper import Supabase  # noqa: E402

FORVARMING = 15  # banen er reservert 15 minutter før kampstart (som på nettsiden)
DAGER = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]
TRENERROLLER = ("trener", "trener_pluss")


# ---------------------------------------------------------------- tid og baner (samme regler som nettsiden)
def til_min(t: str | None) -> int | None:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", (t or "").strip())
    return int(m[1]) * 60 + int(m[2]) if m else None


def fra_min(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def kamp_varighet(k: dict, cfg: dict) -> int:
    if k.get("varighet"):
        return int(k["varighet"])
    m = re.search(r"(\d{1,2})\s*mot", k.get("spillform") or "", re.I)
    v = cfg.get("varighet") or {}
    return int(v.get(m[1]) if m and v.get(m[1]) else v.get("11") or 120)


def delbane(a: dict, del_id: str) -> dict | None:
    return next((d for d in a.get("delbaner") or [] if d.get("id") == del_id), None)


def bane_av(a: dict, del_id: str) -> str | None:
    d = delbane(a, del_id)
    return (d or {}).get("baneId") or ((a.get("baner") or [{}])[0].get("id"))


def sone(a: dict, del_id: str) -> tuple[int, int]:
    d = delbane(a, del_id)
    return (d["start"], d["start"] + d["bredde"]) if d else (0, 12)


def trening_pa(t: dict, dato: dt.date) -> bool:
    """Har treningen en økt denne datoen (ikke avlyst)?"""
    ds = dato.isoformat()
    if ds in (t.get("avlyst") or []):
        return False
    if t.get("type") == "enkelt":
        return t.get("dato") == ds
    if int(t.get("ukedag") or 0) != dato.isoweekday() or not (t.get("fom") or "") <= ds <= (t.get("tom") or ""):
        return False
    ar, uke, _ = dato.isocalendar()
    if isinstance(t.get("ukenr"), list) and not (ar == int(t.get("ar") or 0) and uke in t["ukenr"]):
        return False
    return not t.get("uker") or (uke % 2 == 0) == (t["uker"] == "partall")


def kamp_i_trening(cfg: dict, kamper: dict, treninger: dict, idag: dt.date) -> list[dict]:
    """Kamper fra fotball.no på egne anlegg som overlapper en trening (samme bane, tid og del av banen)."""
    anlegg = {a["id"]: a for a in cfg.get("anlegg") or [] if not a.get("gjest")}
    ut = []
    for kid, k in kamper.items():
        a = anlegg.get(k.get("anleggId"))
        kick = til_min(k.get("tid"))
        if not a or kick is None or (k.get("kilde") or "fotball.no") != "fotball.no" or (k.get("dato") or "") < idag.isoformat():
            continue
        dato = dt.date.fromisoformat(k["dato"])
        ks, ke = kick - FORVARMING, kick + kamp_varighet(k, cfg)
        kb, (kzs, kze) = bane_av(a, k.get("delbaneId")), sone(a, k.get("delbaneId"))
        for tid, t in treninger.items():
            if t.get("anleggId") != a["id"] or bane_av(a, t.get("delbaneId")) != kb or not trening_pa(t, dato):
                continue
            ts, te = til_min(t.get("fra")), til_min(t.get("til"))
            tzs, tze = sone(a, t.get("delbaneId"))
            if ts is None or te is None or ts >= ke or ks >= te or tzs >= kze or kzs >= tze:
                continue
            ut.append({"nokkel": f"kamp|{kid}|{tid}|{k['dato']}", "lag": t.get("lag"), "kamp": k, "trening": t, "anlegg": a,
                       "kampstart": fra_min(kick), "reservert": f"{fra_min(ks)}–{fra_min(ke)}"})
    return ut


# ---------------------------------------------------------------- e-post
def adresse(u: dict) -> str:
    return (u.get("varselEpost") or u.get("epost") or "").strip()


def har_varsel(u: dict, navn: str) -> bool:
    return bool((u.get("varsler") or {}).get(navn)) and "@" in adresse(u)


def send(smtp, avsender: str, til: str, emne: str, tekst: str, dry: bool):
    if dry:
        print(f"  [tørrkjøring] til {til}: {emne}\n    " + tekst.replace("\n", "\n    "))
        return
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = formataddr(("Banedagbok", avsender)), til, emne
    m.set_content(tekst)
    m.add_alternative("<div style=\"font-family:system-ui,sans-serif;font-size:15px;line-height:1.5\">"
                      + "<br>".join(html.escape(x) for x in tekst.split("\n")) + "</div>", subtype="html")
    smtp.send_message(m)


def koble_smtp():
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        return None
    port = int(os.environ.get("SMTP_PORT") or 587)
    s = smtplib.SMTP_SSL(host, port, timeout=30, context=ssl.create_default_context()) if port == 465 else smtplib.SMTP(host, port, timeout=30)
    if port != 465:
        s.starttls(context=ssl.create_default_context())
    if os.environ.get("SMTP_USER"):
        s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASS", ""))
    return s


def dato_tekst(ds: str) -> str:
    d = dt.date.fromisoformat(ds)
    return f"{DAGER[d.weekday()]} {d.day}.{d.month}.{d.year}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--tørrkjøring", "--dry-run", dest="dry", action="store_true", help="vis varslene, ikke send eller lagre")
    args = p.parse_args()
    url, key = os.environ.get("SUPABASE_URL", "").strip(), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        print("Mangler SUPABASE_URL eller SUPABASE_SERVICE_ROLE_KEY.")
        return 2
    avsender, nettside = os.environ.get("VARSEL_AVSENDER", "").strip(), os.environ.get("NETTSIDE", "").strip()
    if not args.dry and not (os.environ.get("SMTP_HOST", "").strip() and avsender):
        print("E-postvarsler er ikke satt opp (SMTP_HOST og VARSEL_AVSENDER mangler). Ingenting sendt.")
        return 0
    db = Supabase(url, key)
    rader = lambda t, q="select=id,data": {r["id"]: r["data"] for r in db.get_all(t, q)}  # noqa: E731
    brukere = rader("brukere")
    logg = set(rader("varsellogg", "select=id"))
    idag = dt.date.today()
    utsendinger: dict[str, list[str]] = {}   # e-post → avsnitt
    emner: dict[str, set[str]] = {}
    nye_logg = []

    def legg_til(u: dict, nokkel: str, emne: str, avsnitt: str):
        til = adresse(u)
        utsendinger.setdefault(til, []).append(avsnitt)
        emner.setdefault(til, set()).add(emne)
        nye_logg.append(nokkel)

    # 1) noen venter på godkjenning
    ventende = rader("ventende")
    admins = [u for u in brukere.values() if u.get("rolle") == "admin" and har_varsel(u, "godkjenning")]
    for vid, v in ventende.items():
        nokkel = f"godkjenning|{vid}"
        if nokkel in logg:
            continue
        hvem = " ".join(x for x in [v.get("navn") or "", f"({v['epost']})" if v.get("epost") else "(uten e-post)"] if x)
        lev = {"google": "Google", "facebook": "Facebook", "email": "lenke på e-post"}.get(v.get("leverandor"), v.get("leverandor") or "")
        for u in admins:
            legg_til(u, nokkel, "Noen venter på godkjenning",
                     f"{hvem} har logget inn med {lev} og venter på godkjenning.\nGodkjenn eller avvis under Brukere i banedagboken.")
        if not admins:
            nye_logg.append(nokkel)

    # 2) kamp i treningstid
    cfg = (rader("config").get("oppsett") or {})
    kamper = rader("kamper", f"select=id,data&kilde=eq.fotball.no&dato=gte.{idag.isoformat()}")
    treninger = rader("treninger")
    trenere: dict[str, list[dict]] = {}
    for u in brukere.values():
        if u.get("rolle") in TRENERROLLER and har_varsel(u, "kampITrening"):
            for lag in u.get("lag") or []:
                trenere.setdefault(lag, []).append(u)
    for x in sorted(kamp_i_trening(cfg, kamper, treninger, idag), key=lambda x: (x["kamp"]["dato"], x["kampstart"])):
        if x["nokkel"] in logg:
            continue
        k, t, a = x["kamp"], x["trening"], x["anlegg"]
        d = delbane(a, k.get("delbaneId")) or {}
        avsnitt = (f"{x['lag']}: {dato_tekst(k['dato'])} har dere trening {t.get('fra')}–{t.get('til')} på {a.get('navn')}.\n"
                   f"Kamp: {(k.get('hjemmelag') or '').strip()} – {(k.get('bortelag') or '').strip()}, kampstart {x['kampstart']}"
                   f"{', ' + d['navn'] if d.get('navn') else ''}. Banen er reservert {x['reservert']}, og kampen går foran treningen.")
        for u in trenere.get(x["lag"], []):
            legg_til(u, x["nokkel"], "Kamp i treningstiden", avsnitt)
        if not trenere.get(x["lag"]):
            nye_logg.append(x["nokkel"])

    if not utsendinger:
        print("Ingen nye varsler.")
    smtp = None if args.dry else koble_smtp()
    try:
        for til, avsnitt in utsendinger.items():
            emne = " og ".join(sorted(emner[til])) if len(emner[til]) < 3 else "Nye varsler"
            tekst = "\n\n".join(avsnitt) + (f"\n\nBanedagboken: {nettside}" if nettside else "") + \
                "\n\nDu får denne e-posten fordi du har slått på varsler. Slå dem av under «Varsler» øverst på siden når du er logget inn."
            send(smtp, avsender, til, f"Banedagbok: {emne}", tekst, args.dry)
            print(f"Sendt til {til}: {len(avsnitt)} varsel(er).")
    finally:
        if smtp:
            smtp.quit()
    if nye_logg and not args.dry:
        na = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        db.upsert("varsellogg", [{"id": n, "data": {"sendt": na}} for n in dict.fromkeys(nye_logg)])
        # rydd: varsler eldre enn ett år
        gamle = [r["id"] for r in db.get_all("varsellogg", f"select=id&updated_at=lt.{(idag - dt.timedelta(days=365)).isoformat()}")]
        if gamle:
            db.delete_ids("varsellogg", gamle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
