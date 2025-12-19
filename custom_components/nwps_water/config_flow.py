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