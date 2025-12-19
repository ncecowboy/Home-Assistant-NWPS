"""Sensors for NWPS Water integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AVAILABLE_PARAMETERS,
    CONF_PARAMETERS,
    CONF_STATION,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import NWPSDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for a config entry."""
    station_id = entry.data.get(CONF_STATION)
    parameters = entry.options.get(CONF_PARAMETERS, list(AVAILABLE_PARAMETERS.keys()))
    update_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    coordinator = NWPSDataCoordinator(hass, station_id, parameters, update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("nwps_water", {})
    hass.data["nwps_water"][entry.entry_id] = coordinator

    entities: list[SensorEntity] = []
    for param in parameters:
        # If unknown param, still create a sensor so user can inspect raw payloads
        entities.append(NWPSWaterSensor(coordinator, entry.entry_id, station_id, param))

    async_add_entities(entities)


class NWPSWaterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a NWPS parameter as a sensor."""

    def __init__(self, coordinator: NWPSDataCoordinator, entry_id: str, station_id: str, parameter: str):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._entry_id = entry_id
        self._station_id = station_id
        self._parameter = parameter
        info = AVAILABLE_PARAMETERS.get(parameter, {})
        self._attr_name = f"{info.get('name', parameter)} ({station_id})"
        self._attr_unique_id = f"nwps_{station_id}_{parameter}"
        self._attr_native_unit_of_measurement = info.get("unit")

    @property
    def device_info(self) -> DeviceInfo | None:
        device_meta = self.coordinator.data.get("_device") or {}
        identifiers = {("nwps_water", device_meta.get("station_id") or self._station_id)}
        name = device_meta.get("name") or f"NWPS {self._station_id}"
        info = DeviceInfo(
            identifiers=identifiers,
            name=name,
            manufacturer="NOAA NWPS",
            model="NWPS Station",
            configuration_url="https://api.water.noaa.gov/nwps/v1/docs/",
        )
        return info

    @property
    def available(self) -> bool:
        # Coordinator has data if successful
        return bool(self.coordinator.data)

    @property
    def native_value(self) -> Any:
        # Return the parsed value for this parameter; fall back to raw if not parsed
        data = self.coordinator.data or {}
        # common normalized keys stored by coordinator
        if self._parameter in data:
            return data.get(self._parameter)
        # check unit-suffixed keys (e.g., "stage_unit")
        return data.get(self._parameter)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {
            "station_id": self._station_id,
            "parameter": self._parameter,
            "raw": self.coordinator.data.get("_raw"),
            "attribution": self.coordinator.data.get("_device", {}).get("dataAttribution"),
        }
        device_meta = self.coordinator.data.get("_device") or {}
        if device_meta.get("latitude"):
            attrs["latitude"] = device_meta.get("latitude")
        if device_meta.get("longitude"):
            attrs["longitude"] = device_meta.get("longitude")
        # include unit fields if available
        if self._parameter == "stage" and self.coordinator.data.get("stage_unit"):
            attrs["unit"] = self.coordinator.data.get("stage_unit")
        if self._parameter == "flow" and self.coordinator.data.get("flow_unit"):
            attrs["unit"] = self.coordinator.data.get("flow_unit")
        return attrs