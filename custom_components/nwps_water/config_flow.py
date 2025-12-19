"""Config flow for NWPS Water component."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_NAME

from .const import DOMAIN, CONF_PARAMETERS, DEFAULT_PARAMETERS


class NWPSWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NWPS Water."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the input
            if not user_input.get(CONF_NAME):
                errors[CONF_NAME] = "required"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        # Build the schema
        schema = vol.Schema({
            vol.Required(CONF_NAME): cv.string,
            vol.Optional(CONF_PARAMETERS, default=DEFAULT_PARAMETERS): cv.multi_select({
                param: param for param in DEFAULT_PARAMETERS
            }),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this config entry."""
        return NWPSWaterOptionsFlow(config_entry)


class NWPSWaterOptionsFlow(config_entries.OptionsFlow):
    """Handle options for NWPS Water."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle the initial options step."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        # Get current settings
        current_parameters = self.config_entry.options.get(
            CONF_PARAMETERS, 
            self.config_entry.data.get(CONF_PARAMETERS, DEFAULT_PARAMETERS)
        )

        # Build the schema
        schema = vol.Schema({
            vol.Optional(
                CONF_PARAMETERS, 
                default=current_parameters
            ): cv.multi_select({
                param: param for param in DEFAULT_PARAMETERS
            }),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
