"""Config flow for NWPS Water integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_LOCATION, CONF_PARAMETERS

_LOGGER = logging.getLogger(__name__)

# Default parameters to display
DEFAULT_PARAMETERS = [
    "WaterTemperature",
    "WindSpeed",
    "WindDirection",
    "WindGust",
    "RelativeHumidity",
    "DewPoint",
    "Pressure",
]

# All available parameters
AVAILABLE_PARAMETERS = [
    "WaterTemperature",
    "WindSpeed",
    "WindDirection",
    "WindGust",
    "RelativeHumidity",
    "DewPoint",
    "Pressure",
    "ApparentTemperature",
    "Visibility",
    "CeilingHeight",
]


class NWPSWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NWPS Water."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate that location is provided
                if not user_input.get(CONF_LOCATION):
                    errors["base"] = "invalid_location"
                else:
                    # Set default parameters if not provided
                    if CONF_PARAMETERS not in user_input:
                        user_input[CONF_PARAMETERS] = DEFAULT_PARAMETERS
                    
                    return self.async_create_entry(
                        title=user_input[CONF_LOCATION], data=user_input
                    )
            except Exception as err:
                _LOGGER.error("Error in config flow: %s", err)
                errors["base"] = "unknown"

        # Build the schema with parameter selection
        data_schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION): str,
                vol.Optional(
                    CONF_PARAMETERS,
                    default=DEFAULT_PARAMETERS,
                ): cv.multi_select(AVAILABLE_PARAMETERS),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for NWPS Water."""

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the options flow."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Get current location from config entry data
                location = self.config_entry.data.get(CONF_LOCATION, "")
                
                # Set default parameters if not provided
                if CONF_PARAMETERS not in user_input:
                    user_input[CONF_PARAMETERS] = DEFAULT_PARAMETERS

                return self.async_create_entry(title="", data=user_input)
            except Exception as err:
                _LOGGER.error("Error in options flow: %s", err)
                errors["base"] = "unknown"

        # Get current values from config entry
        current_parameters = self.config_entry.data.get(
            CONF_PARAMETERS, DEFAULT_PARAMETERS
        )

        # Build the schema with parameter selection
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PARAMETERS,
                    default=current_parameters,
                ): cv.multi_select(AVAILABLE_PARAMETERS),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
