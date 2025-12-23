# National Water Prediction Service - Home Assistant Integration

Fetch water monitoring data from NOAA NWPS (National Water Prediction Service) and expose real-time water stage, flow, and flood information in Home Assistant.

## Features

- **Real-time Water Data**: Stage, flow, and forecast data from NOAA NWPS
- **Configurable Sensors**: Choose which parameters to monitor (Stage, Flow, Forecast Stage/Flow, etc.)
- **Flood Alerts**: Binary sensors for observed and forecast flood conditions
- **Multi-station Support**: Monitor multiple water stations simultaneously
- **Device Info**: Includes station coordinates and metadata for map integration

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots (⋮) → **Custom repositories**
3. Add this URL: `https://github.com/ncecowboy/Home-Assistant-NWPS`
4. Select **Integration** as the category
5. Click **Create**
6. Find "National Water Prediction Service" in HACS and click **Install**
7. Restart Home Assistant
8. Go to **Settings** → **Devices & Services** → **Create Integration**
9. Search for and select **National Water Prediction Service**
10. Enter your NOAA NWPS station ID (e.g., `COCO3`)

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/nwps_water` folder to your Home Assistant `custom_components` directory:
   ```bash
   git clone https://github.com/ncecowboy/Home-Assistant-NWPS.git
   cp -r Home-Assistant-NWPS/custom_components/nwps_water ~/. homeassistant/custom_components/
   ```
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Create Integration**
5. Search for and select **National Water Prediction Service**
6. Enter your NOAA NWPS station ID

## Configuration

After installation, the integration will create sensors based on your selected parameters: 

### Available Sensors

- **Stage** (feet) - Current water stage/level
- **Flow** (cfs) - Current water flow (cubic feet per second)
- **Forecast Stage** (feet) - Predicted water stage
- **Forecast Flow** (cfs) - Predicted water flow
- **Observed Flood Category** - Current flood status (None/Action/Minor/Moderate/Major)
- **Forecast Flood Category** - Predicted flood status
- **Flood Thresholds** - Minor, Moderate, and Major flood stage levels
- **Station Metadata** - Latitude, Longitude, Elevation, River Mile

### Binary Sensors

- **Observed Flood Active** - True if current flood category >= Minor
- **Forecast Flood Expected** - True if predicted flood category >= Minor

## Finding Your Station ID

1. Visit [NOAA NWPS API Documentation](https://api.water.noaa.gov/nwps/v1/docs/)
2. Use the `/gauges` endpoint to browse available stations
3. Look for your location and note the station ID (e.g., `COCO3`, `SACR1`)
4. Example station: `COCO3` (Clackamas River near Oregon City, Oregon)

## Example Automations

### Flood Alert Automation

```yaml
automation:
  - alias: "Flood Warning Alert"
    trigger:
      platform: state
      entity_id:  binary_sensor.nwps_coco3_forecast_flood
      to: "on"
    action:
      - service: notify.notify
        data:
          message: "Flood expected at COCO3 station!"
          title: "NWPS Alert"
```

## Troubleshooting

### Sensors showing "unavailable"

- Check that your station ID is correct
- Verify the station is active on the [NWPS API](https://api.water.noaa.gov/nwps/v1/docs/)
- Check Home Assistant logs for API errors
- **Note**: The integration retains sensor data for up to 1 hour during temporary API unavailability. Sensors will only become unavailable if the API remains inaccessible for more than 1 hour.

### Missing sensor values

- Some stations may not provide all data types
- The integration filters out sentinel values (-999) that indicate missing data
- Check your parameter selection in the integration options

### Update scan interval

By default, the integration polls every 300 seconds (5 minutes). You can adjust this in the integration options. 

## Data Attribution

All data is provided by NOAA (National Oceanic and Atmospheric Administration) through the National Water Prediction Service API. 

Learn more: [NOAA Water Data](https://www.weather.gov/)

## Support

- **Documentation**: [NWPS API Docs](https://api.water.noaa.gov/nwps/v1/docs/)
- **Issues**: [GitHub Issues](https://github.com/ncecowboy/Home-Assistant-NWPS/issues)
- **Repository**: [GitHub](https://github.com/ncecowboy/Home-Assistant-NWPS)

## License

This integration is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Version History

- **1.4.0** - Simplified sensor names to use station ID only; added 1-hour data retention during temporary API unavailability
- **1.0.0** - Initial release with full NWPS integration support