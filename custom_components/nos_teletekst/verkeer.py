"""Verkeersinformatie uitlezen van de teletekstpagina's.

Pagina 730 is de actuele verkeersinformatie van de ANWB. Elke melding begint
met een streepje en loopt over meerdere regels door, dus de tekst moet eerst
weer aan elkaar geplakt worden voordat er iets uit te halen valt.

Voorbeeld van een melding zoals hij op de pagina staat:

    - A12 Duitse grens->Arnhem tussen knp.
    Oud-Dijk en Duiven 3 km,2 min.,
    wegwerkzaamheden,de rechterrijstrook
    is dicht.
"""

from __future__ import annotations

import re
from typing import TypedDict


class Melding(TypedDict):
    """Een uitgelezen verkeersmelding.

    Een eigen type in plaats van een losse dict: zo weet zowel de lezer als de
    typecontrole dat `km` een getal is en `weg` een tekst, en klopt het optellen
    van de kilometers aantoonbaar.
    """

    soort: str
    weg: str
    van: str | None
    naar: str | None
    km: int | None
    minuten: int | None
    tekst: str


# Regels die bij de pagina horen en niet bij een melding.
_OVERSLAAN = re.compile(
    r"^(nos teletekst|binnenland|buitenland|verkeersinformatie|actueel|prognose"
    r"|bron:|nieuws\s|verkeersbelemmerende)",
    re.IGNORECASE,
)

# Een kopje boven een groep meldingen: "Files:", "Afsluiting/Omleiding:".
_SECTIE = re.compile(r"^([A-Za-z/ ]{3,30}):$")

# Wegnummers: A12, N50, en soms met een letter erachter.
_WEG = re.compile(r"\b([AN]\d{1,3}[a-z]?)\b")
# De richting stopt bij "tussen", "bij", "ter hoogte" of het einde van de zin.
_RICHTING = re.compile(
    r"[AN]\d{1,3}[a-z]?\s+(.+?)->(.+?)"
    r"(?=\s+tussen|\s+bij|\s+ter|\s+vanaf|\s*[,.]|\s*$)"
)
_KM = re.compile(r"(\d+)\s*km")
_MINUTEN = re.compile(r"(\d+)\s*min")


def _samenvoegen(regels: list[str]) -> list[tuple[str, str]]:
    """Plak de doorgelopen regels weer aan elkaar tot hele meldingen.

    Geeft paren terug van (sectie, meldingstekst).
    """
    meldingen: list[tuple[str, str]] = []
    sectie = ""
    huidig: list[str] = []

    def afsluiten() -> None:
        if huidig:
            meldingen.append((sectie, " ".join(huidig).strip()))
            huidig.clear()

    for regel in regels:
        kaal = regel.strip()
        if not kaal or _OVERSLAAN.match(kaal):
            continue
        m = _SECTIE.match(kaal)
        if m:
            afsluiten()
            sectie = m.group(1).strip()
            continue
        if kaal.startswith("-"):
            afsluiten()
            huidig.append(kaal.lstrip("- ").strip())
        elif huidig:
            # Vervolgregel van de vorige melding.
            huidig.append(kaal)
    afsluiten()
    return meldingen


def lees(regels: list[str]) -> list[Melding]:
    """Zet de regels van een verkeerspagina om in losse meldingen."""
    uit: list[Melding] = []
    for sectie, melding in _samenvoegen(regels):
        weg = _WEG.search(melding)
        if not weg:
            continue

        richting = _RICHTING.search(melding)
        km = _KM.search(melding)
        minuten = _MINUTEN.search(melding)

        uit.append(
            Melding(
                soort=sectie or "Overig",
                weg=weg.group(1),
                van=richting.group(1).strip() if richting else None,
                naar=richting.group(2).strip() if richting else None,
                km=int(km.group(1)) if km else None,
                minuten=int(minuten.group(1)) if minuten else None,
                tekst=melding,
            )
        )
    return uit


def is_file(melding: Melding) -> bool:
    """Een file is een melding met een lengte; de rest is werk of afsluiting."""
    return melding["soort"].lower().startswith("file")


def samenvatting(meldingen: list[Melding]) -> dict[str, object]:
    """Tel de files bij elkaar op tot iets dat je in een melding kunt zetten."""
    files = [m for m in meldingen if is_file(m)]
    km = sum(m["km"] or 0 for m in files)
    minuten = sum(m["minuten"] or 0 for m in files)
    # A2 hoort voor A15 te staan, dus op nummer sorteren en niet op tekst.
    wegen = sorted(
        {m["weg"] for m in meldingen if m["weg"]},
        key=lambda w: (w[0], int(re.sub(r"\D", "", w) or 0), w),
    )
    return {
        "aantal_files": len(files),
        "totaal_km": km,
        "totaal_minuten": minuten,
        "wegen": wegen,
    }
