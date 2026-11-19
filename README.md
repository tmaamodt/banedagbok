# Banedagbok

Banedagbok for fotballanlegg: kamper fra fotball.no, treningstider, treningskamper, bookinger og dommere på én tavle,
med roller for admin, trenere, dommeransvarlig og dommere. Besøkende ser uka uten å logge inn.

| Mappe / fil | Innhold |
| --- | --- |
| [`banedagbok/`](banedagbok/) | Nettsiden (`index.html`) og brukerveiledning og oppsett ([`banedagbok/README.md`](banedagbok/README.md)) |
| [`supabase/`](supabase/) | Database: `schema.sql` (tabeller og tilgangsregler), `seed.sql` (startoppsett) og `gjesteanlegg_aursmoen.sql` |
| [`scripts/hent_kamper.py`](scripts/hent_kamper.py) | Henter kamper, dommere og klubbenes kamper fra fotball.no, og treninger for gjesteanlegg fra Hoopit |
| [`.github/workflows/hent-kamper.yml`](.github/workflows/hent-kamper.yml) | Kjører hentingen hver natt |

Se [`banedagbok/README.md`](banedagbok/README.md) for hvordan løsningen settes opp med Supabase og publiseres, og hvordan den brukes.
