"""Config flow for NWPS Water integration."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, 
    CONF_STATION, 
    CONF_PARAMETERS, 
    AVAILABLE_PARAMETERS, 
    DEFAULT_SCAN_INTERVAL,
    NWPS_BASE
)

_LOGGER = logging.getLogger(__name__)


async def _validate_station_id(hass, station_id: str) -> dict[str, str] | None:
    """Validate the station ID by making a test API call.
    
    Returns None if valid, or a dict with error key if invalid.
    """
    session = async_get_clientsession(hass)
    url = f"{NWPS_BASE}/{station_id}"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 404:
                return {"base": "invalid_station"}
            elif resp.status != 200:
                _LOGGER.error("NWPS API returned status %s for station %s", resp.status, station_id)
                return {"base": "cannot_connect"}
            # Station is valid
            return None
    except (asyncio.TimeoutError, aiohttp.ServerTimeoutError):
        _LOGGER.error("Timeout validating station ID %s", station_id)
        return {"base": "timeout"}
    except aiohttp.ClientError as err:
        _LOGGER.error("Client error validating station ID %s: %s", station_id, err)
        return {"base": "cannot_connect"}
    except Exception as err:
        _LOGGER.exception("Unexpected error validating station ID %s: %s", station_id, err)
        return {"base": "unknown"}


class NWPSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NWPS Water."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Capitalize station ID for consistency
            station_id = user_input[CONF_STATION].upper()
            
            # Validate station ID with NWPS API
            validation_error = await _validate_station_id(self.hass, station_id)
            if validation_error:
                errors.update(validation_error)
            else:
                # Check for duplicates
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"NWPS {station_id}",
                    data={CONF_STATION: station_id},
                    options={
                        CONF_PARAMETERS: user_input.get(CONF_PARAMETERS, list(AVAILABLE_PARAMETERS.keys())),
                        "scan_interval": user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                    },
                )

        # 2. Define schema with parameter selection
        # Create a simple dict mapping parameter keys to their display names
        parameter_options = {
            param_key: param_info.get("name", param_key)
            for param_key, param_info in AVAILABLE_PARAMETERS.items()
        }
        
        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): str,
                vol.Optional(CONF_PARAMETERS, default=list(AVAILABLE_PARAMETERS.keys())): cv.multi_select(parameter_options),
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user", 
            data_schema=schema, 
            errors=errors
        )