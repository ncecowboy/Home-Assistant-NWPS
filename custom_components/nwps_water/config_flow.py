"""Config flow for NWPS Water integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, CONF_STATION, CONF_PARAMETERS, AVAILABLE_PARAMETERS, DEFAULT_SCAN_INTERVAL

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION): str,
        vol.Optional(CONF_PARAMETERS, default=list(AVAILABLE_PARAMETERS.keys())): list,
        vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class NWPSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NWPS Water."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        # Basic validation could be added here (e.g., call API to validate station exists).
        return self.async_create_entry(
            title=f"NWPS {user_input[CONF_STATION]}",
            data={CONF_STATION: user_input[CONF_STATION]},
            options={
                CONF_PARAMETERS: user_input.get(CONF_PARAMETERS),
                "scan_interval": user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL),
            },
        )