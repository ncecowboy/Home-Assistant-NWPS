"""Camera platform for NWPS Water integration."""
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

# Map camera types to their data keys in coordinator
CAMERAS = {
    "hydrograph": {"key": "hydrograph_image", "name": "Hydrograph"},
    "floodcat": {"key": "floodcat_image", "name": "Flood Category"},
    "short_range_probability": {"key": "short_range_probability_image", "name": "Short Range Probability"},
    "station_photo": {"key": "photo_url", "name": "Station Photo"},
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up camera entities for a config entry."""
    # Robustly retrieve station_id from entry.data
    station_id = entry.data.get(CONF_STATION) or entry.data.get("station_id") or entry.data.get("station")
    
    # Get or create coordinator
    coordinator = hass.data.setdefault(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        # Create coordinator if it doesn't exist
        coordinator = NWPSDataCoordinator(hass, station_id, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    else:
        # Ensure data is available
        if not coordinator.data:
            await coordinator.async_config_entry_first_refresh()

    # Only create cameras where URL exists in coordinator data
    entities = []
    for camera_id, info in CAMERAS.items():
        url_key = info["key"]
        url = coordinator.data.get(url_key)
        if url:  # Only create camera if URL is present
            entities.append(
                NWPSCamera(coordinator, entry.entry_id, station_id, camera_id, url_key, info["name"])
            )

    async_add_entities(entities)


class NWPSCamera(CoordinatorEntity, CameraEntity):
    """Representation of a NWPS camera entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NWPSDataCoordinator,
        entry_id: str,
        station_id: str,
        camera_id: str,
        data_key: str,
        camera_name: str,
    ):
        """Initialize the camera."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._camera_id = camera_id
        self._data_key = data_key

        self._attr_name = camera_name
        self._attr_unique_id = f"nwps_{station_id}_camera_{camera_id}"

        # Set device info to group with other entities
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
    def image_url(self) -> str | None:
        """Return the URL of the camera image."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._data_key)

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return camera image bytes."""
        url = self.image_url
        if not url:
            _LOGGER.debug(
                "No image URL available for camera %s (key: %s)",
                self._camera_id,
                self._data_key,
            )
            return None

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    _LOGGER.warning(
                        "Failed to fetch image from %s: HTTP %s", url, response.status
                    )
                    return None
                return await response.read()
        except Exception as err:
            _LOGGER.error("Error fetching camera image from %s: %s", url, err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "station_id": self._station_id,
            "camera_type": self._camera_id,
            "image_url": self.image_url,
        }
