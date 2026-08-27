"""Eigen sensoren: zelf bepalen wat er van een pagina wordt uitgelezen.

Teletekst staat vol met dingen waar iemand precies op zit te wachten: de
temperatuur in De Bilt, de stand van een club, de waterstand bij Lobith. Welke
regel dat is verschilt per persoon, dus in plaats van dat te raden kun je hier
zelf een regel aanwijzen.

Twee manieren, allebei zonder dat je iets van sjablonen hoeft te weten:

- **regel**: neem regel 5 van de pagina.
- **zoek**: neem de eerste regel waar een woord in staat.

Van die regel kun je de hele tekst nemen, of alleen het eerste getal.
"""

from __future__ import annotations

import re
from typing import Any

MANIER_REGEL = "regel"
MANIER_ZOEK = "zoek"

# Een getal, eventueel met komma of punt als decimaalteken, ook negatief.
_GETAL = re.compile(r"-?\d+(?:[.,]\d+)?")


def zoek_regel(regels: list[str], definitie: dict[str, Any]) -> str | None:
    """Zoek de regel op die bij deze definitie hoort."""
    manier = definitie.get("manier", MANIER_ZOEK)

    if manier == MANIER_REGEL:
        nummer = int(definitie.get("regel") or 1)
        # Mensen tellen vanaf 1.
        if 1 <= nummer <= len(regels):
            return regels[nummer - 1]
        return None

    woord = str(definitie.get("zoekwoord") or "").lower()
    if not woord:
        return None
    for regel in regels:
        if woord in regel.lower():
            return regel
    return None


def waarde_uit(regel: str | None, alleen_getal: bool) -> str | float | None:
    """Haal de waarde uit de gevonden regel."""
    if regel is None:
        return None
    if not alleen_getal:
        return regel.strip()[:255]

    m = _GETAL.search(regel)
    if not m:
        return None
    getal = m.group(0).replace(",", ".")
    try:
        uit = float(getal)
    except ValueError:
        return None
    # Hele getallen niet als 21.0 tonen.
    return int(uit) if uit.is_integer() else uit


def lees(regels: list[str], definitie: dict[str, Any]) -> str | float | None:
    """Bepaal de waarde van een eigen sensor."""
    return waarde_uit(
        zoek_regel(regels, definitie), bool(definitie.get("alleen_getal"))
    )


def sleutel(definitie: dict[str, Any]) -> str:
    """Een vaste sleutel per sensor, zodat hij zijn geschiedenis houdt."""
    naam = str(definitie.get("naam") or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", naam).strip("_") or "eigen"
