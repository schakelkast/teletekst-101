"""Een sensor per gevolgde teletekstpagina.

De toestand is de eerste betekenisvolle regel van de pagina, zodat je hem in
een melding of een automatisering direct kunt gebruiken. De volledige tekst
staat in de attributen.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PaginaCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Maak een sensor voor elke gevolgde pagina."""
    coordinators: dict[str, PaginaCoordinator] = hass.data[DOMAIN][entry.entry_id][
        "coordinators"
    ]
    async_add_entities(
        TeletekstSensor(c, entry) for c in coordinators.values()
    )


class TeletekstSensor(CoordinatorEntity[PaginaCoordinator], SensorEntity):
    """Toont de kop van een teletekstpagina."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:television-classic"

    def __init__(self, coordinator: PaginaCoordinator, entry: ConfigEntry) -> None:
        """Koppel de sensor aan de pagina die de bijhouder ophaalt."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{coordinator.pagina}"
        self._attr_name = f"Pagina {coordinator.pagina}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="NOS Teletekst",
            manufacturer="NOS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://nos.nl/teletekst",
        )

    @property
    def native_value(self) -> str | None:
        """De eerste betekenisvolle regel van de pagina."""
        if not self.coordinator.data:
            return None
        # Een toestand mag maximaal 255 tekens zijn.
        return (self.coordinator.data.get("kop") or "")[:255] or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """De volledige pagina, voor gebruik in sjablonen en spraak."""
        d = self.coordinator.data or {}
        return {
            "pagina": d.get("pagina"),
            "regels": d.get("regels", []),
            "tekst": d.get("tekst", ""),
            "verwijzingen": d.get("verwijzingen", []),
            "vorige_pagina": d.get("vorige_pagina"),
            "volgende_pagina": d.get("volgende_pagina"),
            "volgende_subpagina": d.get("volgende_subpagina"),
        }
