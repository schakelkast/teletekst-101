"""Bijhouden van één teletekstpagina."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import tekst
from .api import PaginaBestaatNiet, TeletekstFout, haal_pagina
from .const import DOMAIN, EVENEMENT_GEWIJZIGD

_LOGGER = logging.getLogger(__name__)


class PaginaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Haalt één pagina op en meldt het als de inhoud verandert."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        pagina: str,
        interval: int,
    ) -> None:
        """Zet de bijhouder op voor één paginanummer."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"Teletekst {pagina}",
            update_interval=timedelta(seconds=interval),
        )
        self.pagina = pagina
        self._vorige_tekst: str | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Haal de pagina op en zet hem om in platte tekst."""
        try:
            ruw = await haal_pagina(self.hass, self.pagina)
        except PaginaBestaatNiet as err:
            # Een niet-bestaande pagina gaat vanzelf niet bestaan; blijven
            # proberen heeft geen zin, maar de entiteit moet wel iets tonen.
            raise UpdateFailed(str(err)) from err
        except TeletekstFout as err:
            raise UpdateFailed(str(err)) from err

        inhoud = ruw.get("content") or ""
        plat = tekst.naar_tekst(inhoud)

        data = {
            "pagina": self.pagina,
            "kop": tekst.kop(inhoud),
            "regels": tekst.naar_regels(inhoud),
            "tekst": plat,
            "verwijzingen": tekst.paginaverwijzingen(inhoud),
            "vorige_pagina": ruw.get("prevPage") or None,
            "volgende_pagina": ruw.get("nextPage") or None,
            "vorige_subpagina": ruw.get("prevSubPage") or None,
            "volgende_subpagina": ruw.get("nextSubPage") or None,
            "snelkoppelingen": ruw.get("fastTextLinks") or [],
        }

        # Alleen melden bij een echte inhoudelijke wijziging. De eerste keer
        # ophalen is geen wijziging, anders vuurt hij bij elke herstart.
        if self._vorige_tekst is not None and plat != self._vorige_tekst:
            self.hass.bus.async_fire(
                EVENEMENT_GEWIJZIGD,
                {"pagina": self.pagina, "kop": data["kop"], "tekst": plat},
            )
            _LOGGER.debug("Pagina %s is gewijzigd", self.pagina)
        self._vorige_tekst = plat

        return data
