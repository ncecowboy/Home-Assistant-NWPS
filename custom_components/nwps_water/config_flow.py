"""Config flow for NWPS Water integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN, 
    CONF_STATION, 
    CONF_PARAMETERS, 
    AVAILABLE_PARAMETERS, 
    DEFAULT_SCAN_INTERVAL
)

class NWPSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NWPS Water."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # 1. Check for duplicates
            await self.async_set_unique_id(user_input[CONF_STATION])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"NWPS {user_input[CONF_STATION]}",
                data={CONF_STATION: user_input[CONF_STATION]},
                options={
                    CONF_PARAMETERS: user_input.get(CONF_PARAMETERS, list(AVAILABLE_PARAMETERS.keys())),
                    "scan_interval": user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                },
            )

        # 2. Define schema with parameter selection
        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): str,
                vol.Optional(CONF_PARAMETERS, default=list(AVAILABLE_PARAMETERS.keys())): cv.multi_select(AVAILABLE_PARAMETERS),
                vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user", 
            data_schema=schema, 
            errors=errors
        )