# NOS Teletekst voor Home Assistant

Teletekst in Home Assistant, zoals het op tv en op nos.nl staat: 40×24 tekens,
blokgrafiek, de acht teletekstkleuren. Werkt op telefoon, tablet, breed scherm
en wandpaneel, en is met de vinger te bedienen.

## Installatie

**Via HACS** — open HACS, kies rechtsboven *Custom repositories*, plak
`https://github.com/schakelkast/teletekst-101` en kies type *Integration*. Installeer daarna *NOS Teletekst* en
herstart Home Assistant. Ga vervolgens naar **Instellingen → Apparaten en
diensten → Integratie toevoegen** en kies *NOS Teletekst*.

**Handmatig** — kopieer `custom_components/nos_teletekst` naar je
`config/custom_components/`, herstart, en voeg de integratie toe.

Er hoeft niets in `configuration.yaml` en er hoeft geen Lovelace-resource
toegevoegd te worden: de integratie regelt dat zelf.

## Gebruik

Voeg de kaart **NOS Teletekst** toe aan een dashboard, of met de hand:

```yaml
type: custom:nos-teletekst-card
page: "100"
```

### Opties

| optie | standaard | betekenis |
|---|---|---|
| `page` | `"100"` | beginpagina, subpagina mag ook: `100-2` |
| `refresh` | `60` | seconden tussen automatisch verversen, `0` zet het uit |
| `controls` | `true` | knoppenbalk onder of naast de pagina |
| `aspect` | `"auto"` | `web` = smal zoals nos.nl, `tv` = breed zoals 4:3, `auto` = past zich aan |
| `max_height` | `0` | vaste maximumhoogte in pixels, `0` = zelf de ruimte meten |

### Bedienen

- **vegen** links/rechts is vorige/volgende pagina, omhoog/omlaag is subpagina
- **tikken** op een paginanummer in de tekst, of op de gekleurde regel onderaan
- **cijferblok** verschijnt als je het paginaveld aanraakt: drie cijfers en hij
  springt, net als met de afstandsbediening
- **toetsenbord**: cijfers intikken, pijltjestoetsen bladeren, Esc sluit

## Hoe het werkt

De pagina's komen van `teletekst-data.nos.nl`, dezelfde bron als nos.nl/teletekst.
Die API stuurt geen CORS-headers, dus de browser mag hem niet rechtstreeks
aanroepen. De integratie haalt de pagina daarom op vanaf Home Assistant zelf en
biedt hem aan op `/api/nos_teletekst/<pagina>`, achter je gewone login.

De blokgrafiek zit in het teletekstfont van de NOS (Android VeraMono), dat
meegeleverd wordt en lokaal geserveerd — geen verbinding met een CDN.

Een teken-cel is op nos.nl 0,602 × 1,204 em, dus smal en hoog. Op tv staat
teletekst op een 4:3-beeld en zijn de tekens duidelijk breder. De kaart meet de
beschikbare ruimte, kiest daarbinnen de verhouding en rekt de tekst horizontaal
op — smal op een telefoon, breed op een groot scherm, en nooit breder dan tv.

## Niet van de NOS

Dit project is **niet van de NOS en heeft geen band met de NOS** — niet
aangesloten, niet goedgekeurd, niet gesponsord. De naam wordt alleen gebruikt om
te beschrijven welke dienst deze integratie ontsluit. De pagina's en het
lettertype komen van de NOS en blijven van hen; zie de [licentie](LICENSE).

## Dank

Aan de NOS, die teletekst al sinds 1980 uitzendt en de pagina's ook als JSON
beschikbaar stelt.

## Meehelpen, forken en hergebruiken

Verbeteringen zijn welkom — er valt nog genoeg te doen: meer paginasoorten netjes
tonen, een echte ondertitelingsmodus, of gewoon een scherper oog voor waar het
beeld nog afwijkt van de uitzending. Zie [CONTRIBUTING.md](CONTRIBUTING.md).

**Klonen en zelf verder bouwen mag, graag zelfs.** De code staat onder de
[MIT-licentie](LICENSE): je mag hem kopiëren, aanpassen, verspreiden en er zelfs
iets mee verdienen. Daar staat één voorwaarde tegenover, en die is niet
vrijblijvend — de licentie verplicht het:

> Houd het bestand `LICENSE` met de copyrightvermelding in je kopie.

**Neem je ook het icoon mee, dan geldt er meer.** Logo's vallen niet onder MIT,
dus daar staan aparte afspraken voor onderaan de [licentie](LICENSE): noem de
bron met een link hierheen, wek niet de indruk dat jouw versie de originele is,
en maak een eigen icoon zodra je iets wezenlijk anders bouwt. Vervang je het
icoon door eigen werk, dan heb je alleen met MIT te maken.

Heb je iets werkends gemaakt? Stuur een pull request. Dan heeft iedereen er wat
aan in plaats van dat het in een losse fork blijft hangen.
