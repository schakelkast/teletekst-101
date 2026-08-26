"""Serverkant ophalen van een teletekstpagina.

De JSON-API van de NOS stuurt geen CORS-headers, dus de browser mag hem niet
rechtstreeks aanroepen. Deze view haalt de pagina op vanaf Home Assistant zelf
en geeft hem door aan de kaart, op hetzelfde adres en achter dezelfde login.
"""

from __future__ import annotations

import asyncio
import logging
import re
from http import HTTPStatus

from aiohttp import ClientError, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API

_LOGGER = logging.getLogger(__name__)

# Paginanummer of subpagina, bijvoorbeeld 101 of 100-2.
PAGINA = re.compile(r"^\d{3}(?:-\d{1,2})?$")

TIMEOUT = 15


class TeletekstView(HomeAssistantView):
    """Geeft een teletekstpagina terug als JSON."""

    url = "/api/nos_teletekst/{pagina}"
    name = "api:nos_teletekst"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Bewaar hass, zodat de view niet van de request-app hoeft af te hangen."""
        self.hass = hass

    async def get(self, request: web.Request, pagina: str) -> web.Response:
        """Haal de gevraagde pagina op bij de NOS."""
        if not PAGINA.match(pagina):
            return self.json(
                {"fout": "ongeldig paginanummer"}, HTTPStatus.BAD_REQUEST
            )

        sessie = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(TIMEOUT):
                antwoord = await sessie.get(
                    API.format(pagina=pagina), headers={"accept": "application/json"}
                )
                if antwoord.status == HTTPStatus.NOT_FOUND:
                    return self.json(
                        {"fout": f"pagina {pagina} bestaat niet"}, HTTPStatus.NOT_FOUND
                    )
                if antwoord.status != HTTPStatus.OK:
                    _LOGGER.warning(
                        "NOS gaf status %s voor pagina %s", antwoord.status, pagina
                    )
                    return self.json(
                        {"fout": f"NOS gaf status {antwoord.status}"},
                        HTTPStatus.BAD_GATEWAY,
                    )
                data = await antwoord.json(content_type=None)
        except TimeoutError:
            return self.json({"fout": "de NOS reageerde niet op tijd"}, HTTPStatus.GATEWAY_TIMEOUT)
        except ClientError as err:
            _LOGGER.warning("Ophalen van pagina %s mislukte: %s", pagina, err)
            return self.json({"fout": "de NOS is niet bereikbaar"}, HTTPStatus.BAD_GATEWAY)

        # De pagina ververst bij de NOS elke paar seconden.
        return self.json(data, headers={"cache-control": "max-age=5"})
