"""Coordinator that fetches NWPS data and parses station JSON from NWPS."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import NWPS_BASE

_LOGGER = logging.getLogger(__name__)


def _to_float_safe(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _is_valid_reading(value: Optional[float]) -> bool:
    """Check if a reading is valid (not a sentinel/error value).
    
    NWPS API uses -999 to indicate missing or invalid data.
    """
    if value is None:
        return False
    # Common NWPS sentinel values for missing/invalid data
    if value in (-999, -999.0):
        return False
    return True


def _k_prefix_to_multiplier(unit: Optional[str]) -> float:
    """Return multiplier if unit includes a kilo prefix (e.g., 'kcfs' => 1000)."""
    if not unit:
        return 1.0
    unit_lower = unit.lower()
    # common NWPS example used "kcfs" for thousands of cfs
    if "kcfs" in unit_lower or unit_lower.startswith("k"):
        return 1000.0
    return 1.0


class NWPSDataCoordinator(DataUpdateCoordinator):
    """Fetch data from NWPS API and expose parsed results."""

    def __init__(self, hass: HomeAssistant, station_id: str, entry: ConfigEntry):
        """Initialize coordinator."""
        self.hass = hass
        self.station_id = station_id
        
        # Pull parameters and interval directly from the entry options
        from . const import CONF_PARAMETERS, DEFAULT_SCAN_INTERVAL, AVAILABLE_PARAMETERS
        
        self.parameters = entry.options.get(
            CONF_PARAMETERS, 
            list(AVAILABLE_PARAMETERS.keys())
        )
        update_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"nwps_{station_id}",
            update_interval=timedelta(seconds=update_interval),
        )

        self.raw: Dict[str, Any] = {}

    async def _async_update_data(self) -> dict:
        """Fetch and parse NWPS station JSON into a normalized dict."""
        try:
            url = f"{NWPS_BASE}/{self.station_id}"
            _LOGGER.debug("Fetching NWPS station URL: %s", url)
            try:
                async with self.session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise UpdateFailed(f"NWPS station endpoint returned HTTP {resp.status}: {text}")
                    station_json = await resp.json()
            except asyncio.TimeoutError:
                raise UpdateFailed("Timeout while fetching NWPS station data")
            except Exception as exc:
                raise UpdateFailed(f"Error fetching NWPS station data: {exc}") from exc

            self.raw = station_json

            parsed:  Dict[str, Any] = {}

            # Device / station metadata
            device:  Dict[str, Any] = {}
            device["station_id"] = station_json.get("lid") or station_json.get("id")
            device["name"] = station_json.get("name") or station_json.get("description")
            device["latitude"] = station_json.get("latitude")
            device["longitude"] = station_json.get("longitude")
            device["description"] = station_json.get("description")
            device["dataAttribution"] = station_json.get("dataAttribution")

            # Status block contains observed and forecast values (as in sample JSON)
            status = station_json.get("status", {})
            observed = status.get("observed") or {}
            forecast = status.get("forecast") or {}

            # Observed primary/secondary
            obs_primary = _to_float_safe(observed. get("primary"))
            obs_primary_unit = observed.get("primaryUnit")
            obs_secondary = _to_float_safe(observed.get("secondary"))
            obs_secondary_unit = observed.get("secondaryUnit")

            # Forecast primary/secondary
            fcst_primary = _to_float_safe(forecast.get("primary"))
            fcst_primary_unit = forecast.get("primaryUnit")
            fcst_secondary = _to_float_safe(forecast.get("secondary"))
            fcst_secondary_unit = forecast. get("secondaryUnit")

            # Convert secondary (often flow) if unit uses kilo prefix
            obs_secondary_multiplier = _k_prefix_to_multiplier(obs_secondary_unit)
            fcst_secondary_multiplier = _k_prefix_to_multiplier(fcst_secondary_unit)

            # Map to normalized keys - only include valid readings (not sentinel values)
            parsed["stage"] = obs_primary if _is_valid_reading(obs_primary) else None
            parsed["stage_unit"] = obs_primary_unit
            parsed["flow"] = (obs_secondary * obs_secondary_multiplier) if (obs_secondary is not None and _is_valid_reading(obs_secondary)) else None
            parsed["flow_unit"] = "cfs" if (obs_secondary is not None and _is_valid_reading(obs_secondary)) else obs_secondary_unit

            parsed["forecast_stage"] = fcst_primary if _is_valid_reading(fcst_primary) else None
            parsed["forecast_stage_unit"] = fcst_primary_unit
            parsed["forecast_flow"] = (fcst_secondary * fcst_secondary_multiplier) if (fcst_secondary is not None and _is_valid_reading(fcst_secondary)) else None
            parsed["forecast_flow_unit"] = "cfs" if (fcst_secondary is not None and _is_valid_reading(fcst_secondary)) else fcst_secondary_unit

            # Flood categories and thresholds
            parsed["observed_flood_category"] = observed.get("floodCategory") or station_json.get("ObservedFloodCategory")
            parsed["forecast_flood_category"] = forecast.get("floodCategory") or station_json.get("ForecastFloodCategory")
            parsed["flood_thresholds"] = station_json. get("flood", {}).get("categories", {})
            
            # Parse individual flood threshold values
            flood_categories = station_json.get("flood", {}).get("categories", {})
            major = flood_categories.get("major", {})
            moderate = flood_categories.get("moderate", {})
            minor = flood_categories.get("minor", {})
            
            parsed["flood_major_stage"] = _to_float_safe(major.get("stage"))
            parsed["flood_major_flow"] = _to_float_safe(major.get("flow"))
            parsed["flood_moderate_stage"] = _to_float_safe(moderate.get("stage"))
            parsed["flood_moderate_flow"] = _to_float_safe(moderate.get("flow"))
            parsed["flood_minor_stage"] = _to_float_safe(minor.get("stage"))
            parsed["flood_minor_flow"] = _to_float_safe(minor.get("flow"))

            # Images (hydrograph, floodcat, probabilistic, short range)
            images = station_json.get("images", {}) or {}
            hydrograph = images.get("hydrograph", {}) or {}
            parsed["hydrograph_image"] = hydrograph.get("default") or hydrograph.get("floodcat")
            parsed["floodcat_image"] = hydrograph. get("floodcat")
            # probabilistic images
            prob = images.get("probability", {}) or {}
            weekint = prob.get("weekint", {}) or {}
            parsed["probability_stage_week"] = weekint. get("stage")
            parsed["probability_flow_week"] = weekint.get("flow")
            parsed["short_range_probability_image"] = images.get("probability", {}).get("shortrange") or images.get("probability", {}).get("shortrange")

            # Photos - provide first photo url if available
            photos = images.get("photos") or station_json.get("images", {}).get("photos") or []
            if isinstance(photos, list) and photos:
                first = photos[0]
                # In sample photos are GeoJSON-like features with properties.image
                photo_url = None
                caption = None
                if isinstance(first, dict):
                    props = first.get("properties") or {}
                    photo_url = props.get("image") or first.get("image")
                    caption = props.get("caption")
                parsed["photo_url"] = photo_url
                parsed["photo_caption"] = caption

            parsed["_device"] = device
            parsed["_raw"] = station_json

            _LOGGER.debug("Parsed NWPS data keys: %s", list(parsed.keys()))
            _LOGGER.debug("Parsed flow value: %s", parsed.get("flow"))

            return parsed

        except UpdateFailed:
            raise
        except Exception as err: 
            raise UpdateFailed(f"Unexpected error parsing NWPS data: {err}") from err