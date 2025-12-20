"""Constants for the NWPS Water integration."""

DOMAIN = "nwps_water"
DEFAULT_NAME = "NWPS Water"
DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)
CONF_STATION = "station_id"
CONF_PARAMETERS = "parameters"

# Parameter keys exposed as sensors. Units are typical / normalized to more common units.
AVAILABLE_PARAMETERS = {
    "stage": {"name": "Stage", "unit": "ft"},
    "flow": {"name": "Flow", "unit": "cfs"},
    "forecast_stage": {"name": "Forecast Stage", "unit": "ft"},
    "forecast_flow": {"name": "Forecast Flow", "unit": "cfs"},
    "observed_flood_category": {"name": "Observed Flood Category", "unit": None},
    "forecast_flood_category": {"name": "Forecast Flood Category", "unit": None},
    "flood_major_stage": {"name": "Flood Major Stage", "unit": "ft"},
    "flood_major_flow": {"name": "Flood Major Flow", "unit": "cfs"},
    "flood_moderate_stage": {"name": "Flood Moderate Stage", "unit": "ft"},
    "flood_moderate_flow": {"name": "Flood Moderate Flow", "unit": "cfs"},
    "flood_minor_stage": {"name": "Flood Minor Stage", "unit": "ft"},
    "flood_minor_flow": {"name": "Flood Minor Flow", "unit": "cfs"},
    "hydrograph_image": {"name": "Hydrograph Image", "unit": None},
    "floodcat_image": {"name": "Flood Category Image", "unit": None},
    "short_range_probability_image": {"name": "Short Range Probability Image", "unit": None},
    "probability_stage_week": {"name": "Probability Stage (weekint)", "unit": None},
    "probability_flow_week": {"name": "Probability Flow (weekint)", "unit": None},
    "photo_url": {"name": "Station Photo", "unit": None},
}

# Binary sensor keys
BINARY_SENSORS = {
    "observed_flood": "Observed Flood Active",
    "forecast_flood": "Forecast Flood Expected",
}

# NWPS API base
NWPS_BASE = "https://api.water.noaa.gov/nwps/v1/gauges"