# Wat er veranderd is

## 1.4.0

- **Koppenlijst-kaart** (`custom:nos-teletekst-koppen-card`). De koppen als
  leesbare lijst; tik erop en het bericht klapt open. Prettiger op een telefoon
  dan de teletekstpagina zelf.
- Spraakbediening gedocumenteerd: met een `conversation`-trigger kun je Assist
  laten voorlezen wat er op teletekst staat. Daar was geen extra code voor
  nodig, alleen een voorbeeld.
- Changelog en issue-sjablonen toegevoegd.

## 1.3.0

- **Verkeersinformatie** uit pagina 730. Alle subpagina's worden opgehaald en
  de doorlopende meldingen weer samengevoegd, dan uit elkaar getrokken tot weg,
  richting, lengte, vertraging en oorzaak.
- `sensor.nos_teletekst_verkeer` met het aantal files, plus een `binary_sensor`
  per opgegeven weg.
- De integratie ruimt achtergebleven entiteiten op. Haalde je een trefwoord of
  weg uit de instellingen, dan bleef de sensor als *niet beschikbaar* staan.

## 1.2.0

- **Trefwoord-bewaking**: elk opgegeven woord krijgt een `binary_sensor` die
  aangaat zodra het op een gevolgde pagina verschijnt.
- **Koppen met paginanummer** als `[{tekst, pagina}]` op de sensor en de dienst.
- Subpagina's lopen in de kaart vanzelf door, zoals op tv. Blader je zelf, dan
  stopt dat.
- Snelknoppen (`favorieten`) in de kaart.
- Diagnostiek, en tests op het uitlezen van de tekst.

## 1.1.0

- **Sensoren** per gevolgde pagina, met de volledige tekst in de attributen.
- **Gebeurtenis** `nos_teletekst_pagina_gewijzigd` bij een inhoudelijke
  wijziging.
- **Diensten** `pagina_ophalen` en `zoeken`.

## 1.0.1

Eerste versie: de teletekstkaart, met een eigen adres om de pagina's op te
halen zodat de browser niet tegen CORS aanloopt.
