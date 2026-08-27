"""Een teletekstpagina als afbeelding.

Hiermee is teletekst ook buiten een dashboard bruikbaar: meesturen in een
melding, op een e-ink schermpje zetten, of in een gewone plaatjeskaart tonen.
"""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import render
from .const import DOMAIN
from .coordinator import PaginaCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Maak een afbeelding voor elke gevolgde pagina."""
    coordinators: dict[str, PaginaCoordinator] = hass.data[DOMAIN][entry.entry_id][
        "coordinators"
    ]
    async_add_entities(
        TeletekstAfbeelding(hass, c, entry) for c in coordinators.values()
    )


class TeletekstAfbeelding(CoordinatorEntity[PaginaCoordinator], ImageEntity):
    """Tekent de pagina zoals hij op tv zou staan."""

    _attr_has_entity_name = True
    _attr_content_type = "image/png"

    def __init__(
        self, hass: HomeAssistant, coordinator: PaginaCoordinator, entry: ConfigEntry
    ) -> None:
        """Koppel de afbeelding aan de pagina die de bijhouder ophaalt."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = f"{entry.entry_id}_beeld_{coordinator.pagina}"
        self._attr_name = f"Pagina {coordinator.pagina} beeld"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="NOS Teletekst",
            manufacturer="NOS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://nos.nl/teletekst",
        )
        self._gemaakt_van: str | None = None
        self._png: bytes | None = None
        self._attr_image_last_updated = dt_util.utcnow()

    def _handle_coordinator_update(self) -> None:
        """Onthoud wanneer de pagina veranderde, zodat de cache verloopt."""
        inhoud = (self.coordinator.data or {}).get("tekst")
        if inhoud != self._gemaakt_van:
            self._attr_image_last_updated = dt_util.utcnow()
            self._png = None
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        """Geef de pagina terug als PNG.

        Tekenen kost rekentijd, dus het gebeurt buiten de gebeurtenislus en het
        resultaat wordt bewaard tot de pagina verandert.
        """
        data = self.coordinator.data or {}
        inhoud = data.get("ruwe_inhoud")
        if not inhoud:
            return None
        if self._png is not None and self._gemaakt_van == data.get("tekst"):
            return self._png

        self._png = await self.hass.async_add_executor_job(render.teken, inhoud)
        self._gemaakt_van = data.get("tekst")
        return self._png
