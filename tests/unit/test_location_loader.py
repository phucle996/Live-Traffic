# ==============================================================================
# Unit Tests for Location Loader & Coordinate Parsing (tests/unit/test_location_loader.py)
# ==============================================================================

from src.ingestion.location_loader import LocationLoader


def test_location_loader_parses_locations_file():
    """
    Verifies that LocationLoader reads data_converted.csv and splits combined 'Latitude,Longitude'.
    """
    locations = LocationLoader.load_locations_list()

    assert len(locations) > 0
    row0 = locations[0]
    assert "Location/Street" in row0
    assert "District" in row0
    assert "Latitude" in row0
    assert "Longitude" in row0

    # Verify first row coordinates are valid doubles
    assert isinstance(row0["Latitude"], float)
    assert isinstance(row0["Longitude"], float)
    assert -90.0 <= row0["Latitude"] <= 90.0
    assert -180.0 <= row0["Longitude"] <= 180.0


if __name__ == "__main__":
    test_location_loader_parses_locations_file()
    print("All test_location_loader unit tests PASSED!")
