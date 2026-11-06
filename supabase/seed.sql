-- Startoppsett for banedagboken: anleggene og delbanene som brukes i dag.
-- Kjør etter schema.sql. Overskriver ikke et oppsett som allerede finnes.
-- Kampene hentes av skriptet scripts/hent_kamper.py (GitHub Actions), ikke herfra.

insert into public.config (id, data) values ('oppsett', '{
  "klubb": "",
  "anlegg": [
    {
      "id": "a-holand",
      "navn": "Høland idrettsanlegg",
      "fiksId": "11998",
      "delbaner": [
        {
          "id": "d-hele",
          "navn": "Hele banen",
          "start": 0,
          "bredde": 12,
          "alias": [
            "Høland stadion kunstgress"
          ]
        },
        {
          "id": "d-9a",
          "navn": "9er A",
          "start": 0,
          "bredde": 6,
          "alias": []
        },
        {
          "id": "d-9b",
          "navn": "9er B",
          "start": 6,
          "bredde": 6,
          "alias": [
            "Høland stadion kg 9er B"
          ]
        },
        {
          "id": "d-7a",
          "navn": "7er A",
          "start": 0,
          "bredde": 3,
          "alias": [
            "Høland stadion kg 7er A"
          ]
        },
        {
          "id": "d-7b",
          "navn": "7er B",
          "start": 3,
          "bredde": 3,
          "alias": []
        },
        {
          "id": "d-7c",
          "navn": "7er C",
          "start": 6,
          "bredde": 3,
          "alias": []
        },
        {
          "id": "d-7d",
          "navn": "7er D",
          "start": 9,
          "bredde": 3,
          "alias": [
            "Høland stadion kg 7er D"
          ]
        },
        {
          "id": "d-5a",
          "navn": "5er A",
          "start": 0,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5b",
          "navn": "5er B",
          "start": 2,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5c",
          "navn": "5er C",
          "start": 4,
          "bredde": 2,
          "alias": [
            "Høland stadion kg 5er C"
          ]
        },
        {
          "id": "d-5d",
          "navn": "5er D",
          "start": 6,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5e",
          "navn": "5er E",
          "start": 8,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5f",
          "navn": "5er F",
          "start": 10,
          "bredde": 2,
          "alias": []
        }
      ]
    },
    {
      "id": "a-bjorkelangen",
      "navn": "Bjørkelangen kunstgress",
      "fiksId": "5316",
      "delbaner": [
        {
          "id": "d-hele",
          "navn": "Hele banen",
          "start": 0,
          "bredde": 12,
          "alias": [
            "Bjørkelangen kunstgress"
          ]
        },
        {
          "id": "d-9a",
          "navn": "9er A",
          "start": 0,
          "bredde": 6,
          "alias": [
            "Bjørkelangen kg 9er A"
          ]
        },
        {
          "id": "d-9b",
          "navn": "9er B",
          "start": 6,
          "bredde": 6,
          "alias": [
            "Bjørkelangen kg 9er B"
          ]
        },
        {
          "id": "d-7a",
          "navn": "7er A",
          "start": 0,
          "bredde": 3,
          "alias": [
            "Bjørkelangen kg 7er A"
          ]
        },
        {
          "id": "d-7b",
          "navn": "7er B",
          "start": 3,
          "bredde": 3,
          "alias": []
        },
        {
          "id": "d-7c",
          "navn": "7er C",
          "start": 6,
          "bredde": 3,
          "alias": []
        },
        {
          "id": "d-7d",
          "navn": "7er D",
          "start": 9,
          "bredde": 3,
          "alias": [
            "Bjørkelangen kg 7er D"
          ]
        },
        {
          "id": "d-5a",
          "navn": "5er A",
          "start": 0,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5b",
          "navn": "5er B",
          "start": 2,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5c",
          "navn": "5er C",
          "start": 4,
          "bredde": 2,
          "alias": [
            "Bjørkelangen kg 5er C"
          ]
        },
        {
          "id": "d-5d",
          "navn": "5er D",
          "start": 6,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5e",
          "navn": "5er E",
          "start": 8,
          "bredde": 2,
          "alias": []
        },
        {
          "id": "d-5f",
          "navn": "5er F",
          "start": 10,
          "bredde": 2,
          "alias": [
            "Bjørkelangen kg 5er F"
          ]
        }
      ]
    }
  ],
  "varighet": {
    "11": 120,
    "9": 90,
    "7": 75,
    "5": 60,
    "3": 45
  }
}'::jsonb)
on conflict (id) do nothing;

-- Legg inn den første admin. Bytt ut e-postadressen (to steder, små bokstaver i id) og navnet, og kjør:
-- insert into public.brukere (id, data) values
--   ('navn@eksempel.no', '{"epost": "navn@eksempel.no", "navn": "Banekoordinator", "rolle": "admin", "lag": []}');
-- Flere admins og trenere legges til fra nettsiden (fanen Brukere) etter innlogging.
