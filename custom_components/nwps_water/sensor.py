"""Sensors for NWPS Water integration."""
from __future__ import annotations
from .coordinator import NWPSDataCoordinator

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, AVAILABLE_PARAMETERS, CONF_PARAMETERS, CONF_STATION

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for a config entry."""
    # Retrieve the coordinator created in __init__.py
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    station_id = entry.data.get(CONF_STATION)
    parameters = entry.options.get(CONF_PARAMETERS)
    
    # If no parameters configured, apply defaults and persist them
    if not parameters:
        parameters = list(AVAILABLE_PARAMETERS.keys())
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_PARAMETERS: parameters}
        )

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
        
        # Set the device info so it groups correctly in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=f"NWPS {station_id}",
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