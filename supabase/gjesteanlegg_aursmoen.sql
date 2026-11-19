-- Gjesteanlegg: Aursmoen (Aurskog-Finstadbru SK). Bare visning i banedagboken.
-- Treninger og bookinger hentes fra AFSK sin offentlige kalender i Hoopit, kamper fra fotball.no
-- (anlegg 11991 og 17513). Kampene som Hoopit selv har hentet fra fotball.no, hoppes over, så ingen
-- kamper vises to ganger. Kjør etter schema.sql og seed.sql. Legger ikke inn anleggene på nytt hvis de finnes.
--
-- Hoopit-bane-ID-ene (hoopit) og navnene på fotball.no (alias) kan endres under Baner på nettsiden.
update public.config
set data = jsonb_set(data, '{anlegg}', coalesce(data->'anlegg', '[]'::jsonb) || '[
  {
    "id": "a-aursmoen",
    "navn": "Aursmoen",
    "fiksId": "11991",
    "gjest": true,
    "hoopit": {
      "kalender": "a9be74ad-a8e6-41e4-a70a-d30df15e8f96",
      "klubb": "Aurskog-Finstadbru SK"
    },
    "baner": [
      {
        "id": "b-kg",
        "navn": "Kunstgress",
        "underlag": "kunstgress",
        "storrelse": "11",
        "kobling": "fotball.no",
        "hoopit": 2263
      },
      {
        "id": "b-kg2",
        "navn": "KG 2 (9er)",
        "underlag": "kunstgress",
        "storrelse": "9",
        "kobling": "fotball.no",
        "hoopit": 2264
      },
      {
        "id": "b-5",
        "navn": "5er",
        "underlag": "kunstgress",
        "storrelse": "5",
        "kobling": "fotball.no",
        "hoopit": 2265
      },
      {
        "id": "b-mini",
        "navn": "Mini 3er-baner",
        "underlag": "kunstgress",
        "storrelse": "3",
        "kobling": "fri",
        "hoopit": 2558
      }
    ],
    "delbaner": [
      {
        "id": "d-kg-hele",
        "baneId": "b-kg",
        "navn": "Hele banen",
        "start": 0,
        "bredde": 12,
        "alias": [
          "Aursmoen kunstgress"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg-9a",
        "baneId": "b-kg",
        "navn": "9er A",
        "start": 0,
        "bredde": 6,
        "alias": [
          "Aursmoen kunstgress 9er A"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg-9b",
        "baneId": "b-kg",
        "navn": "9er B",
        "start": 6,
        "bredde": 6,
        "alias": [
          "Aursmoen kunstgress 9er B"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg-7a",
        "baneId": "b-kg",
        "navn": "7er A",
        "start": 0,
        "bredde": 3,
        "alias": [
          "Aursmoen kunstgress 7er A"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg-7b",
        "baneId": "b-kg",
        "navn": "7er B",
        "start": 3,
        "bredde": 3,
        "alias": [
          "Aursmoen kunstgress 7er B"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg-7c",
        "baneId": "b-kg",
        "navn": "7er C",
        "start": 6,
        "bredde": 3,
        "alias": [
          "Aursmoen kunstgress 7er C"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg-7d",
        "baneId": "b-kg",
        "navn": "7er D",
        "start": 9,
        "bredde": 3,
        "alias": [
          "Aursmoen kunstgress 7er D"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg2-hele",
        "baneId": "b-kg2",
        "navn": "Hele banen",
        "start": 0,
        "bredde": 12,
        "alias": [
          "Aursmoen KG 2 9er"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg2-a",
        "baneId": "b-kg2",
        "navn": "7er A",
        "start": 0,
        "bredde": 6,
        "alias": [
          "Aursmoen KG 2 7er A",
          "Aursmoen KG 2 5er A"
        ],
        "aktiv": true
      },
      {
        "id": "d-kg2-b",
        "baneId": "b-kg2",
        "navn": "7er B",
        "start": 6,
        "bredde": 6,
        "alias": [
          "Aursmoen KG 2 7er B"
        ],
        "aktiv": true
      },
      {
        "id": "d-5-hele",
        "baneId": "b-5",
        "navn": "Hele banen",
        "start": 0,
        "bredde": 12,
        "alias": [
          "Aursmoen mini kg"
        ],
        "aktiv": true
      },
      {
        "id": "d-5-a",
        "baneId": "b-5",
        "navn": "Halvdel A",
        "start": 0,
        "bredde": 6,
        "alias": [],
        "aktiv": true
      },
      {
        "id": "d-5-b",
        "baneId": "b-5",
        "navn": "Halvdel B",
        "start": 6,
        "bredde": 6,
        "alias": [],
        "aktiv": true
      },
      {
        "id": "d-mini-hele",
        "baneId": "b-mini",
        "navn": "Alle 3er-banene",
        "start": 0,
        "bredde": 12,
        "alias": [],
        "aktiv": true
      }
    ]
  },
  {
    "id": "a-sletta",
    "navn": "Aursmoen Sletta",
    "fiksId": "17513",
    "gjest": true,
    "hoopit": {
      "kalender": "a9be74ad-a8e6-41e4-a70a-d30df15e8f96",
      "klubb": "Aurskog-Finstadbru SK"
    },
    "baner": [
      {
        "id": "b-s9",
        "navn": "9er",
        "underlag": "kunstgress",
        "storrelse": "9",
        "kobling": "fotball.no",
        "hoopit": 2847
      },
      {
        "id": "b-s7a",
        "navn": "7er A",
        "underlag": "kunstgress",
        "storrelse": "7",
        "kobling": "fotball.no",
        "hoopit": 2848
      },
      {
        "id": "b-s7b",
        "navn": "7er B",
        "underlag": "kunstgress",
        "storrelse": "7",
        "kobling": "fotball.no",
        "hoopit": 2849
      }
    ],
    "delbaner": [
      {
        "id": "d-s9-hele",
        "baneId": "b-s9",
        "navn": "Hele banen",
        "start": 0,
        "bredde": 12,
        "alias": [
          "Aursmoen Sletta 9er"
        ],
        "aktiv": true
      },
      {
        "id": "d-s7a-hele",
        "baneId": "b-s7a",
        "navn": "Hele banen",
        "start": 0,
        "bredde": 12,
        "alias": [
          "Aursmoen Sletta 7er A"
        ],
        "aktiv": true
      },
      {
        "id": "d-s7b-hele",
        "baneId": "b-s7b",
        "navn": "Hele banen",
        "start": 0,
        "bredde": 12,
        "alias": [
          "Aursmoen Sletta 7er B"
        ],
        "aktiv": true
      }
    ]
  }
]'::jsonb)
where id = 'oppsett'
  and not exists (select 1 from jsonb_array_elements(coalesce(data->'anlegg', '[]'::jsonb)) a
                  where a->>'id' in ('a-aursmoen', 'a-sletta'));
