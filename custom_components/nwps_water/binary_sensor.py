"""Binary sensors for NWPS integration (flood alerts/warnings)."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BINARY_SENSORS, CONF_STATION, DEFAULT_SCAN_INTERVAL
from .coordinator import NWPSDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up binary sensors for a config entry."""
    station_id = entry.data.get(CONF_STATION)
    update_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    # Coordinator fetches station JSON (sensors use the parsed data)
    parameters = entry.options.get("parameters", [])
    coordinator = NWPSDataCoordinator(hass, station_id, parameters, update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("nwps_water", {})
    hass.data["nwps_water"][entry.entry_id] = coordinator

    entities = []
    for key, name in BINARY_SENSORS.items():
        entities.append(NWPSBinarySensor(coordinator, entry.entry_id, station_id, key, name))
    async_add_entities(entities)


class NWPSBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for NWPS flood condition."""

    def __init__(self, coordinator: NWPSDataCoordinator, entry_id: str, station_id: str, key: str, name: str):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._station_id = station_id
        self._key = key
        self._attr_name = f"{name} ({station_id})"
        self._attr_unique_id = f"nwps_{station_id}_{key}"

    def _category_active(self, category: str | None) -> bool:
        """Return True if category indicates any flooding (minor or greater)."""
        if not category:
            return False
        cat = str(category).lower()
        return cat in ("minor", "moderate", "major") or cat == "action"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        if self._key == "observed_flood":
            return self._category_active(data.get("observed_flood_category"))
        if self._key == "forecast_flood":
            return self._category_active(data.get("forecast_flood_category"))
        return False

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "station_id": self._station_id,
            "observed_flood_category": self.coordinator.data.get("observed_flood_category"),
            "forecast_flood_category": self.coordinator.data.get("forecast_flood_category"),
            "flood_thresholds": self.coordinator.data.get("flood_thresholds"),
            "raw": self.coordinator.data.get("_raw"),
            "attribution": self.coordinator.data.get("_device", {}).get("dataAttribution"),
        }