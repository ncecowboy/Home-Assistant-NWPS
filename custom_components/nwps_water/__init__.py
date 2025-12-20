"""NWPS Water integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

# Add camera to platforms so HA loads camera platform in addition to sensor and binary_sensor.
PLATFORMS = ["sensor", "binary_sensor", "camera"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration (no YAML)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Schedule platform setup without awaiting so imports aren't run as a blocking call on the event loop.
    # Use async_create_task(...) to schedule the coroutine returned by async_forward_entry_setups.
    hass.async_create_task(hass.config_entries.async_forward_entry_setups(entry, PLATFORMS))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
