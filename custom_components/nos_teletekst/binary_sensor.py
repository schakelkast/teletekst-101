"""Trefwoord-bewaking.

Je geeft woorden op, en zodra zo'n woord op een van de gevolgde pagina's
opduikt gaat de bijbehorende sensor aan. Zo kun je op nieuws over een onderwerp
reageren zonder zelf sjablonen te schrijven.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TREFWOORDEN, CONF_WEGEN, DOMAIN
from .coordinator import PaginaCoordinator, VerkeerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Maak een sensor voor elk opgegeven trefwoord."""
    gegevens = hass.data[DOMAIN][entry.entry_id]
    coordinators: dict[str, PaginaCoordinator] = gegevens["coordinators"]
    trefwoorden = entry.options.get(CONF_TREFWOORDEN) or []

    entiteiten: list[BinarySensorEntity] = [
        TrefwoordSensor(entry, coordinators, woord)
        for woord in trefwoorden
        if str(woord).strip()
    ]

    verkeer_c: VerkeerCoordinator | None = gegevens.get("verkeer")
    if verkeer_c:
        for weg in entry.options.get(CONF_WEGEN) or []:
            if str(weg).strip():
                entiteiten.append(WegSensor(entry, verkeer_c, str(weg).strip()))

    async_add_entities(entiteiten)


class TrefwoordSensor(BinarySensorEntity):
    """Gaat aan zodra het trefwoord op een gevolgde pagina staat."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:magnify"
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        coordinators: dict[str, PaginaCoordinator],
        woord: str,
    ) -> None:
        """Koppel de sensor aan alle gevolgde pagina's tegelijk."""
        self._woord = str(woord).strip()
        self._coordinators = coordinators
        self._attr_unique_id = f"{entry.entry_id}_trefwoord_{self._woord.lower()}"
        self._attr_name = f"Trefwoord {self._woord}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="NOS Teletekst",
            manufacturer="NOS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://nos.nl/teletekst",
        )

    async def async_added_to_hass(self) -> None:
        """Luister naar elke pagina, niet naar één."""
        await super().async_added_to_hass()
        for c in self._coordinators.values():
            self.async_on_remove(c.async_add_listener(self._bijgewerkt))

    @callback
    def _bijgewerkt(self) -> None:
        self.async_write_ha_state()

    def _treffers(self) -> list[dict[str, Any]]:
        """Alle regels waarin het trefwoord voorkomt, per pagina."""
        woord = self._woord.lower()
        uit: list[dict[str, Any]] = []
        for nummer, c in self._coordinators.items():
            regels = [
                r for r in (c.data or {}).get("regels", []) if woord in r.lower()
            ]
            if regels:
                uit.append({"pagina": nummer, "regels": regels})
        return uit

    @property
    def available(self) -> bool:
        """Alleen bruikbaar als minstens een pagina met succes is opgehaald."""
        return any(c.last_update_success for c in self._coordinators.values())

    @property
    def is_on(self) -> bool:
        """Staat het trefwoord ergens op de gevolgde pagina's?"""
        return bool(self._treffers())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Waar het woord gevonden is, en in welke regels."""
        treffers = self._treffers()
        return {
            "trefwoord": self._woord,
            "paginas": [t["pagina"] for t in treffers],
            "regels": [r for t in treffers for r in t["regels"]],
            "treffers": treffers,
        }


class WegSensor(CoordinatorEntity[VerkeerCoordinator], BinarySensorEntity):
    """Gaat aan zodra er een melding staat voor deze weg."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:road-variant"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self, entry: ConfigEntry, coordinator: VerkeerCoordinator, weg: str
    ) -> None:
        """Koppel de sensor aan een wegnummer, bijvoorbeeld A15."""
        super().__init__(coordinator)
        self._weg = weg.upper()
        self._attr_unique_id = f"{entry.entry_id}_weg_{self._weg.lower()}"
        self._attr_name = f"Verkeer {self._weg}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="NOS Teletekst",
            manufacturer="NOS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://nos.nl/teletekst",
        )

    def _mijn_meldingen(self) -> list[dict[str, Any]]:
        d = self.coordinator.data or {}
        return [
            m for m in d.get("meldingen", []) if str(m.get("weg", "")).upper() == self._weg
        ]

    @property
    def is_on(self) -> bool:
        """Staat er iets op deze weg?"""
        return bool(self._mijn_meldingen())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Wat er precies aan de hand is, en hoeveel vertraging."""
        meldingen = self._mijn_meldingen()
        files = [m for m in meldingen if str(m.get("soort", "")).lower().startswith("file")]
        return {
            "weg": self._weg,
            "aantal_meldingen": len(meldingen),
            "aantal_files": len(files),
            "km": sum(int(m["km"]) for m in files if m.get("km")),
            "minuten": sum(int(m["minuten"]) for m in files if m.get("minuten")),
            "meldingen": meldingen,
        }
