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
from .const import (
    CONF_INTERVAL,
    CONF_PAGINAS,
    CONF_TREFWOORDEN,
    DOMAIN,
    MIN_INTERVAL,
    STANDAARD_INTERVAL,
    STANDAARD_PAGINAS,
)


class NosTeletekstConfigFlow(ConfigFlow, domain=DOMAIN):
    """Voegt de integratie toe. Er is maar een exemplaar nodig."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Bevestig het toevoegen."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(
            title="NOS Teletekst",
            data={},
            options={
                CONF_PAGINAS: STANDAARD_PAGINAS,
                CONF_INTERVAL: STANDAARD_INTERVAL,
            },
        )

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
        return self.async_show_form(step_id="init", data_schema=schema, errors=fouten)
