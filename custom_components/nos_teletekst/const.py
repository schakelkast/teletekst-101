"""Vaste waarden voor de NOS Teletekst-integratie."""

DOMAIN = "nos_teletekst"

# Versie van de meegeleverde kaart. Ophogen bij elke wijziging aan het
# js-bestand, anders blijven browsers de gecachte versie gebruiken.
VERSIE = "1.0.1"

# Waar de meegeleverde kaart en het font vandaan komen.
FRONTEND_URL = "/nos_teletekst_frontend"
KAART_BESTAND = "nos-teletekst-card.js"

# De bron. Stuurt zelf geen CORS-headers, vandaar dat deze integratie de
# aanvraag serverkant doet.
API = "https://teletekst-data.nos.nl/json/{pagina}"
