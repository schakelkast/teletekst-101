"""Diagnostische gegevens.

Bedoeld om aan een foutmelding toe te voegen: welke pagina's gevolgd worden en
of het ophalen lukt. Er zitten geen persoonlijke gegevens in — deze integratie
kent geen account en geen sleutel.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PaginaCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Geef de toestand van elke gevolgde pagina terug."""
    coordinators: dict[str, PaginaCoordinator] = (
        hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("coordinators", {})
    )

    paginas = {}
    for nummer, c in coordinators.items():
        d = c.data or {}
        paginas[nummer] = {
            "laatste_keer_gelukt": c.last_update_success,
            "interval_seconden": c.update_interval.total_seconds()
            if c.update_interval
            else None,
            "aantal_regels": len(d.get("regels", [])),
            "aantal_koppen": len(d.get("koppen", [])),
            "kop": d.get("kop"),
            "heeft_subpaginas": bool(d.get("volgende_subpagina")),
        }

    return {
        "opties": dict(entry.options),
        "paginas": paginas,
    }
