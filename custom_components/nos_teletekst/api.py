"""Ophalen van teletekstpagina's bij de NOS.

De JSON-API van de NOS stuurt geen CORS-headers, dus de browser mag hem niet
rechtstreeks aanroepen. Alles loopt daarom via deze module: de kaart via een
eigen adres, en de sensoren en diensten rechtstreeks.
"""

from __future__ import annotations

import asyncio
import logging
import re
from http import HTTPStatus
from typing import Any

from aiohttp import ClientError, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API, TIMEOUT

_LOGGER = logging.getLogger(__name__)

# Paginanummer of subpagina, bijvoorbeeld 101 of 100-2.
PAGINA = re.compile(r"^\d{3}(?:-\d{1,2})?$")


class TeletekstFout(Exception):
    """Ophalen mislukte."""


class PaginaBestaatNiet(TeletekstFout):
    """De NOS kent deze pagina niet."""


def geldige_pagina(pagina: str) -> bool:
    """Controleer of dit een bruikbaar paginanummer is."""
    return bool(PAGINA.match(str(pagina)))


async def haal_pagina(hass: HomeAssistant, pagina: str) -> dict[str, Any]:
    """Haal één teletekstpagina op.

    Raises:
        PaginaBestaatNiet: de NOS geeft 404.
        TeletekstFout: netwerkfout of een onverwacht antwoord.
    """
    if not geldige_pagina(pagina):
        raise TeletekstFout(f"ongeldig paginanummer: {pagina}")

    sessie = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(TIMEOUT):
            antwoord = await sessie.get(
                API.format(pagina=pagina), headers={"accept": "application/json"}
            )
            if antwoord.status == HTTPStatus.NOT_FOUND:
                raise PaginaBestaatNiet(f"pagina {pagina} bestaat niet")
            if antwoord.status != HTTPStatus.OK:
                raise TeletekstFout(f"NOS gaf status {antwoord.status}")
            return await antwoord.json(content_type=None)
    except TimeoutError as err:
        raise TeletekstFout("de NOS reageerde niet op tijd") from err
    except ClientError as err:
        raise TeletekstFout(f"de NOS is niet bereikbaar: {err}") from err


class TeletekstView(HomeAssistantView):
    """Geeft een teletekstpagina terug als JSON, voor de kaart."""

    url = "/api/nos_teletekst/{pagina}"
    name = "api:nos_teletekst"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Bewaar hass, zodat de view niet van de request-app hoeft af te hangen."""
        self.hass = hass

    async def get(self, request: web.Request, pagina: str) -> web.Response:
        """Haal de gevraagde pagina op bij de NOS."""
        try:
            data = await haal_pagina(self.hass, pagina)
        except PaginaBestaatNiet as err:
            return self.json({"fout": str(err)}, HTTPStatus.NOT_FOUND)
        except TeletekstFout as err:
            _LOGGER.warning("Ophalen van pagina %s mislukte: %s", pagina, err)
            return self.json({"fout": str(err)}, HTTPStatus.BAD_GATEWAY)

        # De pagina ververst bij de NOS elke paar seconden.
        return self.json(data, headers={"cache-control": "max-age=5"})
