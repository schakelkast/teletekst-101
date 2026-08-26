"""Vaste waarden voor de NOS Teletekst-integratie."""

DOMAIN = "nos_teletekst"

# Versie van de meegeleverde kaart. Ophogen bij elke wijziging aan het
# js-bestand, anders blijven browsers de gecachte versie gebruiken.
VERSIE = "1.3.0"

# Waar de meegeleverde kaart en het font vandaan komen.
FRONTEND_URL = "/nos_teletekst_frontend"
KAART_BESTAND = "nos-teletekst-card.js"

# De bron. Stuurt zelf geen CORS-headers, vandaar dat deze integratie de
# aanvraag serverkant doet.
API = "https://teletekst-data.nos.nl/json/{pagina}"
TIMEOUT = 15

# Instellingen
CONF_PAGINAS = "paginas"
CONF_INTERVAL = "interval"
CONF_TREFWOORDEN = "trefwoorden"
CONF_VERKEER = "verkeer"
CONF_WEGEN = "wegen"

# Standaard alleen de nieuwspagina. Teletekst ververst een paar keer per uur,
# dus vaker dan dit ophalen levert niets op en belast de NOS onnodig.
STANDAARD_PAGINAS = ["101"]
STANDAARD_INTERVAL = 300

# Actuele verkeersinformatie van de ANWB, met subpaginas.
VERKEER_PAGINA = "730"
VERKEER_MAX_SUB = 10
MIN_INTERVAL = 60

# Diensten
DIENST_PAGINA = "pagina_ophalen"
DIENST_ZOEK = "zoeken"

# Wordt afgevuurd zodra een gevolgde pagina inhoudelijk verandert.
EVENEMENT_GEWIJZIGD = f"{DOMAIN}_pagina_gewijzigd"
