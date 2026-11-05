import re
import sys

TALLORD = {
    "null", "ett", "én", "to", "tre", "fire", "fem", "seks", "sju", "syv",
    "åtte", "ni", "ti", "elleve", "tolv", "tretten", "fjorten", "femten",
    "seksten", "sytten", "atten", "nitten", "tjue", "tretti", "førti",
    "femti", "seksti", "sytti", "åtti", "nitti", "hundre", "tusen",
    "million", "millioner", "milliard", "milliarder",
}

def analyser_tekst(filnavn):
    with open(filnavn, "r", encoding="utf-8-sig") as fil:
        tekst = fil.read()
    ordliste = tekst.split()

    antall_ord = len(ordliste)

    store_bokstaver = 0
    for tegn in tekst:
        if tegn.isupper():
            store_bokstaver += 1

    ord_med_stor_forbokstav = 0
    for ord in ordliste:
        if ord[0].isupper():
            ord_med_stor_forbokstav += 1

    sifre = 0
    for tegn in tekst:
        if tegn.isdigit():
            sifre += 1

    antall_tall = len(re.findall(r"\d+", tekst))

    antall_tallord = 0
    for ord in ordliste:
        rent_ord = ord.lower().strip(".,!?:;\"'()")
        if rent_ord in TALLORD:
            antall_tallord += 1

    return antall_ord, store_bokstaver, ord_med_stor_forbokstav, antall_tall, sifre, antall_tallord

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bruk: python ordteller.py <filnavn>")
        sys.exit(1)

    filnavn = sys.argv[1]

    try:
        antall_ord, store_bokstaver, stor_forbokstav, antall_tall, sifre, tallord = analyser_tekst(filnavn)
        print(f"Filen '{filnavn}' inneholder:")
        print(f"  {antall_ord} ord")
        print(f"  {store_bokstaver} store bokstaver")
        print(f"  {stor_forbokstav} ord som starter med stor bokstav")
        print(f"  {antall_tall} tall")
        print(f"  {sifre} sifre")
        print(f"  {tallord} tallord")
    except FileNotFoundError:
        print(f"Fant ikke filen '{filnavn}'.")
