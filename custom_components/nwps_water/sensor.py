"""Sensors for NWPS Water integration."""
from __future__ import annotations
from .coordinator import NWPSDataCoordinator

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, AVAILABLE_PARAMETERS, CONF_PARAMETERS, CONF_STATION

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for a config entry."""
    # Retrieve the coordinator created in __init__.py
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    station_id = entry.data.get(CONF_STATION)
    parameters = entry.options.get(CONF_PARAMETERS, list(AVAILABLE_PARAMETERS.keys()))

    entities = [
        NWPSWaterSensor(coordinator, station_id, param)
        for param in parameters
    ]

    async_add_entities(entities)


class NWPSWaterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a NWPS parameter as a sensor."""

    # This tells HA to use the Device Name + the translated Entity Name
    _attr_has_entity_name = True

    def __init__(self, coordinator: NWPSDataCoordinator, station_id: str, parameter: str):
        super().__init__(coordinator)
        self._station_id = station_id
        self._parameter = parameter
        
        info = AVAILABLE_PARAMETERS.get(parameter, {})
        
        # The name now only describes the sensor, not the station
        self._attr_name = info.get('name', parameter)
        self._attr_unique_id = f"nwps_{station_id}_{parameter}"
        self._attr_native_unit_of_measurement = info.get("unit")
        
        # Set state class for numeric sensors that measure values
        if parameter in ("stage", "flow", "forecast_stage", "forecast_flow", 
                         "flood_minor_stage", "flood_moderate_stage", "flood_major_stage",
                         "elevation", "river_mile"):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Set entity category for diagnostic/metadata sensors
        if parameter in ("latitude", "longitude", "elevation", "river_mile",
                         "flood_minor_stage", "flood_moderate_stage", "flood_major_stage"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
        # Set device class where applicable
        if parameter in ("latitude", "longitude"):
            # No specific device class for coordinates, but they're diagnostic
            pass
        elif parameter in ("elevation"):
            self._attr_device_class = SensorDeviceClass.DISTANCE
        
        # Set icon based on parameter type
        if parameter in ("stage", "forecast_stage"):
            self._attr_icon = "mdi:waves-arrow-up"
        elif parameter in ("flow", "forecast_flow"):
            self._attr_icon = "mdi:waves"
        elif parameter in ("observed_flood_category", "forecast_flood_category"):
            self._attr_icon = "mdi:alert-circle"
        elif parameter in ("flood_minor_stage", "flood_moderate_stage", "flood_major_stage"):
            self._attr_icon = "mdi:alert"
        elif parameter in ("latitude", "longitude"):
            self._attr_icon = "mdi:map-marker"
        elif parameter in ("elevation"):
            self._attr_icon = "mdi:elevation-rise"
        elif parameter in ("river_mile"):
            self._attr_icon = "mdi:map-marker-distance"
        
        # Get station name from coordinator data, with fallback to station_id
        station_name = coordinator.data.get("_device", {}).get("name") if coordinator.data else None
        device_name = f"{station_id} - {station_name}" if station_name else station_id
        
        # Set the device info so it groups correctly in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=device_name,
            manufacturer="NOAA NWPS",
            model="NWPS Station",
            configuration_url="https://api.water.noaa.gov/nwps/v1/docs/",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._parameter)

    @property
    def extra_state_attributes(self) -> dict:
        """Return entity specific state attributes."""
        data = self.coordinator.data or {}
        return {
            "station_id": self._station_id,
            "parameter": self._parameter,
            "raw_payload": data.get("_raw"),
            "attribution": "Data provided by NOAA NWPS",
        }