# Wat er veranderd is

## 1.9.1

- De koppenlijst zei alleen dát de sensor ontbrak, niet waar je hem aanzet. Nu
  wijst hij de weg naar Snel instellen.

## 1.9.0

Een ronde die niets nieuws toevoegt maar alles beter maakt.

- **Entiteitsnamen zijn nu vertaald.** Ze stonden hardcoded in het Nederlands,
  dus een Engelse gebruiker zag "Pagina 101". Nu komen ze uit de vertaling:
  "Page 101".
- **Twee echte fouten uit de typecontrole.** Het schaalfilter gebruikte de oude
  Pillow-naam die op termijn verdwijnt, en de verkeersmeldingen waren losse
  dicts waardoor het optellen van kilometers niet te controleren viel. Die
  hebben nu een eigen type.
- **Twee ongebruikte imports** eruit, en de hele codebase door dezelfde linter
  en formatter als Home Assistant zelf gebruikt.
- **Twee nieuwe bewakers**, allebei voor fouten die anders pas bij de gebruiker
  opduiken: één die kijkt of elke gebruikte naam geïmporteerd is, en één die
  kijkt of elk scherm en elke entiteitsnaam een vertaling heeft in beide talen.
- **De CI controleert nu alles**: ruff, mypy, de tests, en eslint plus prettier
  op de kaart. 65 tests.

## 1.8.0

- **Aantal regels verder** bij een eigen sensor. Teletekst zet de waarde vaak
  onder het kopje: op het weerrapport staat de temperatuur een regel onder de
  plaatsnaam. Zonder springen vond je de plaatsnaam en dus geen getal.
- **Subpagina's worden meegenomen** bij het zoeken. Het weerrapport verdeelt de
  plaatsen over vijf subpagina's; wie alleen de eerste ophaalde, vond de helft
  niet.
- **Opgelost:** de voorkeuze "temperatuur bij mij in de buurt" wees naar pagina
  702, maar dat is een weerkaart met losse getallen zonder plaatsnamen. Hij
  gebruikt nu pagina 705, het weerrapport.

## 1.7.2

- **Opgelost:** "Eigen sensor verwijderen" gaf een serverfout. Er ontbrak een
  import, en die regel wordt pas uitgevoerd als je op die knop drukt, dus het
  viel bij het bouwen niet op.
- Er draait nu een test die elke module nakijkt op namen die nergens vandaan
  komen, zodat zoiets voortaan bij het bouwen stukloopt en niet bij jou.

## 1.7.1

- **Opgelost:** wie al sensoren had, raakte ze kwijt bij het bijwerken naar
  1.7.0. De nieuwe standaard "niets aanmaken" gold namelijk ook voor bestaande
  installaties. Nu blijven bestaande sensoren staan; alleen een nieuwe
  installatie begint leeg.

## 1.7.0

- **Installeren maakt niets meer aan.** De teletekstkaart werkt zonder
  entiteiten, dus je lijst blijft leeg tot je zelf iets kiest.
- **Snel instellen**: kies "het nieuws volgen", "seintje over mijn club",
  "afbeelding voor e-ink", "files op mijn route" of "temperatuur bij mij", en de
  rest wordt goed gezet. Wat je al had blijft staan.

## 1.6.0

- **Zelf sensoren maken.** Wijs bij Configureren een regel van een pagina aan en
  maak er een sensor van: de eerste regel met een woord erin, of een vast
  regelnummer. Eventueel alleen het getal, met een eenheid.
- **Je bepaalt wat er aangemaakt wordt.** Per pagina vink je aan of je de
  tekstsensor wilt, de afbeelding, of allebei. De afbeelding staat nu standaard
  uit — twaalf entiteiten aanmaken zonder te vragen was te veel.
- **Opgelost:** bij een vast regelnummer werden lege regels niet meegeteld,
  waardoor regel 5 op een andere rij uitkwam dan je op het scherm ziet.

## 1.5.0

- **Instellingsschermen voor beide kaarten.** Geen YAML meer nodig: kies de
  kaart en vul de velden in.
- **Teletekst als afbeelding.** Elke gevolgde pagina krijgt een `image`-entiteit
  die de pagina tekent met het echte teletekstfont. Voor meldingen, e-ink
  schermpjes of een plaatjeskaart.
- **Pagina's kiezen bij het installeren**, met de bekendste alvast in de lijst.
  Voorheen kreeg je alleen 101 en moest je de instellingen zien te vinden.
- **`koppen_markdown`**: de koppen als kant-en-klare lijst voor een
  Markdown-kaart, zonder sjabloon.

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
