"""NWPS Water integration for Home Assistant."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

# --- MISSING IMPORTS ADDED BELOW ---
from .const import DOMAIN, CONF_STATION
from .coordinator import NWPSDataCoordinator
# -----------------------------------

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "camera"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration (no YAML)."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    # station_id needs CONF_STATION imported from .const
    station_id = entry.data.get(CONF_STATION)
    
    # NWPSDataCoordinator needs to be imported from .coordinator
    coordinator = NWPSDataCoordinator(hass, station_id, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    
    # Forward setups to the platforms (non-blocking)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    
    return True

async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # standard way to apply changes to scan interval or parameters
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
    return unload_ok