"""Coordinator that fetches NWPS data and parses station JSON from NWPS."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import AVAILABLE_PARAMETERS, CONF_PARAMETERS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, NWPS_BASE

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


def parse_station(station_json: dict[str, Any]) -> dict[str, Any]:
    """Normalize NWPS gauge JSON into a flat dict of parameter values."""
    parsed: dict[str, Any] = {}

    # Device / station metadata
    device: dict[str, Any] = {}
    device["station_id"] = station_json.get("lid") or station_json.get("id")
    device["name"] = station_json.get("name") or station_json.get("description")
    device["latitude"] = station_json.get("latitude")
    device["longitude"] = station_json.get("longitude")
    device["description"] = station_json.get("description")
    device["dataAttribution"] = station_json.get("dataAttribution")

    # Status block contains observed and forecast values (as in sample JSON)
    status = station_json.get("status") or {}
    observed = status.get("observed") or {}
    forecast = status.get("forecast") or {}

    # Observed primary/secondary
    obs_primary = _to_float_safe(observed.get("primary"))
    obs_primary_unit = observed.get("primaryUnit")
    obs_secondary = _to_float_safe(observed.get("secondary"))
    obs_secondary_unit = observed.get("secondaryUnit")

    # Forecast primary/secondary
    fcst_primary = _to_float_safe(forecast.get("primary"))
    fcst_primary_unit = forecast.get("primaryUnit")
    fcst_secondary = _to_float_safe(forecast.get("secondary"))
    fcst_secondary_unit = forecast.get("secondaryUnit")

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
    parsed["flood_thresholds"] = (station_json.get("flood") or {}).get("categories") or {}
    
    # Parse individual flood threshold values
    flood_categories = (station_json.get("flood") or {}).get("categories") or {}
    parsed["flood_minor_stage"] = _to_float_safe((flood_categories.get("minor") or {}).get("stage"))
    parsed["flood_moderate_stage"] = _to_float_safe((flood_categories.get("moderate") or {}).get("stage"))
    parsed["flood_major_stage"] = _to_float_safe((flood_categories.get("major") or {}).get("stage"))
    
    # GPS coordinates and other metadata
    parsed["latitude"] = _to_float_safe(station_json.get("latitude"))
    parsed["longitude"] = _to_float_safe(station_json.get("longitude"))
    parsed["elevation"] = _to_float_safe(station_json.get("elevation"))
    parsed["river_mile"] = _to_float_safe(station_json.get("riverMile"))

    # Images (hydrograph, floodcat, probabilistic, short range)
    images = station_json.get("images", {}) or {}
    hydrograph = images.get("hydrograph", {}) or {}
    parsed["hydrograph_image"] = hydrograph.get("default") or hydrograph.get("floodcat")
    parsed["floodcat_image"] = hydrograph.get("floodcat")
    # probabilistic images
    prob = images.get("probability", {}) or {}
    weekint = prob.get("weekint", {}) or {}
    parsed["probability_stage_week"] = weekint.get("stage")
    parsed["probability_flow_week"] = weekint.get("flow")
    parsed["short_range_probability_image"] = prob.get("shortrange")

    # Photos - provide first photo url if available
    photos = images.get("photos") or []
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
    return parsed


CACHE_RETENTION = timedelta(hours=1)
REQUEST_TIMEOUT = 30


class NWPSDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch data from NWPS API and expose parsed results."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, station_id: str, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.station_id = station_id
        self.parameters: list[str] = entry.options.get(
            CONF_PARAMETERS, list(AVAILABLE_PARAMETERS)
        )
        update_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"nwps_{station_id}",
            update_interval=timedelta(seconds=update_interval),
        )

        self.raw: dict[str, Any] = {}
        self._last_successful_update: Optional[datetime] = None
        self._cached_data: Optional[dict[str, Any]] = None

    def get_device_name(self) -> str:
        """Get the device name for this station."""
        if self.data:
            station_name = self.data.get("_device", {}).get("name")
            if station_name:
                return f"{self.station_id} - {station_name}"
        return self.station_id

    async def _fetch_station(self) -> dict[str, Any]:
        """Fetch raw gauge JSON from the NWPS API."""
        url = f"{NWPS_BASE}/{self.station_id}"
        _LOGGER.debug("Fetching NWPS station URL: %s", url)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self.session.get(url) as resp:
                    if resp.status == 404:
                        raise UpdateFailed(
                            f"Station {self.station_id} not found. "
                            "Please verify the station ID is correct."
                        )
                    if resp.status != 200:
                        text = await resp.text()
                        raise UpdateFailed(
                            f"NWPS API returned HTTP {resp.status}: {text[:200]}"
                        )
                    station_json = await resp.json()
        except TimeoutError as err:
            raise UpdateFailed(
                f"Timeout while fetching NWPS data for station {self.station_id}"
            ) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching NWPS station data: {err}") from err
        if not isinstance(station_json, dict):
            raise UpdateFailed("Unexpected NWPS response format")
        return station_json

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and parse NWPS station JSON into a normalized dict."""
        try:
            station_json = await self._fetch_station()
            self.raw = station_json
            parsed = parse_station(station_json)
        except Exception as err:  # noqa: BLE001
            if self._cached_data is not None and self._last_successful_update is not None:
                age = dt_util.utcnow() - self._last_successful_update
                if age < CACHE_RETENTION:
                    _LOGGER.warning(
                        "NWPS update failed for station %s, using cached data from %s ago: %s",
                        self.station_id, age, err,
                    )
                    return self._cached_data
                _LOGGER.error(
                    "NWPS data unavailable for station %s for more than 1 hour: %s",
                    self.station_id, err,
                )
            if isinstance(err, UpdateFailed):
                raise
            raise UpdateFailed(f"Unexpected error parsing NWPS data: {err}") from err

        self._last_successful_update = dt_util.utcnow()
        self._cached_data = parsed
        return parsed
