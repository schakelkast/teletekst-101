"""Bijhouden van één teletekstpagina."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import tekst, verkeer
from .api import PaginaBestaatNiet, TeletekstFout, haal_pagina
from .const import (
    DOMAIN,
    EVENEMENT_GEWIJZIGD,
    VERKEER_MAX_SUB,
    VERKEER_PAGINA,
)

# Zoveel subpagina's halen we hooguit op voor een eigen sensor.
SUB_MAX = 10

_LOGGER = logging.getLogger(__name__)


class PaginaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Haalt één pagina op en meldt het als de inhoud verandert."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        pagina: str,
        interval: int,
        met_subpaginas: bool = False,
    ) -> None:
        """Zet de bijhouder op voor één paginanummer.

        `met_subpaginas` haalt ook de vervolgpagina's op. Dat is nodig zodra er
        een eigen sensor op deze pagina zoekt: het weerrapport verdeelt de
        plaatsen over vijf subpagina's, dus wie alleen de eerste ophaalt vindt
        de helft niet.
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"Teletekst {pagina}",
            update_interval=timedelta(seconds=interval),
        )
        self.pagina = pagina
        self._met_subpaginas = met_subpaginas
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

        # Regels om in te zoeken: standaard alleen deze pagina, en met
        # subpagina's alles achter elkaar.
        zoekregels = tekst.naar_regels(inhoud)
        if self._met_subpaginas:
            volgende = ruw.get("nextSubPage")
            gezien = 0
            while volgende and gezien < SUB_MAX:
                try:
                    extra = await haal_pagina(self.hass, volgende)
                except TeletekstFout:
                    break
                zoekregels += tekst.naar_regels(extra.get("content") or "")
                volgende = extra.get("nextSubPage")
                gezien += 1

        data = {
            "pagina": self.pagina,
            # De tekenaar heeft de originele HTML nodig: daar zitten de kleuren
            # en de blokgrafiek in, die in platte tekst verloren gaan.
            "ruwe_inhoud": inhoud,
            "kop": tekst.kop(inhoud),
            "regels": tekst.naar_regels(inhoud),
            # Met de lege regels erin, zodat regelnummers overeenkomen met wat
            # je op het scherm telt. Zonder dit wijst "regel 5" naar de vijfde
            # niet-lege regel en dus naar iets anders dan de gebruiker bedoelt.
            "alle_regels": tekst.naar_regels(inhoud, houd_leeg=True),
            "koppen": tekst.koppen(inhoud),
            "koppen_markdown": tekst.koppen_markdown(inhoud),
            "tekst": plat,
            "zoekregels": zoekregels,
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


class VerkeerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Haalt de actuele verkeersinformatie op, inclusief alle subpagina's.

    Pagina 730 past niet op een scherm: de ANWB verdeelt de meldingen over een
    stuk of zes subpagina's. Die worden hier achter elkaar opgehaald en weer tot
    een lijst samengevoegd.
    """

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, interval: int
    ) -> None:
        """Zet de bijhouder op voor de verkeerspagina's."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Teletekst verkeer",
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Loop de subpagina's af en lees de meldingen uit."""
        regels: list[str] = []
        pagina: str | None = VERKEER_PAGINA
        gezien = 0

        while pagina and gezien < VERKEER_MAX_SUB:
            try:
                ruw = await haal_pagina(self.hass, pagina)
            except TeletekstFout as err:
                if gezien == 0:
                    raise UpdateFailed(str(err)) from err
                # Een losse subpagina die hapert mag de rest niet ongeldig maken.
                _LOGGER.debug("Subpagina %s overgeslagen: %s", pagina, err)
                break
            regels += tekst.naar_regels(ruw.get("content") or "")
            pagina = ruw.get("nextSubPage") or None
            gezien += 1

        meldingen = verkeer.lees(regels)
        return {
            "meldingen": meldingen,
            "subpaginas": gezien,
            **verkeer.samenvatting(meldingen),
        }
