"""NOS Teletekst voor Home Assistant.

Levert drie dingen: een eigen adres waarlangs de kaart pagina's kan ophalen
zonder CORS-probleem, de kaart zelf (automatisch geladen), en sensoren plus
diensten waarmee je teletekst in automatiseringen kunt gebruiken.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from . import tekst
from .api import (
    PaginaBestaatNiet,
    TeletekstFout,
    TeletekstView,
    geldige_pagina,
    haal_pagina,
)
from .const import (
    CONF_INTERVAL,
    CONF_PAGINAS,
    CONF_VERKEER,
    DIENST_PAGINA,
    DIENST_ZOEK,
    DOMAIN,
    FRONTEND_URL,
    KAART_BESTAND,
    MIN_INTERVAL,
    STANDAARD_INTERVAL,
    STANDAARD_PAGINAS,
    VERSIE,
)
from .coordinator import PaginaCoordinator, VerkeerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

# Statische paden en views kunnen maar een keer geregistreerd worden.
GEREGISTREERD = f"{DOMAIN}_geregistreerd"

KAART_URL = f"{FRONTEND_URL}/{KAART_BESTAND}"
KAART_URL_VERSIE = f"{KAART_URL}?v={VERSIE}"

# Zoeken haalt elke opgegeven pagina apart op. Daar zit een harde grens op: een
# zoekopdracht over honderden pagina's zou de NOS onnodig belasten.
ZOEK_MAX = 30

SCHEMA_PAGINA = vol.Schema({vol.Required("pagina"): cv.string})
SCHEMA_ZOEK = vol.Schema(
    {
        vol.Required("term"): cv.string,
        vol.Required("paginas"): vol.All(cv.ensure_list, [cv.string]),
    }
)


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
        _LOGGER.info("Lovelace staat in YAML-modus; kaart geladen via extra_module_url")

    paginas = entry.options.get(CONF_PAGINAS, STANDAARD_PAGINAS)
    interval = max(
        MIN_INTERVAL, int(entry.options.get(CONF_INTERVAL, STANDAARD_INTERVAL))
    )

    coordinators: dict[str, PaginaCoordinator] = {}
    for pagina in paginas:
        if not geldige_pagina(str(pagina)):
            _LOGGER.warning("Paginanummer %s overgeslagen: ongeldig", pagina)
            continue
        c = PaginaCoordinator(hass, entry, str(pagina), interval)
        await c.async_config_entry_first_refresh()
        coordinators[str(pagina)] = c

    # Verkeersinformatie is optioneel: het kost zes extra aanvragen per ronde.
    verkeer_c: VerkeerCoordinator | None = None
    if entry.options.get(CONF_VERKEER):
        verkeer_c = VerkeerCoordinator(hass, entry, interval)
        await verkeer_c.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinators": coordinators,
        "verkeer": verkeer_c,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _registreer_diensten(hass)
    entry.async_on_unload(entry.add_update_listener(_opnieuw_laden))
    return True


async def _opnieuw_laden(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Herlaad zodra de gevolgde pagina's of het interval veranderen."""
    await hass.config_entries.async_reload(entry.entry_id)


def _registreer_diensten(hass: HomeAssistant) -> None:
    """Registreer de diensten, eenmalig."""
    if hass.services.has_service(DOMAIN, DIENST_PAGINA):
        return

    async def _pagina_ophalen(call: ServiceCall) -> ServiceResponse:
        """Geef een teletekstpagina terug als platte tekst."""
        pagina = str(call.data["pagina"])
        try:
            ruw = await haal_pagina(hass, pagina)
        except PaginaBestaatNiet as err:
            raise HomeAssistantError(str(err)) from err
        except TeletekstFout as err:
            raise HomeAssistantError(str(err)) from err

        inhoud = ruw.get("content") or ""
        return {
            "pagina": pagina,
            "kop": tekst.kop(inhoud),
            "regels": tekst.naar_regels(inhoud),
            "koppen": tekst.koppen(inhoud),
            "tekst": tekst.naar_tekst(inhoud),
            "verwijzingen": tekst.paginaverwijzingen(inhoud),
            "volgende_pagina": ruw.get("nextPage") or None,
            "volgende_subpagina": ruw.get("nextSubPage") or None,
        }

    async def _zoeken(call: ServiceCall) -> ServiceResponse:
        """Zoek een woord in een opgegeven reeks pagina's."""
        term = str(call.data["term"]).lower()
        paginas = [str(p) for p in call.data["paginas"] if geldige_pagina(str(p))]
        if len(paginas) > ZOEK_MAX:
            _LOGGER.warning(
                "Zoekopdracht beperkt tot de eerste %s van de %s opgegeven paginas",
                ZOEK_MAX,
                len(paginas),
            )
            paginas = paginas[:ZOEK_MAX]

        async def _kijk(p: str) -> dict[str, Any] | None:
            try:
                ruw = await haal_pagina(hass, p)
            except TeletekstFout:
                return None
            regels = tekst.naar_regels(ruw.get("content") or "")
            treffers = [r for r in regels if term in r.lower()]
            return {"pagina": p, "regels": treffers} if treffers else None

        uitkomsten = await asyncio.gather(*(_kijk(p) for p in paginas))
        gevonden = [u for u in uitkomsten if u]
        return {
            "term": call.data["term"],
            "doorzocht": len(paginas),
            "aantal": sum(len(g["regels"]) for g in gevonden),
            "treffers": gevonden,
        }

    hass.services.async_register(
        DOMAIN,
        DIENST_PAGINA,
        _pagina_ophalen,
        schema=SCHEMA_PAGINA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        DIENST_ZOEK,
        _zoeken,
        schema=SCHEMA_ZOEK,
        supports_response=SupportsResponse.ONLY,
    )


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
            await resources.async_update_item(item["id"], {"url": KAART_URL_VERSIE})
            _LOGGER.debug("Resource bijgewerkt naar %s", KAART_URL_VERSIE)
        return True

    await resources.async_create_item({"res_type": "module", "url": KAART_URL_VERSIE})
    _LOGGER.debug("Resource aangemaakt: %s", KAART_URL_VERSIE)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder de config-entry.

    Het statische pad, de view en de kaart blijven tot een herstart bestaan;
    Home Assistant biedt geen manier om die weer los te koppelen.
    """
    gelukt = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if gelukt:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return gelukt


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
