"""Een sensor per gevolgde teletekstpagina.

De toestand is de eerste betekenisvolle regel van de pagina, zodat je hem in
een melding of een automatisering direct kunt gebruiken. De volledige tekst
staat in de attributen.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import eigen
from .const import (
    CONF_EIGEN,
    CONF_ENTITEITEN,
    DOMAIN,
    ENTITEIT_SENSOR,
    STANDAARD_ENTITEITEN,
)
from .coordinator import PaginaCoordinator, VerkeerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Maak een sensor voor elke gevolgde pagina."""
    gegevens = hass.data[DOMAIN][entry.entry_id]
    coordinators: dict[str, PaginaCoordinator] = gegevens["coordinators"]

    gekozen = entry.options.get(CONF_ENTITEITEN, STANDAARD_ENTITEITEN)
    entiteiten: list[SensorEntity] = []
    if ENTITEIT_SENSOR in gekozen:
        entiteiten += [TeletekstSensor(c, entry) for c in coordinators.values()]
    if gegevens.get("verkeer"):
        entiteiten.append(VerkeerSensor(gegevens["verkeer"], entry))

    # Sensoren die de gebruiker zelf heeft samengesteld.
    for definitie in entry.options.get(CONF_EIGEN) or []:
        pagina = str(definitie.get("pagina") or "")
        if pagina in coordinators:
            entiteiten.append(EigenSensor(coordinators[pagina], entry, definitie))
    async_add_entities(entiteiten)


class TeletekstSensor(CoordinatorEntity[PaginaCoordinator], SensorEntity):
    """Toont de kop van een teletekstpagina."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:television-classic"

    def __init__(self, coordinator: PaginaCoordinator, entry: ConfigEntry) -> None:
        """Koppel de sensor aan de pagina die de bijhouder ophaalt."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{coordinator.pagina}"
        # Naam via een vertaalsleutel, zodat een Engelse gebruiker "Page 101"
        # ziet en niet "Pagina 101".
        self._attr_translation_key = "pagina"
        self._attr_translation_placeholders = {"pagina": coordinator.pagina}
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
            "koppen": d.get("koppen", []),
            "koppen_markdown": d.get("koppen_markdown", ""),
            "tekst": d.get("tekst", ""),
            "verwijzingen": d.get("verwijzingen", []),
            "vorige_pagina": d.get("vorige_pagina"),
            "volgende_pagina": d.get("volgende_pagina"),
            "volgende_subpagina": d.get("volgende_subpagina"),
        }


class VerkeerSensor(CoordinatorEntity[VerkeerCoordinator], SensorEntity):
    """Het aantal files volgens de actuele verkeersinformatie."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:traffic-light"
    _attr_translation_key = "verkeer"
    _attr_native_unit_of_measurement = "files"
    _attr_state_class = "measurement"

    def __init__(self, coordinator: VerkeerCoordinator, entry: ConfigEntry) -> None:
        """Koppel de sensor aan de verkeerspagina's."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_verkeer"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="NOS Teletekst",
            manufacturer="NOS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://nos.nl/teletekst",
        )

    @property
    def native_value(self) -> int | None:
        """Hoeveel files er op dit moment staan."""
        d = self.coordinator.data
        return d.get("aantal_files") if d else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """De meldingen zelf, plus de optelsom."""
        d = self.coordinator.data or {}
        return {
            "totaal_km": d.get("totaal_km", 0),
            "totaal_minuten": d.get("totaal_minuten", 0),
            "wegen": d.get("wegen", []),
            "meldingen": d.get("meldingen", []),
            "bron": "ANWB via NOS Teletekst",
        }


class EigenSensor(CoordinatorEntity[PaginaCoordinator], SensorEntity):
    """Een sensor die de gebruiker zelf heeft samengesteld.

    Welke regel van een pagina interessant is, verschilt per persoon. Deze
    sensor leest uit wat er in de instellingen is aangewezen.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:text-search"

    def __init__(
        self,
        coordinator: PaginaCoordinator,
        entry: ConfigEntry,
        definitie: dict[str, Any],
    ) -> None:
        """Koppel de sensor aan zijn eigen leesregel."""
        super().__init__(coordinator)
        self._definitie = definitie
        self._attr_unique_id = f"{entry.entry_id}_eigen_{eigen.sleutel(definitie)}"
        self._attr_name = str(definitie.get("naam") or "Eigen sensor")
        eenheid = str(definitie.get("eenheid") or "").strip()
        if eenheid:
            self._attr_native_unit_of_measurement = eenheid
        if definitie.get("alleen_getal"):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="NOS Teletekst",
            manufacturer="NOS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://nos.nl/teletekst",
        )

    def _regels(self) -> list[str]:
        """Op nummer tellen gaat over het scherm, zoeken over de tekst.

        Bij een vast regelnummer moeten de lege regels meetellen, anders komt
        regel 5 niet uit op de vijfde rij die je ziet staan.
        """
        data = self.coordinator.data or {}
        if self._definitie.get("manier") == eigen.MANIER_REGEL:
            return data.get("alle_regels", [])
        return data.get("zoekregels") or data.get("regels", [])

    @property
    def native_value(self) -> str | float | None:
        """De waarde volgens de eigen leesregel."""
        return eigen.lees(self._regels(), self._definitie)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Laat zien waar de waarde vandaan komt, handig bij het afstellen."""
        return {
            "pagina": self._definitie.get("pagina"),
            "manier": self._definitie.get("manier"),
            "gevonden_regel": eigen.zoek_regel(self._regels(), self._definitie),
        }
