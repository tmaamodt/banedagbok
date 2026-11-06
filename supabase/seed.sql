-- Startoppsett for banedagboken: anleggene, delbanene og koblingene til banene på fotball.no.
-- Kjør etter schema.sql. Overskriver ikke et oppsett som allerede finnes.
-- Kampene hentes av skriptet scripts/hent_kamper.py (GitHub Actions), ikke herfra.
--
-- Banen er delt i fire kvarter: 9er A/B er halvdelene, 7er A–D er kvarterene.
-- 5er-banene på fotball.no ligger i et kvarter (5er C → 7er B, 5er F → 7er C), utledet fra hvilke
-- baner som er i bruk samtidig i kampoppsettet. Koblingene kan endres under Baner på nettsiden.

insert into public.config (id, data) values ('oppsett', '{
  "klubb": "",
  "lag": [],
  "varighet": {
    "3": 45,
    "5": 60,
    "7": 75,
    "9": 90,
    "11": 120
  },
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
          "alias": [
            "Høland stadion kg 5er C"
          ]
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
          "alias": [
            "Bjørkelangen kg 5er C"
          ]
        },
        {
          "id": "d-7c",
          "navn": "7er C",
          "start": 6,
          "bredde": 3,
          "alias": [
            "Bjørkelangen kg 5er F"
          ]
        },
        {
          "id": "d-7d",
          "navn": "7er D",
          "start": 9,
          "bredde": 3,
          "alias": [
            "Bjørkelangen kg 7er D"
          ]
        }
      ]
    }
  ]
}'::jsonb)
on conflict (id) do nothing;

-- Legg inn den første admin. Bytt ut e-postadressen (to steder, små bokstaver i id) og navnet, og kjør:
-- insert into public.brukere (id, data) values
--   ('navn@eksempel.no', '{"epost": "navn@eksempel.no", "navn": "Banekoordinator", "rolle": "admin", "lag": []}');
-- Flere admins og trenere legges til fra nettsiden (fanen Brukere) etter innlogging.
