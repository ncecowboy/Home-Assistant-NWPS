"""Camera entities for NWPS Water integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.camera import CameraEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_STATION
from .coordinator import NWPSDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Camera mapping: camera_id -> {key in coordinator data, friendly name}
CAMERAS = {
    "hydrograph": {"key": "hydrograph_image", "name": "Hydrograph"},
    "floodcat": {"key": "floodcat_image", "name": "Flood Category Image"},
    "short_range_probability": {"key": "short_range_probability_image", "name": "Short Range Probability"},
    "station_photo": {"key": "photo_url", "name": "Station Photo"},
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up camera entities for a config entry."""
    # Retrieve the coordinator created in __init__.py
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data.get(CONF_STATION)

    entities = [
        NWPSCamera(coordinator, station_id, camera_id, camera_info)
        for camera_id, camera_info in CAMERAS.items()
    ]

    async_add_entities(entities)


class NWPSCamera(CoordinatorEntity, CameraEntity):
    """Representation of a NWPS camera entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NWPSDataCoordinator,
        station_id: str,
        camera_id: str,
        camera_info: dict[str, str],
    ):
        """Initialize the camera."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._camera_id = camera_id
        self._data_key = camera_info["key"]
        self._friendly_name = camera_info["name"]

        self._attr_name = self._friendly_name
        self._attr_unique_id = f"nwps_{station_id}_camera_{camera_id}"

        # Set the device info so it groups correctly in the UI
        device_data = coordinator.data.get("_device", {}) if coordinator.data else {}
        device_name = device_data.get("name") or f"NWPS {station_id}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=device_name,
            manufacturer="NOAA NWPS",
            model="NWPS Station",
            configuration_url="https://api.water.noaa.gov/nwps/v1/docs/",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self.coordinator.data or {}
        image_url = data.get(self._data_key)
        return {
            "image_url": image_url,
            "station_id": self._station_id,
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        data = self.coordinator.data or {}
        image_url = data.get(self._data_key)

        if not image_url:
            _LOGGER.debug(
                "No image URL available for camera %s (key: %s)",
                self._camera_id,
                self._data_key,
            )
            return None

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(image_url, timeout=10) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    _LOGGER.warning(
                        "Failed to fetch image from %s: HTTP %s",
                        image_url,
                        response.status,
                    )
                    return None
        except Exception as err:
            _LOGGER.error("Error fetching camera image from %s: %s", image_url, err)
            return None
