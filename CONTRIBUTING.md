# Meehelpen

Leuk dat je meedoet. Een paar dingen die het makkelijker maken.

## Melden wat er misgaat
Zet er het paginanummer bij waar het misgaat, je Home Assistant-versie en op wat
voor scherm je kijkt (telefoon, tablet, wandpaneel, breed scherm). Een schermfoto
zegt bij dit project vaak meer dan een beschrijving.

## Zelf iets veranderen
De hele integratie is klein en zonder bouwstap: bewerk de bestanden, kopieer
`custom_components/nos_teletekst` naar je eigen `config/custom_components/` en
herstart Home Assistant.

**Verander je iets aan de kaart?** Hoog dan `VERSIE` op in `const.py`. Dat getal
staat in de resource-URL, en zonder die wijziging blijft de browser de oude kaart
laden — je ziet je aanpassing dan niet en gaat naar de verkeerde oorzaak zoeken.

### Waar wat zit
- `api.py` — haalt de pagina op bij de NOS. De API stuurt geen CORS-headers,
  vandaar dat dit serverkant gebeurt.
- `__init__.py` — registreert de view, serveert `frontend/` en zet de kaart in de
  Lovelace-resources.
- `frontend/nos-teletekst-card.js` — de kaart: opmaak, schalen en bediening.

### Twee dingen die niet vanzelfsprekend zijn
De pagina wordt horizontaal opgerekt met `scaleX`, omdat een teken op tv breder
is dan op nos.nl. Dat rekken legt de rand tussen twee gekleurde vlakken op een
halve pixel, waar de browser een haarlijn tekent; elk vlakje krijgt daarom een
fractie extra achtergrond met een even grote negatieve marge.

De kaart wordt als Lovelace-resource geregistreerd en niet met
`add_extra_js_url`. Dat laatste laadt asynchroon, waardoor Lovelace de kaart soms
al wil opbouwen voordat het element bestaat en er een foutkaart blijft staan tot
je herlaadt.

## Taal
Code en commentaar zijn Nederlands, net als teletekst zelf. Houd dat aan, dan
blijft het een geheel.

## Forken
Een eigen fork maken en die kant op verder bouwen mag zonder te vragen. De
MIT-licentie stelt één harde voorwaarde: het `LICENSE`-bestand met de
copyrightvermelding blijft in je kopie staan. En noem het origineel even in je
README — dat kost een regel en houdt zichtbaar waar het vandaan komt.

Werkt je verbetering? Doe er een pull request van. Een fork die stilletjes beter
is dan het origineel helpt de volgende persoon niet.
