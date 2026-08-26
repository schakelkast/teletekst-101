"""NOS Teletekst voor Home Assistant.

Levert twee dingen: een eigen adres waarlangs de kaart teletekstpagina's kan
ophalen zonder CORS-probleem, en de kaart zelf. De kaart wordt automatisch als
Lovelace-resource geregistreerd, dus handmatig toevoegen hoeft niet.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import TeletekstView
from .const import DOMAIN, FRONTEND_URL, KAART_BESTAND, VERSIE

_LOGGER = logging.getLogger(__name__)

# Statische paden en views kunnen maar een keer geregistreerd worden.
GEREGISTREERD = f"{DOMAIN}_geregistreerd"

KAART_URL = f"{FRONTEND_URL}/{KAART_BESTAND}"
KAART_URL_VERSIE = f"{KAART_URL}?v={VERSIE}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet de integratie op."""
    if not hass.data.get(GEREGISTREERD):
        map_ = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL, str(map_), True)]
        )
        hass.http.register_view(TeletekstView(hass))
        hass.data[GEREGISTREERD] = True

    if not await _zet_resource(hass):
        # Lovelace in YAML-modus: dan kan de resource niet gezet worden en is
        # dit de enige manier om de kaart alsnog te laden.
        frontend.add_extra_js_url(hass, KAART_URL_VERSIE)
        _LOGGER.info(
            "Lovelace staat in YAML-modus; kaart geladen via extra_module_url"
        )

    return True


async def _zet_resource(hass: HomeAssistant) -> bool:
    """Zorg dat de kaart als Lovelace-resource geregistreerd staat.

    Een resource laadt gegarandeerd voordat het dashboard zijn kaarten opbouwt.
    Via extra_module_url is dat niet gegarandeerd: dan kan Lovelace de kaart net
    te vroeg willen maken en blijft er een foutkaart staan tot je herlaadt.
    """
    resources = getattr(hass.data.get("lovelace"), "resources", None)
    if resources is None or not hasattr(resources, "async_create_item"):
        return False

    if hasattr(resources, "async_get_info"):
        await resources.async_get_info()

    for item in resources.async_items():
        if str(item.get("url", "")).split("?")[0] != KAART_URL:
            continue
        if item["url"] != KAART_URL_VERSIE:
            await resources.async_update_item(
                item["id"], {"url": KAART_URL_VERSIE}
            )
            _LOGGER.debug("Resource bijgewerkt naar %s", KAART_URL_VERSIE)
        return True

    await resources.async_create_item(
        {"res_type": "module", "url": KAART_URL_VERSIE}
    )
    _LOGGER.debug("Resource aangemaakt: %s", KAART_URL_VERSIE)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder de config-entry.

    Het statische pad en de view blijven tot een herstart bestaan; Home Assistant
    biedt geen manier om die weer los te koppelen.
    """
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ruim de Lovelace-resource op als de integratie wordt verwijderd."""
    resources = getattr(hass.data.get("lovelace"), "resources", None)
    if resources is None or not hasattr(resources, "async_delete_item"):
        return
    if hasattr(resources, "async_get_info"):
        await resources.async_get_info()
    for item in list(resources.async_items()):
        if str(item.get("url", "")).split("?")[0] == KAART_URL:
            await resources.async_delete_item(item["id"])
            _LOGGER.debug("Resource verwijderd: %s", item["url"])
