"""Instelstroom en instellingen."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import geldige_pagina
from .eigen import MANIER_REGEL, MANIER_ZOEK
from .eigen import sleutel as eigen_sleutel
from .const import (
    CONF_INTERVAL,
    CONF_PAGINAS,
    CONF_ENTITEITEN,
    CONF_TREFWOORDEN,
    CONF_VERKEER,
    CONF_WEGEN,
    DOMAIN,
    ENTITEIT_BEELD,
    ENTITEIT_SENSOR,
    MIN_INTERVAL,
    STANDAARD_ENTITEITEN,
    STANDAARD_INTERVAL,
    STANDAARD_PAGINAS,
)


# De bekendste pagina's, zodat je bij het installeren niet hoeft te raden.
SUGGESTIES = [
    ("101", "Nieuws"),
    ("104", "Binnenland"),
    ("120", "Buitenland"),
    ("501", "Economie"),
    ("601", "Sport"),
    ("702", "Weer"),
    ("801", "Voetbal"),
]
SUGGESTIE_PAGINAS = ["101"]


class NosTeletekstConfigFlow(ConfigFlow, domain=DOMAIN):
    """Voegt de integratie toe. Er is maar een exemplaar nodig."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Vraag meteen welke pagina's je wilt volgen.

        Dat kan ook achteraf bij Configureren, maar wie net installeert weet
        nog niet dat die knop bestaat en houdt anders alleen pagina 101 over.
        """
        fouten: dict[str, str] = {}
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            paginas = [p.strip() for p in user_input.get(CONF_PAGINAS, []) if p.strip()]
            if any(not geldige_pagina(p) for p in paginas):
                fouten[CONF_PAGINAS] = "ongeldige_pagina"
            elif not paginas:
                fouten[CONF_PAGINAS] = "geen_paginas"
            else:
                return self.async_create_entry(
                    title="NOS Teletekst",
                    data={},
                    options={
                        CONF_PAGINAS: paginas,
                        CONF_INTERVAL: STANDAARD_INTERVAL,
                        CONF_VERKEER: user_input.get(CONF_VERKEER, False),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_PAGINAS, default=list(SUGGESTIE_PAGINAS)): (
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=nr, label=f"{nr} - {naam}")
                                for nr, naam in SUGGESTIES
                            ],
                            multiple=True,
                            custom_value=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                ),
                vol.Optional(CONF_VERKEER, default=False): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=fouten)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Instellingen achteraf aanpassen."""
        return NosTeletekstOptionsFlow()


class NosTeletekstOptionsFlow(OptionsFlow):
    """Kiezen welke pagina's een sensor krijgen, en hoe vaak."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Laat kiezen wat je wilt aanpassen."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["instellingen", "sensor_toevoegen", "sensor_verwijderen"],
        )

    async def async_step_instellingen(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Toon en verwerk de instellingen."""
        fouten: dict[str, str] = {}

        if user_input is not None:
            paginas = [p.strip() for p in user_input[CONF_PAGINAS] if p.strip()]
            ongeldig = [p for p in paginas if not geldige_pagina(p)]
            if ongeldig:
                fouten[CONF_PAGINAS] = "ongeldige_pagina"
            elif not paginas:
                fouten[CONF_PAGINAS] = "geen_paginas"
            else:
                return self.async_create_entry(
                    data={
                        CONF_PAGINAS: paginas,
                        CONF_INTERVAL: user_input[CONF_INTERVAL],
                        CONF_TREFWOORDEN: [
                            t.strip()
                            for t in user_input.get(CONF_TREFWOORDEN, [])
                            if t.strip()
                        ],
                        CONF_ENTITEITEN: user_input.get(
                            CONF_ENTITEITEN, STANDAARD_ENTITEITEN
                        ),
                        CONF_VERKEER: user_input.get(CONF_VERKEER, False),
                        CONF_WEGEN: [
                            w.strip().upper()
                            for w in user_input.get(CONF_WEGEN, [])
                            if w.strip()
                        ],
                    }
                )

        huidig = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PAGINAS,
                    default=list(huidig.get(CONF_PAGINAS, STANDAARD_PAGINAS)),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[],
                        multiple=True,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_ENTITEITEN,
                    default=list(huidig.get(CONF_ENTITEITEN, STANDAARD_ENTITEITEN)),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=ENTITEIT_SENSOR, label="Sensor met de tekst"
                            ),
                            selector.SelectOptionDict(
                                value=ENTITEIT_BEELD, label="Afbeelding van de pagina"
                            ),
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_TREFWOORDEN,
                    default=list(huidig.get(CONF_TREFWOORDEN, [])),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[],
                        multiple=True,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_VERKEER,
                    default=huidig.get(CONF_VERKEER, False),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_WEGEN,
                    default=list(huidig.get(CONF_WEGEN, [])),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[],
                        multiple=True,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(
                    CONF_INTERVAL,
                    default=huidig.get(CONF_INTERVAL, STANDAARD_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_INTERVAL,
                        max=3600,
                        step=30,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="instellingen", data_schema=schema, errors=fouten
        )

    async def async_step_sensor_toevoegen(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Zelf een sensor samenstellen uit een regel van een pagina."""
        fouten: dict[str, str] = {}

        if user_input is not None:
            pagina = str(user_input["pagina"]).strip()
            if not geldige_pagina(pagina):
                fouten["pagina"] = "ongeldige_pagina"
            elif not str(user_input.get("naam", "")).strip():
                fouten["naam"] = "geen_naam"
            elif user_input["manier"] == MANIER_ZOEK and not str(
                user_input.get("zoekwoord", "")
            ).strip():
                fouten["zoekwoord"] = "geen_zoekwoord"
            else:
                nieuw = {
                    "naam": str(user_input["naam"]).strip(),
                    "pagina": pagina,
                    "manier": user_input["manier"],
                    "regel": int(user_input.get("regel") or 1),
                    "zoekwoord": str(user_input.get("zoekwoord") or "").strip(),
                    "alleen_getal": bool(user_input.get("alleen_getal")),
                    "eenheid": str(user_input.get("eenheid") or "").strip(),
                }
                bestaand = list(self.config_entry.options.get(CONF_EIGEN) or [])
                # Dezelfde naam vervangt de vorige, zodat aanpassen ook werkt.
                bestaand = [
                    d for d in bestaand if eigen_sleutel(d) != eigen_sleutel(nieuw)
                ]
                bestaand.append(nieuw)
                return self.async_create_entry(
                    data={**self.config_entry.options, CONF_EIGEN: bestaand}
                )

        schema = vol.Schema(
            {
                vol.Required("naam"): selector.TextSelector(),
                vol.Required("pagina", default="702"): selector.TextSelector(),
                vol.Required("manier", default=MANIER_ZOEK): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=MANIER_ZOEK, label="De eerste regel met een woord erin"
                            ),
                            selector.SelectOptionDict(
                                value=MANIER_REGEL, label="Een vaste regel, op nummer"
                            ),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional("zoekwoord", default=""): selector.TextSelector(),
                vol.Optional("regel", default=1): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=25, step=1, mode="box")
                ),
                vol.Optional("alleen_getal", default=False): selector.BooleanSelector(),
                vol.Optional("eenheid", default=""): selector.TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="sensor_toevoegen", data_schema=schema, errors=fouten
        )

    async def async_step_sensor_verwijderen(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Eigen sensoren weghalen."""
        bestaand = list(self.config_entry.options.get(CONF_EIGEN) or [])
        if not bestaand:
            return self.async_abort(reason="geen_eigen_sensoren")

        if user_input is not None:
            houden = [
                d
                for d in bestaand
                if eigen_sleutel(d) not in set(user_input.get("weg", []))
            ]
            return self.async_create_entry(
                data={**self.config_entry.options, CONF_EIGEN: houden}
            )

        schema = vol.Schema(
            {
                vol.Optional("weg", default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=eigen_sleutel(d),
                                label=f"{d.get('naam')} (pagina {d.get('pagina')})",
                            )
                            for d in bestaand
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="sensor_verwijderen", data_schema=schema)
