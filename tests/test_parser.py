"""Tests for the NWPS station JSON parser."""
from custom_components.nwps_water.coordinator import parse_station

SAMPLE = {
    "lid": "COCO3",
    "name": "Test River",
    "latitude": "44.5",
    "longitude": -123.2,
    "status": {
        "observed": {"primary": 5.2, "primaryUnit": "ft", "secondary": 1.5,
                     "secondaryUnit": "kcfs", "floodCategory": "action"},
        "forecast": {"primary": -999, "primaryUnit": "ft", "secondary": -999,
                     "secondaryUnit": "kcfs", "floodCategory": "no_flooding"},
    },
    "flood": {"categories": {"minor": {"stage": "10"}, "major": {"stage": 20}}},
}


def test_parse_full_station():
    data = parse_station(SAMPLE)
    assert data["stage"] == 5.2
    assert data["flow"] == 1500.0
    assert data["flow_unit"] == "cfs"
    assert data["forecast_stage"] is None
    assert data["forecast_flow"] is None
    assert data["observed_flood_category"] == "action"
    assert data["flood_minor_stage"] == 10.0
    assert data["flood_moderate_stage"] is None
    assert data["flood_major_stage"] == 20.0
    assert data["latitude"] == 44.5
    assert data["_device"]["station_id"] == "COCO3"


def test_parse_empty_and_null_blocks():
    data = parse_station({"status": None, "flood": None, "images": None})
    assert data["stage"] is None
    assert data["flood_minor_stage"] is None
    assert "photo_url" not in data
