# NWPS Water - Home Assistant custom integration

Fetch selected water data from NOAA NWPS (National Water Prediction Service) and expose them in Home Assistant.

Status
- Current version: 0.4.0
- Integration type: Custom component (Integration)
- Default polling interval: 300 seconds (5 minutes)
- Code owner: @ncecowboy

Quick links
- NWPS API docs: https://api.water.noaa.gov/nwps/v1/docs/
- Example station used for development: COCO3 (Clackamas River near Oregon City)
- NOAA logo (optional): https://www.weather.gov/images/logos/NOAA_shield.png

Features
- Sensors for observed stage, observed flow (normalized to cfs where possible), forecast stage/flow.
- Binary sensors for observed and forecast flood conditions when category is minor/moderate/major.
- Images: hydrograph, probabilistic/exceedance maps, station photos exposed in entity attributes.
- Device info and coordinates exposed in attributes (so you can add the station to maps).
- Raw JSON stored in entity attributes for inspection and debugging.

Installation (local development)
1. Copy `custom_components/nwps_water` into Home Assistant's `config/custom_components/`.
2. Restart Home Assistant.
3. Settings → Devices & Services → Add Integration → search for "NWPS Water".
4. Enter `station_id` (e.g., COCO3) and choose parameters and scan interval.

Installation via HACS (custom repository)
1. Push this repository to GitHub.
2. In Home Assistant → HACS → Integrations → ••• → Custom repositories.
3. Add your GitHub repository URL and select category "Integration".
4. Install via HACS and restart Home Assistant.

Configuration options
- station_id (required): NWPS station identifier, e.g., COCO3.
- parameters (optional): list of parameter keys to expose. Defaults are defined in `const.py`.
- scan_interval (optional): polling interval in seconds (default 300).

Entities created (examples)
- sensor.nwps_<station>_stage — observed stage (ft)
- sensor.nwps_<station>_flow — observed flow (cfs)
- sensor.nwps_<station>_forecast_stage — forecast stage (ft)
- sensor.nwps_<station>_forecast_flow — forecast flow (cfs)
- binary_sensor.nwps_<station>_observed_flood — active if observed flood category >= minor
- binary_sensor.nwps_<station>_forecast_flood — active if forecast flood category >= minor

Attributes available
- raw: the raw JSON from the NWPS station endpoint (useful for extending parsers)
- flood_thresholds: flood category thresholds (action/minor/moderate/major)
- hydrograph_image / floodcat_image / probability image URLs
- dataAttribution: original data attribution block (USGS, etc.)
- latitude / longitude (if available)

Versioning & releases
- Use semantic versioning (MAJOR.MINOR.PATCH).
- Bump the `version` in `custom_components/nwps_water/manifest.json` for each release.
- Create a Git tag matching the version (e.g., v0.4.0) and create a GitHub Release summarizing changes:
  git tag -a v0.4.0 -m "v0.4.0: Add config_flow and packaging improvements"
  git push origin v0.4.0
- Add a short changelog entry in the Release notes.

HACS publishing notes
- For personal use, add the repository as a custom repository in HACS (no extra metadata required).
- For public listing in HACS default store, follow HACS contribution guidelines and submit a PR to the HACS/default repository (requires additional metadata and review).
- Consider adding a `hacs.json` file if you want HACS to show additional metadata in the UI.

Testing & debugging
- Enable debug logging for development:
  logger:
    default: info
    logs:
      custom_components.nwps_water: debug
- Use Developer Tools → Services to restart or test updates.
- Inspect entity attributes → raw to see the exact NWPS JSON returned for your station; this helps fine-tune parsing.

CI / Quality suggestions
- Add a GitHub Actions workflow for linting (flake8) and optional unit tests.
- Create a tests/ folder and write unit tests for coordinator parsing using saved sample JSON (e.g., COCO3.json).

Contributing
- Open issues for bugs/features.
- Pull requests should include unit tests where applicable.
- Follow the repository code style and include type hints where convenient.

License
- Add a LICENSE file to indicate the license (e.g., MIT). The integration currently has no license file—add one before publishing if you want permissive reuse.

Changelog (high level)
- 0.1.0 — Initial scaffold
- 0.2.0 — Basic coordinator & sensor prototypes
- 0.3.0 — Heuristic parsing and optional binary sensors
- 0.4.0 — UI config_flow enabled, README and packaging improvements, codeowner added

Support / Contact
- Code owner: @ncecowboy
- For issues and PRs, please use the GitHub repository's Issues tab.
