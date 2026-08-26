# NOS Teletekst voor Home Assistant

[![HACS: custom](https://img.shields.io/badge/HACS-custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Release](https://img.shields.io/github/v/release/schakelkast/teletekst-101)](https://github.com/schakelkast/teletekst-101/releases)
[![Validatie](https://github.com/schakelkast/teletekst-101/actions/workflows/validate.yml/badge.svg)](https://github.com/schakelkast/teletekst-101/actions/workflows/validate.yml)
[![Licentie: MIT](https://img.shields.io/badge/licentie-MIT-green.svg)](LICENSE)

Teletekst in Home Assistant, zoals het op tv staat: 40×24 tekens, blokgrafiek,
de acht teletekstkleuren. En omdat het gewoon entiteiten zijn, kun je er ook
mee automatiseren.

![Teletekst in Home Assistant](images/teletekst-kaart.png)

## Wat je ermee kunt

**Een melding als er nieuws is over jouw onderwerp.** Geef trefwoorden op — je
club, je woonplaats, een dossier dat je volgt — en er komt een sensor per woord
die aangaat zodra het op een gevolgde pagina verschijnt.

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.nos_teletekst_trefwoord_feyenoord
    to: "on"
actions:
  - action: notify.mobile_app_telefoon
    data:
      title: Teletekst
      message: "{{ state_attr(trigger.entity_id, 'regels') | join(' — ') }}"
```

**Het nieuws voorlezen bij je ochtendroutine.** De volledige pagina staat als
platte tekst klaar, zonder blokgrafiek, dus een spraakassistent maakt er geen
onzin van.

```yaml
actions:
  - action: tts.speak
    target:
      entity_id: tts.google
    data:
      media_player_entity_id: media_player.keuken
      message: >-
        Goedemorgen. Het nieuws van teletekst:
        {{ state_attr('sensor.nos_teletekst_pagina_101', 'tekst') }}
```

**Weten of het vastloopt op jouw route.** Zet verkeersinformatie aan en geef de
wegen op die je rijdt. Elke weg krijgt een sensor die aangaat zodra er een
melding voor staat, met de vertraging erbij — uitgelezen uit de ANWB-pagina's.

```yaml
triggers:
  - trigger: time
    at: "07:15:00"
conditions:
  - condition: state
    entity_id: binary_sensor.nos_teletekst_verkeer_a15
    state: "on"
actions:
  - action: notify.mobile_app_telefoon
    data:
      title: "File op de A15"
      message: >-
        {{ state_attr('binary_sensor.nos_teletekst_verkeer_a15', 'km') }} km,
        {{ state_attr('binary_sensor.nos_teletekst_verkeer_a15', 'minuten') }} minuten vertraging.
```

Er is ook een `sensor.nos_teletekst_verkeer` met het totale aantal files, de
opgetelde kilometers en alle meldingen in de attributen.

**Een koppenlijst op je dashboard.** Elke kop komt met het paginanummer waar
het bericht staat, dus je kunt er doorheen klikken.

```jinja
{% for k in state_attr('sensor.nos_teletekst_pagina_101', 'koppen') %}
- {{ k.tekst }} ({{ k.pagina }})
{% endfor %}
```

**Teletekst laten voorlezen door Assist.** Vraag het gewoon; er is geen extra
instelling voor nodig.

```yaml
triggers:
  - trigger: conversation
    command:
      - "wat staat er op teletekst"
      - "lees het nieuws voor"
actions:
  - action: nos_teletekst.pagina_ophalen
    data:
      pagina: "101"
    response_variable: pagina
  - set_conversation_response: "{{ pagina.kop }}"
```

**En gewoon: teletekst kijken.** Op je telefoon, je tablet of een wandpaneel.
Subpagina's lopen vanzelf door, net als op tv.

<p>
  <img src="images/teletekst-wandpaneel.png" width="300" alt="Op een wandpaneel">
  <img src="images/teletekst-cijferblok.png" width="200" alt="Cijferblok voor aanraakbediening">
</p>

## Installatie

**Via HACS** — open HACS, kies rechtsboven *Custom repositories*, plak
`https://github.com/schakelkast/teletekst-101` en kies type *Integration*.
Installeer daarna *NOS Teletekst* en herstart Home Assistant. Ga vervolgens naar
**Instellingen → Apparaten en diensten → Integratie toevoegen** en kies
*NOS Teletekst*.

**Handmatig** — kopieer `custom_components/nos_teletekst` naar je
`config/custom_components/`, herstart, en voeg de integratie toe.

Er hoeft niets in `configuration.yaml` en er hoeft geen Lovelace-resource
toegevoegd te worden: de integratie regelt dat zelf.

## De kaarten

Er zijn er twee. **NOS Teletekst** geeft de pagina zoals hij uitgezonden wordt.
**NOS Teletekst koppen** geeft dezelfde inhoud als leeslijst — prettiger op een
telefoon:

```yaml
type: custom:nos-teletekst-koppen-card
entity: sensor.nos_teletekst_pagina_101
```

Tik je op een kop, dan wordt dat bericht opgehaald en uitgeklapt. De lijst komt
uit het `koppen`-attribuut van de sensor, dus kies een overzichtspagina zoals
101 of 601.

### De teletekstkaart

Voeg de kaart **NOS Teletekst** toe aan een dashboard, of met de hand:

```yaml
type: custom:nos-teletekst-card
page: "101"
favorieten:
  - naam: Nieuws
    pagina: "101"
  - naam: Sport
    pagina: "601"
  - naam: Weer
    pagina: "702"
  - naam: Verkeer
    pagina: "730"
```

| optie | standaard | betekenis |
|---|---|---|
| `page` | `"100"` | beginpagina, subpagina mag ook: `100-2` |
| `refresh` | `60` | seconden tussen automatisch verversen, `0` zet het uit |
| `controls` | `true` | knoppenbalk onder of naast de pagina |
| `favorieten` | `[]` | snelknoppen, elk met `naam` en `pagina` |
| `subpages` | `"auto"` | subpagina's vanzelf doorlopen, `"off"` zet het uit |
| `subpage_seconds` | `8` | hoe lang een subpagina blijft staan |
| `aspect` | `"auto"` | `web` = smal zoals nos.nl, `tv` = breed zoals 4:3 |
| `max_height` | `0` | vaste maximumhoogte in pixels, `0` = zelf de ruimte meten |

### Bedienen

- **vegen** links/rechts is vorige/volgende pagina, omhoog/omlaag is subpagina
- **tikken** op een paginanummer in de tekst, of op de gekleurde regel onderaan
- **cijferblok** verschijnt als je het paginaveld aanraakt: drie cijfers en hij
  springt, net als met de afstandsbediening
- **toetsenbord**: cijfers intikken, pijltjestoetsen bladeren, Esc sluit

Blader je zelf door de subpagina's, dan stopt het automatisch doorlopen — je
bent dan aan het lezen, en dan is het vervelend als het beeld wegspringt. Met de
pauzeknop zet je het weer aan.

## Entiteiten, diensten en gebeurtenissen

Bij **Configureren** kies je welke pagina's je volgt, hoe vaak ze ververst
worden en op welke trefwoorden gelet wordt.

### Sensoren

Elke gevolgde pagina krijgt een sensor. De toestand is de eerste betekenisvolle
regel; de rest staat in de attributen:

| attribuut | inhoud |
|---|---|
| `tekst` | de hele pagina als platte tekst |
| `regels` | dezelfde tekst als lijst |
| `koppen` | koppen met het paginanummer erbij: `[{tekst, pagina}]` |
| `verwijzingen` | alle paginanummers waar deze pagina naar doorverwijst |
| `volgende_pagina`, `volgende_subpagina` | om doorheen te bladeren |

Elk trefwoord krijgt een `binary_sensor` die aangaat zodra het woord op een van
je gevolgde pagina's staat, met de gevonden regels in de attributen.

### Verkeer

Zet je verkeersinformatie aan, dan wordt pagina 730 met al zijn subpagina's
uitgelezen tot losse meldingen. Je krijgt `sensor.nos_teletekst_verkeer` met het
aantal files als toestand, en in de attributen `totaal_km`, `totaal_minuten`,
`wegen` en `meldingen`. Elke melding is opgesplitst:

```yaml
soort: Files            # of Afsluiting/Omleiding
weg: A12
van: Duitse grens
naar: Arnhem
km: 3
minuten: 2
tekst: "A12 Duitse grens->Arnhem tussen knp. Oud-Dijk en Duiven 3 km,2 min., ..."
```

Geef je wegen op, dan krijgt elke weg een eigen `binary_sensor` met alleen de
meldingen voor die weg. Bron is de ANWB, via de NOS.

### Gebeurtenis

`nos_teletekst_pagina_gewijzigd` komt langs zodra een gevolgde pagina
inhoudelijk verandert, met `pagina`, `kop` en `tekst`.

### Diensten

**`nos_teletekst.pagina_ophalen`** haalt elke pagina op, ook eentje die je niet
volgt, en geeft hem terug als tekst, regels en koppen.

**`nos_teletekst.zoeken`** zoekt een woord in de pagina's die je opgeeft. Elke
pagina is een aparte aanvraag bij de NOS, dus er worden er maximaal 30 tegelijk
doorzocht.

## Hoe het werkt

De pagina's komen van `teletekst-data.nos.nl`, dezelfde bron als
nos.nl/teletekst. Die API stuurt geen CORS-headers, dus de browser mag hem niet
rechtstreeks aanroepen. De integratie haalt de pagina daarom op vanaf Home
Assistant zelf en biedt hem aan op `/api/nos_teletekst/<pagina>`, achter je
gewone login.

De blokgrafiek zit in het teletekstfont van de NOS (Android VeraMono), dat
meegeleverd wordt en lokaal geserveerd — geen verbinding met een CDN. Bij het
omzetten naar platte tekst worden die tekens (F020–F07F) vervangen door spaties:
het zijn tekeningen, geen letters.

Een teken-cel is op nos.nl 0,602 × 1,204 em, dus smal en hoog. Op tv staat
teletekst op een 4:3-beeld en zijn de tekens duidelijk breder. De kaart meet de
beschikbare ruimte, kiest daarbinnen de verhouding en rekt de tekst horizontaal
op — smal op een telefoon, breed op een groot scherm, en nooit breder dan tv.

## Niet van de NOS

Dit project is **niet van de NOS en heeft geen band met de NOS** — niet
aangesloten, niet goedgekeurd, niet gesponsord. De naam wordt alleen gebruikt om
te beschrijven welke dienst deze integratie ontsluit. De pagina's en het
lettertype komen van de NOS en blijven van hen; zie [MERK.md](MERK.md).

## Dank

Aan de NOS, die teletekst al sinds 1980 uitzendt en de pagina's ook als JSON
beschikbaar stelt.

## Meehelpen, forken en hergebruiken

Verbeteringen zijn welkom — er valt nog genoeg te doen: een echte
ondertitelingsmodus, beursinformatie uitlezen, of gewoon een scherper oog voor
waar het beeld nog afwijkt van de uitzending. Zie
[CONTRIBUTING.md](CONTRIBUTING.md).

Er staan tests bij (`python -m pytest tests -q`), zodat je kunt zien of je
wijziging iets breekt voordat je hem instuurt.

**Klonen en zelf verder bouwen mag, graag zelfs.** De code staat onder de
[MIT-licentie](LICENSE): je mag hem kopiëren, aanpassen, verspreiden en er zelfs
iets mee verdienen. Daar staat één voorwaarde tegenover, en die is niet
vrijblijvend — de licentie verplicht het:

> Houd het bestand `LICENSE` met de copyrightvermelding in je kopie.

**Neem je ook het icoon mee, dan geldt er meer.** Logo's vallen niet onder MIT,
dus daar staan aparte afspraken voor in [MERK.md](MERK.md): noem de bron met een
link hierheen, wek niet de indruk dat jouw versie de originele is, en maak een
eigen icoon zodra je iets wezenlijk anders bouwt. Vervang je het icoon door eigen
werk, dan heb je alleen met MIT te maken.

Heb je iets werkends gemaakt? Stuur een pull request. Dan heeft iedereen er wat
aan in plaats van dat het in een losse fork blijft hangen.
