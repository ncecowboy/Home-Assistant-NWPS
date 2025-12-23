"""Binary sensors for NWPS integration (flood alerts/warnings)."""
from __future__ import annotations

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BINARY_SENSORS, CONF_STATION
from .coordinator import NWPSDataCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for a config entry."""
    # RECOVERY: Get the coordinator created in __init__.py
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data.get(CONF_STATION)

    entities = []
    for key, name in BINARY_SENSORS.items():
        entities.append(NWPSBinarySensor(coordinator, station_id, key, name))
    
    async_add_entities(entities)


class NWPSBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for NWPS flood condition."""

    # Entity naming is handled manually to create concise entity IDs
    _attr_has_entity_name = False
    # 'problem' makes the sensor turn Red in the UI when 'on'
    _attr_device_class = BinarySensorDeviceClass.PROBLEM 

    def __init__(self, coordinator: NWPSDataCoordinator, station_id: str, key: str, name: str):
        super().__init__(coordinator)
        self._station_id = station_id
        self._key = key
        # Set entity name to be station_id + name for concise entity IDs
        # e.g., "COCO3 Observed Flood Active" creates entity_id "binary_sensor.coco3_observed_flood_active"
        self._attr_name = f"{station_id} {name}"
        self._attr_unique_id = f"nwps_{station_id}_{key}"
        
        # Link to the same device as the regular sensors
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=coordinator.get_device_name(),
            manufacturer="NOAA NWPS",
        )

    def _category_active(self, category: str | None) -> bool:
        """Return True if category indicates any flooding."""
        if not category:
            return False
        cat = str(category).lower()
        # 'action' is a pre-flood stage, 'minor/moderate/major' are active floods
        return cat in ("minor", "moderate", "major", "action")

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        data = self.coordinator.data or {}
        if self._key == "observed_flood":
            return self._category_active(data.get("observed_flood_category"))
        if self._key == "forecast_flood":
            return self._category_active(data.get("forecast_flood_category"))
        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return details about the flood state."""
        data = self.coordinator.data or {}
        attrs = {
            "station_id": self._station_id,
            "flood_category": data.get(f"{self._key}_category"),
        }
        
        # Add flood thresholds if available
        if data.get("flood_minor_stage"):
            attrs["flood_minor"] = data.get("flood_minor_stage")
        if data.get("flood_moderate_stage"):
            attrs["flood_moderate"] = data.get("flood_moderate_stage")
        if data.get("flood_major_stage"):
            attrs["flood_major"] = data.get("flood_major_stage")
        
        # Add current stage if available for context
        if self._key == "observed_flood" and data.get("stage"):
            attrs["current_stage"] = data.get("stage")
        elif self._key == "forecast_flood" and data.get("forecast_stage"):
            attrs["forecast_stage"] = data.get("forecast_stage")
            
        return attrs