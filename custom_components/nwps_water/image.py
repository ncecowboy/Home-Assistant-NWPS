"""Image entities for NWPS Water integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_STATION
from .coordinator import NWPSDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Image parameter definitions
IMAGE_PARAMETERS = {
    "hydrograph_image": {
        "name": "Hydrograph Image",
    },
    "floodcat_image": {
        "name": "Flood Category Image",
    },
    "short_range_probability_image": {
        "name": "Short Range Probability Image",
    },
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up image entities for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data.get(CONF_STATION)

    entities = [
        NWPSImageEntity(coordinator, station_id, param_key, param_info)
        for param_key, param_info in IMAGE_PARAMETERS.items()
    ]

    async_add_entities(entities)


class NWPSImageEntity(CoordinatorEntity, ImageEntity):
    """Representation of a NWPS image entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NWPSDataCoordinator,
        station_id: str,
        parameter: str,
        parameter_info: dict[str, Any],
    ):
        """Initialize the image entity."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._parameter = parameter
        self._attr_name = parameter_info.get("name", parameter)
        self._attr_unique_id = f"nwps_{station_id}_{parameter}"

        # Set the device info so it groups correctly in the UI
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=f"NWPS {station_id}",
            manufacturer="NOAA NWPS",
            model="NWPS Station",
            configuration_url="https://api.water.noaa.gov/nwps/v1/docs/",
        )

    @property
    def image_url(self) -> str | None:
        """Return the URL of the image."""
        if not self.coordinator.data:
            return None
        url = self.coordinator.data.get(self._parameter)
        return url if url else None

    @property
    def extra_state_attributes(self) -> dict:
        """Return entity specific state attributes."""
        return {
            "station_id": self._station_id,
            "parameter": self._parameter,
            "attribution": "Data provided by NOAA NWPS",
        }
