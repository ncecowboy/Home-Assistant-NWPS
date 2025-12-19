```markdown
# NWPS Water - Home Assistant custom integration

This integration fetches selected water data from NOAA NWPS (National Water Prediction Service) and exposes them as Home Assistant sensors and binary sensors.

Key features:
- Sensors for water stage, flow/discharge, temperature, velocity, and other parameters.
- Optional binary sensors for flood alerts/warnings derived from NWPS alerts.
- DataUpdateCoordinator with default 5 minute polling (configurable).
- Device info and extra attributes (including raw NWPS JSON for debugging).
- Works with station IDs such as `COCO3`.

NWPS docs
- API documentation: https://api.water.noaa.gov/nwps/v1/docs/
- Example station used in development: COCO3 (replace with your station ID)

Images and logos (links)
- NOAA logo: https://www.weather.gov/images/logos/NOAA_shield.png
- NWPS docs: https://api.water.noaa.gov/nwps/v1/docs/

Installation (local development)
1. Copy the `custom_components/nwps_water` folder into your Home Assistant `config` directory.
2. Restart Home Assistant.
3. Go to Settings → Devices & Services → Add Integration → search for "NWPS Water" and add your station ID and parameters.

Configuration options
- station_id: the NWPS station identifier (string).
- parameters: list of parameter keys to expose. Default includes stage, flow, water_temperature, and others.
- scan_interval: polling interval in seconds (default 300).

Notes about the implementation
- The coordinator will attempt multiple NWPS endpoints and aggregate available data.
- The code uses heuristics to map API fields to the available parameter keys. If your station uses different field names you'll still get raw JSON in attributes for inspecting actual keys.
- To debug parsing, enable debug logging for the integration:
  logger:
    default: info
    logs:
      custom_components.nwps_water: debug

Publishing to HACS
- Push this repository to GitHub.
- In HACS → Integrations → three-dot menu → Custom repositories → add your repo URL and choose "Integration".
- Install and restart Home Assistant.

License
- Choose a license and add LICENSE file as needed.
```