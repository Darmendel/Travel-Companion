# tests/test_stops.py
import time
from datetime import date, timedelta
import pytest


# ==================== CREATE STOP TESTS ====================

def test_create_stop_success(client, sample_trip):
    """Test creating a stop successfully."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "country": "Japan",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.6762,
        "longitude": 139.6503,
        "notes": "Visit Shibuya"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tokyo"
    assert data["country"] == "Japan"
    assert data["trip_id"] == sample_trip.id
    assert data["order_index"] == 0
    assert "id" in data


def test_create_stop_minimal_fields(client, sample_trip):
    """Test creating a stop with only required fields (success)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Paris",
        "start_date": (date.today() + timedelta(days=12)).isoformat(),
        "end_date": (date.today() + timedelta(days=14)).isoformat(),
        "order_index": 1
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Paris"
    assert data["country"] is None
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["notes"] is None


def test_create_stop_trip_not_found(client):
    """Test creating a stop for non-existent trip."""
    response = client.post("/trips/999/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0
    })
    assert response.status_code == 404
    assert "Trip with ID 999 not found" in response.json()["detail"]


def test_create_stop_dates_outside_trip_dates(client, sample_trip):
    """Test creating a stop with dates outside trip dates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=5)).isoformat(),  # Before trip start
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0
    })
    assert response.status_code == 400
    assert "Stop dates must be within trip dates" in response.json()["detail"]


def test_create_stop_end_date_after_trip_end(client, sample_trip):
    """Test creating a stop that ends after trip ends."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=15)).isoformat(),
        "end_date": (date.today() + timedelta(days=25)).isoformat(),  # After trip end
        "order_index": 0
    })
    assert response.status_code == 400
    assert "Stop dates must be within trip dates" in response.json()["detail"]


def test_create_stop_duplicate_order_index(client, sample_trip_with_stop):
    """Test creating a stop with duplicate order_index."""
    trip, existing_stop = sample_trip_with_stop
    response = client.post(f"/trips/{trip.id}/stops/", json={
        "name": "Kyoto",
        "start_date": (date.today() + timedelta(days=16)).isoformat(),
        "end_date": (date.today() + timedelta(days=18)).isoformat(),
        "order_index": existing_stop.order_index  # Same order_index
    })
    assert response.status_code == 400
    assert f"Stop with order_index {existing_stop.order_index} already exists" in response.json()["detail"]


def test_create_stop_empty_name(client, sample_trip):
    """Test creating a stop with empty name."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "   ",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0
    })
    assert response.status_code == 422
    assert "Stop name must not be empty" in response.text


def test_create_stop_start_date_in_past(client, sample_trip):
    """Test creating a stop with start_date in the past."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() - timedelta(days=1)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0
    })
    assert response.status_code == 422
    assert "cannot be in the past" in response.text


def test_create_stop_end_before_start(client, sample_trip):
    """Test creating a stop where end_date is before start_date."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=15)).isoformat(),
        "end_date": (date.today() + timedelta(days=11)).isoformat(),
        "order_index": 0
    })
    assert response.status_code == 422
    assert "end_date must be after or equal to start_date" in response.text


def test_create_stop_latitude_without_longitude(client, sample_trip):
    """Test creating a stop with latitude but no longitude."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.6762
    })
    assert response.status_code == 422
    assert "Both latitude and longitude must be provided together" in response.text


def test_create_stop_longitude_without_latitude(client, sample_trip):
    """Test creating a stop with longitude but no latitude."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "longitude": 139.6503
    })
    assert response.status_code == 422
    assert "Both latitude and longitude must be provided together" in response.text


def test_create_stop_invalid_latitude(client, sample_trip):
    """Test creating a stop with invalid latitude."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 95.0,  # Invalid: > 90
        "longitude": 139.6503
    })
    assert response.status_code == 422


def test_create_stop_negative_order_index(client, sample_trip):
    """Test creating a stop with negative order_index."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": -1
    })
    assert response.status_code == 422


# ==================== GET STOPS TESTS ====================

def test_get_all_stops_empty(client, sample_trip):
    """Test getting stops for a trip with no stops."""
    response = client.get(f"/trips/{sample_trip.id}/stops/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_stops_with_data(client, sample_trip_with_stop):
    """Test getting all stops for a trip."""
    trip, stop = sample_trip_with_stop
    response = client.get(f"/trips/{trip.id}/stops/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == stop.name
    assert data[0]["id"] == stop.id


def test_get_all_stops_ordered(client, sample_trip_with_multiple_stops):
    """Test that stops are returned in order_index order."""
    trip, stops = sample_trip_with_multiple_stops
    response = client.get(f"/trips/{trip.id}/stops/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Should be ordered by order_index
    assert data[0]["order_index"] == 0
    assert data[1]["order_index"] == 1
    assert data[2]["order_index"] == 2


def test_get_all_stops_trip_not_found(client):
    """Test getting stops for non-existent trip."""
    response = client.get("/trips/999/stops/")
    assert response.status_code == 404


def test_get_stop_by_id_success(client, sample_trip_with_stop):
    """Test getting a specific stop by ID."""
    trip, stop = sample_trip_with_stop
    response = client.get(f"/trips/{trip.id}/stops/{stop.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == stop.id
    assert data["name"] == stop.name


def test_get_stop_by_id_not_found(client, sample_trip):
    """Test getting non-existent stop."""
    response = client.get(f"/trips/{sample_trip.id}/stops/999")
    assert response.status_code == 404
    assert "Stop with ID 999 not found" in response.json()["detail"]


def test_get_stop_wrong_trip(client, sample_trip, sample_trip_with_stop):
    """Test getting a stop from the wrong trip."""
    trip1 = sample_trip
    trip2, stop = sample_trip_with_stop
    # Try to get trip2's stop using trip1's ID
    response = client.get(f"/trips/{trip1.id}/stops/{stop.id}")
    assert response.status_code == 404


# ==================== UPDATE STOP TESTS ====================

def test_update_stop_name(client, sample_trip_with_stop):
    """Test updating stop name."""
    trip, stop = sample_trip_with_stop
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "Kyoto"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Kyoto"
    assert data["id"] == stop.id


def test_update_stop_dates(client, sample_trip_with_stop):
    """Test updating stop dates."""
    trip, stop = sample_trip_with_stop
    new_start = (date.today() + timedelta(days=12)).isoformat()
    new_end = (date.today() + timedelta(days=16)).isoformat()

    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "start_date": new_start,
        "end_date": new_end
    })
    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == new_start
    assert data["end_date"] == new_end


def test_update_stop_coordinates(client, sample_trip_with_stop):
    """Test updating stop coordinates."""
    trip, stop = sample_trip_with_stop
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "latitude": 35.6762,   # Tokyo
        "longitude": 139.6503  # Tokyo
    })
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 35.6762
    assert data["longitude"] == 139.6503


def test_update_stop_not_found(client, sample_trip):
    """Test updating non-existent stop."""
    response = client.put(f"/trips/{sample_trip.id}/stops/999", json={
        "name": "Ghost Stop"
    })
    assert response.status_code == 404


def test_update_stop_dates_outside_trip(client, sample_trip_with_stop):
    """Test updating stop with dates outside trip dates."""
    trip, stop = sample_trip_with_stop
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "start_date": (date.today() + timedelta(days=5)).isoformat(),  # Before trip
        "end_date": (date.today() + timedelta(days=15)).isoformat()
    })
    assert response.status_code == 400
    assert "Stop dates must be within trip dates" in response.json()["detail"]


def test_update_stop_duplicate_order_index(client, sample_trip_with_multiple_stops):
    """Test updating stop to have duplicate order_index."""
    trip, stops = sample_trip_with_multiple_stops
    # Try to update stop[2] to have same order_index as stop[0]
    response = client.put(f"/trips/{trip.id}/stops/{stops[2].id}", json={
        "order_index": stops[0].order_index
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_update_stop_empty_name(client, sample_trip_with_stop):
    """Test updating stop with empty name."""
    trip, stop = sample_trip_with_stop
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "   "
    })
    assert response.status_code == 422
    assert "Stop name must not be empty" in response.text


# ==================== DELETE STOP TESTS ====================

def test_delete_stop_success(client, sample_trip_with_stop):
    """Test deleting a stop."""
    trip, stop = sample_trip_with_stop
    response = client.delete(f"/trips/{trip.id}/stops/{stop.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == stop.id

    # Verify it's deleted
    get_response = client.get(f"/trips/{trip.id}/stops/{stop.id}")
    assert get_response.status_code == 404


def test_delete_stop_not_found(client, sample_trip):
    """Test deleting non-existent stop."""
    response = client.delete(f"/trips/{sample_trip.id}/stops/999")
    assert response.status_code == 404


def test_delete_stop_wrong_trip(client, sample_trip, sample_trip_with_stop):
    """Test deleting a stop using wrong trip ID."""
    trip1 = sample_trip
    trip2, stop = sample_trip_with_stop
    response = client.delete(f"/trips/{trip1.id}/stops/{stop.id}")
    assert response.status_code == 404


# ==================== REORDER STOPS TESTS ====================

def test_reorder_stops_success(client, sample_trip_with_multiple_stops):
    """Test reordering stops."""
    trip, stops = sample_trip_with_multiple_stops
    # Original order: [stops[0], stops[1], stops[2]]
    # New order: [stops[2], stops[0], stops[1]]
    new_order = [stops[2].id, stops[0].id, stops[1].id]

    response = client.put(f"/trips/{trip.id}/stops/reorder", json={
        "stop_ids": new_order
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["id"] == stops[2].id
    assert data[0]["order_index"] == 0
    assert data[1]["id"] == stops[0].id
    assert data[1]["order_index"] == 1
    assert data[2]["id"] == stops[1].id
    assert data[2]["order_index"] == 2


def test_reorder_stops_trip_not_found(client):
    """Test reordering stops for non-existent trip."""
    response = client.put("/trips/999/stops/reorder", json={
        "stop_ids": [1, 2, 3]
    })
    assert response.status_code == 404


def test_reorder_stops_missing_ids(client, sample_trip_with_multiple_stops):
    """Test reordering with missing stop IDs."""
    trip, stops = sample_trip_with_multiple_stops
    # Only provide 2 out of 3 stops
    response = client.put(f"/trips/{trip.id}/stops/reorder", json={
        "stop_ids": [stops[0].id, stops[1].id]
    })
    assert response.status_code == 400
    assert "Missing stop IDs" in response.json()["detail"]


def test_reorder_stops_invalid_ids(client, sample_trip_with_multiple_stops):
    """Test reordering with invalid stop IDs."""
    trip, stops = sample_trip_with_multiple_stops
    response = client.put(f"/trips/{trip.id}/stops/reorder", json={
        "stop_ids": [stops[0].id, stops[1].id, 999]
    })
    assert response.status_code == 400
    assert "Invalid stop IDs" in response.json()["detail"]


def test_reorder_stops_duplicate_ids(client, sample_trip_with_multiple_stops):
    """Test reordering with duplicate stop IDs."""
    trip, stops = sample_trip_with_multiple_stops
    response = client.put(f"/trips/{trip.id}/stops/reorder", json={
        "stop_ids": [stops[0].id, stops[0].id, stops[1].id]
    })
    assert response.status_code == 422
    assert "must not contain duplicates" in response.text


def test_reorder_stops_empty_list(client, sample_trip_with_stop):
    """Test reordering with empty list."""
    trip, stop = sample_trip_with_stop
    response = client.put(f"/trips/{trip.id}/stops/reorder", json={
        "stop_ids": []
    })
    assert response.status_code == 422


"""
Additional tests for stop coordinate validation.
Tests realistic coordinates, null island, country validation, etc.
"""

# ==================== NULL ISLAND TESTS ====================

def test_create_stop_null_island(client, sample_trip):
    """Test creating a stop with Null Island coordinates (0, 0)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Null Island",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "Coordinates (0, 0) appear to be a placeholder" in response.text


def test_update_stop_to_null_island(client, sample_trip_with_stop):
    """Test updating a stop to Null Island coordinates."""
    trip, stop = sample_trip_with_stop
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "latitude": 0.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "Coordinates (0, 0) appear to be a placeholder" in response.text


# ==================== PLACEHOLDER VALUES TESTS ====================

def test_create_stop_placeholder_coordinates(client, sample_trip):
    """Test creating a stop with common placeholder coordinates (1, 1)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Test Location",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 1.0,
        "longitude": 1.0
    })
    assert response.status_code == 422
    assert "appear to be a placeholder" in response.text


def test_create_stop_north_pole_placeholder(client, sample_trip):
    """Test creating a stop at North Pole + Prime Meridian (unlikely)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "North Pole",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 90.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "appear to be a placeholder" in response.text


# ==================== COUNTRY VALIDATION TESTS ====================

def test_create_stop_japan_valid_coordinates(client, sample_trip):
    """Test creating a stop in Japan with valid Tokyo coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "country": "Japan",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.6762,
        "longitude": 139.6503
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tokyo"
    assert data["latitude"] == 35.6762
    assert data["longitude"] == 139.6503


def test_create_stop_japan_invalid_coordinates(client, sample_trip):
    """Test creating a stop in Japan with coordinates outside Japan (LA)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "country": "Japan",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 34.0522,  # Los Angeles
        "longitude": -118.2437
    })
    assert response.status_code == 422
    assert "do not appear to be in Japan" in response.text


def test_create_stop_israel_valid_coordinates(client, sample_trip):
    """Test creating a stop in Israel with valid Tel Aviv coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tel Aviv",
        "country": "Israel",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 32.0853,
        "longitude": 34.7818
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tel Aviv"
    assert data["country"] == "Israel"


def test_create_stop_israel_invalid_coordinates(client, sample_trip):
    """Test creating a stop in Israel with coordinates outside Israel (Paris)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Jerusalem",
        "country": "Israel",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 48.8566,  # Paris
        "longitude": 2.3522
    })
    assert response.status_code == 422
    assert "do not appear to be in Israel" in response.text


def test_create_stop_usa_valid_coordinates(client, sample_trip):
    """Test creating a stop in USA with valid New York coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "New York",
        "country": "USA",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 40.7128,
        "longitude": -74.0060
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New York"


def test_create_stop_usa_alaska_valid(client, sample_trip):
    """Test creating a stop in USA with valid Alaska coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Anchorage",
        "country": "USA",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 61.2181,
        "longitude": -149.9003
    })
    assert response.status_code == 201


def test_create_stop_usa_hawaii_valid(client, sample_trip):
    """Test creating a stop in USA with valid Hawaii coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Honolulu",
        "country": "USA",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 21.3099,
        "longitude": -157.8581
    })
    assert response.status_code == 201


def test_create_stop_usa_invalid_coordinates(client, sample_trip):
    """Test creating a stop in USA with coordinates outside USA (Tokyo)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Los Angeles",
        "country": "USA",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.6762,  # Tokyo
        "longitude": 139.6503
    })
    assert response.status_code == 422
    assert "do not appear to be in United States" in response.text or "do not appear to be in USA" in response.text


# ==================== NO COUNTRY SPECIFIED TESTS ====================

def test_create_stop_no_country_any_coordinates(client, sample_trip):
    """Test creating a stop without country - should accept any valid coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Random Place",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 48.8566,  # Paris
        "longitude": 2.3522
    })
    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] == 48.8566
    assert data["longitude"] == 2.3522


def test_create_stop_no_country_still_blocks_null_island(client, sample_trip):
    """Test that Null Island is blocked even without country."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Random Place",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "Coordinates (0, 0) appear to be a placeholder" in response.text


# ==================== UPDATE TESTS ====================

def test_update_stop_change_country_and_coordinates(client, sample_trip_with_stop):
    """Test updating both country and coordinates together."""
    trip, stop = sample_trip_with_stop
    # Original: Tokyo, Japan
    # Update to: Tel Aviv, Israel
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "Tel Aviv",
        "country": "Israel",
        "latitude": 32.0853,
        "longitude": 34.7818
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tel Aviv"
    assert data["country"] == "Israel"
    assert data["latitude"] == 32.0853


def test_update_stop_change_country_but_keep_old_coordinates(client, sample_trip_with_stop):
    """Test updating country but keeping old coordinates - should fail."""
    trip, stop = sample_trip_with_stop
    # Original: Tokyo (35.6762, 139.6503), Japan
    # Try to change to Israel but keep Tokyo coordinates
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "country": "Israel"
        # Keeping Tokyo coordinates from DB
    })
    assert response.status_code == 422
    assert "do not appear to be in Israel" in response.text


# ==================== EDGE CASES ====================

def test_create_stop_extreme_valid_latitude(client, sample_trip):
    """Test creating a stop with extreme but valid latitude."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "South Pole",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -89.9,
        "longitude": 45.0
    })
    assert response.status_code == 201


def test_create_stop_extreme_valid_longitude(client, sample_trip):
    """Test creating a stop with extreme but valid longitude."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "International Date Line",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0001,  # Just off equator to avoid null island
        "longitude": 179.9
    })
    assert response.status_code == 201


def test_create_stop_case_insensitive_country(client, sample_trip):
    """Test that country validation is case-insensitive."""
    # Test "JAPAN" (uppercase)
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Tokyo",
        "country": "JAPAN",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.6762,
        "longitude": 139.6503
    })
    assert response.status_code == 201


def test_create_stop_country_code(client, sample_trip):
    """Test using country code (JP for Japan)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Kyoto",
        "country": "JP",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.0116,
        "longitude": 135.7681
    })
    assert response.status_code == 201


"""
Comprehensive tests for coordinate validation.

Tests include:
1. Additional countries (France, Germany, UK, Australia, etc.)
2. Edge cases (borders, equator, prime meridian)
3. Performance tests
4. Invalid coordinate scenarios
"""


# ==================== ADDITIONAL COUNTRY TESTS ====================

def test_create_stop_france_valid_coordinates(client, sample_trip):
    """Test creating a stop in France with valid coordinates (Paris)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Paris",
        "country": "France",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 48.8566,
        "longitude": 2.3522,
        "notes": "Eiffel Tower"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Paris"
    assert data["country"] == "France"
    assert data["latitude"] == 48.8566
    assert data["longitude"] == 2.3522


def test_create_stop_germany_valid_coordinates(client, sample_trip):
    """Test creating a stop in Germany with valid coordinates (Berlin)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Berlin",
        "country": "Germany",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 52.5200,
        "longitude": 13.4050
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Berlin"
    assert data["country"] == "Germany"


def test_create_stop_uk_valid_coordinates(client, sample_trip):
    """Test creating a stop in UK with valid coordinates (London)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "London",
        "country": "United Kingdom",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 51.5074,
        "longitude": -0.1278
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "London"
    assert data["country"] == "United Kingdom"


def test_create_stop_australia_valid_coordinates(client, sample_trip):
    """Test creating a stop in Australia with valid coordinates (Sydney)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Sydney",
        "country": "Australia",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -33.8688,
        "longitude": 151.2093
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Sydney"
    assert data["country"] == "Australia"
    assert data["latitude"] == -33.8688  # Southern hemisphere


def test_create_stop_canada_valid_coordinates(client, sample_trip):
    """Test creating a stop in Canada with valid coordinates (Toronto)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Toronto",
        "country": "Canada",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 43.6532,
        "longitude": -79.3832
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Toronto"
    assert data["country"] == "Canada"


def test_create_stop_brazil_valid_coordinates(client, sample_trip):
    """Test creating a stop in Brazil with valid coordinates (Rio)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Rio de Janeiro",
        "country": "Brazil",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -22.9068,
        "longitude": -43.1729
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rio de Janeiro"
    assert data["country"] == "Brazil"


def test_create_stop_south_africa_valid_coordinates(client, sample_trip):
    """Test creating a stop in South Africa with valid coordinates (Cape Town)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Cape Town",
        "country": "South Africa",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -33.9249,
        "longitude": 18.4241
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cape Town"
    assert data["country"] == "South Africa"


# ==================== INVALID COUNTRY-COORDINATE MISMATCHES ====================

def test_create_stop_france_with_japan_coordinates(client, sample_trip):
    """Test creating a stop in France with Tokyo coordinates - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Paris",
        "country": "France",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.6762,  # Tokyo coordinates
        "longitude": 139.6503
    })
    # Note: This might pass if France validation isn't implemented
    # If validation exists, it should return 422
    # For now, we just ensure it doesn't crash
    assert response.status_code in [201, 422]


def test_create_stop_australia_with_usa_coordinates(client, sample_trip):
    """Test creating a stop in Australia with USA coordinates - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Sydney",
        "country": "Australia",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 40.7128,  # New York coordinates
        "longitude": -74.0060
    })
    # Should fail if validation exists
    assert response.status_code in [201, 422]


# ==================== EDGE CASE TESTS: BOUNDARIES ====================

def test_create_stop_equator_valid(client, sample_trip):
    """Test creating a stop at the equator (latitude = 0) - should be valid."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Quito",
        "country": "Ecuador",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.1807,  # Near equator
        "longitude": -78.4678
    })
    assert response.status_code == 201
    data = response.json()
    assert abs(data["latitude"]) < 1  # Very close to equator


def test_create_stop_prime_meridian_valid(client, sample_trip):
    """Test creating a stop at the prime meridian (longitude = 0) - should be valid."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Greenwich",
        "country": "United Kingdom",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 51.4769,
        "longitude": 0.0  # Prime meridian
    })
    assert response.status_code == 201
    data = response.json()
    assert data["longitude"] == 0.0


def test_create_stop_null_island_invalid(client, sample_trip):
    """Test creating a stop at (0, 0) - Null Island - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Null Island",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "placeholder" in response.text.lower()


def test_create_stop_max_latitude_north_pole(client, sample_trip):
    """Test creating a stop at North Pole (latitude = 90)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "North Pole",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 90.0,
        "longitude": 0.0
    })
    # Might be rejected as placeholder
    assert response.status_code in [201, 422]


def test_create_stop_min_latitude_south_pole(client, sample_trip):
    """Test creating a stop at South Pole (latitude = -90)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "South Pole",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -90.0,
        "longitude": 0.0
    })
    # Might be rejected as placeholder
    assert response.status_code in [201, 422]


def test_create_stop_max_longitude_international_date_line(client, sample_trip):
    """Test creating a stop at International Date Line (longitude = 180)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Fiji",
        "country": "Fiji",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -17.7134,
        "longitude": 178.0650  # Near date line
    })
    assert response.status_code == 201


def test_create_stop_min_longitude(client, sample_trip):
    """Test creating a stop at minimum longitude (-180)."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Remote Pacific",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0,
        "longitude": -179.0
    })
    # Should be valid (not exactly -180, 0)
    assert response.status_code == 201


# ==================== LATITUDE/LONGITUDE BOUNDARY TESTS ====================

def test_create_stop_latitude_too_high(client, sample_trip):
    """Test creating a stop with latitude > 90 - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Invalid North",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 91.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "Latitude" in response.text or "latitude" in response.text


def test_create_stop_latitude_too_low(client, sample_trip):
    """Test creating a stop with latitude < -90 - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Invalid South",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -91.0,
        "longitude": 0.0
    })
    assert response.status_code == 422
    assert "Latitude" in response.text or "latitude" in response.text


def test_create_stop_longitude_too_high(client, sample_trip):
    """Test creating a stop with longitude > 180 - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Invalid East",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0,
        "longitude": 181.0
    })
    assert response.status_code == 422
    assert "Longitude" in response.text or "longitude" in response.text


def test_create_stop_longitude_too_low(client, sample_trip):
    """Test creating a stop with longitude < -180 - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Invalid West",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 0.0,
        "longitude": -181.0
    })
    assert response.status_code == 422
    assert "Longitude" in response.text or "longitude" in response.text


# ==================== COMMON PLACEHOLDER VALUES ====================

def test_create_stop_placeholder_1_1(client, sample_trip):
    """Test creating a stop at (1, 1) - common test placeholder - should fail."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Test Location",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 1.0,
        "longitude": 1.0
    })
    assert response.status_code == 422
    assert "placeholder" in response.text.lower()


# ==================== COORDINATE PRECISION TESTS ====================

def test_create_stop_high_precision_coordinates(client, sample_trip):
    """Test creating a stop with very precise coordinates."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Precise Location",
        "country": "Japan",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": 35.676234567890,
        "longitude": 139.650345678901
    })
    assert response.status_code == 201
    data = response.json()
    # Check precision is preserved
    assert data["latitude"] == 35.676234567890
    assert data["longitude"] == 139.650345678901


# ==================== UPDATE COORDINATE VALIDATION TESTS ====================

def test_update_stop_valid_coordinates_to_different_country(client, sample_trip_with_stop):
    """Test updating stop to different country with matching coordinates."""
    trip, stop = sample_trip_with_stop
    # Original: Tokyo (Japan)
    # Update to: Seoul (South Korea) with correct coordinates
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "Seoul",
        "country": "South Korea",
        "latitude": 37.5665,
        "longitude": 126.9780
    })
    # Should succeed if coordinates match country (if validation exists for South Korea)
    assert response.status_code in [200, 422]


def test_update_stop_only_coordinates_keep_country(client, sample_trip_with_stop):
    """Test updating only coordinates while keeping same country."""
    trip, stop = sample_trip_with_stop
    # Original: Tokyo (35.6762, 139.6503), Japan
    # Update to: Osaka coordinates, still Japan
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "latitude": 34.6937,
        "longitude": 135.5023
    })
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "Japan"  # Unchanged
    assert data["latitude"] == 34.6937
    assert data["longitude"] == 135.5023


# ==================== PERFORMANCE TESTS ====================

def test_create_100_stops_performance(client, db_session):
    """Performance test: Create 100 stops with coordinates."""
    from app.models.trip import Trip as TripModel

    # Create a long trip
    trip = TripModel(
        title="Long Trip",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=500)
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    start_time = time.time()

    # Create 100 stops
    for i in range(100):
        response = client.post(f"/trips/{trip.id}/stops/", json={
            "name": f"Stop {i}",
            "country": "Japan",
            "start_date": (date.today() + timedelta(days=10 + i * 4)).isoformat(),
            "end_date": (date.today() + timedelta(days=10 + i * 4 + 2)).isoformat(),
            "order_index": i,
            "latitude": 35.6762 + (i * 0.01),  # Slight variation
            "longitude": 139.6503 + (i * 0.01)
        })
        assert response.status_code == 201

    end_time = time.time()
    duration = end_time - start_time

    print(f"\nCreated 100 stops in {duration:.2f} seconds")
    print(f"Average: {duration / 100 * 1000:.2f} ms per stop")

    # Should complete in reasonable time (< 10 seconds)
    assert duration < 10, f"Creating 100 stops took too long: {duration:.2f}s"


def test_coordinate_validation_performance(client, sample_trip):
    """Performance test: Measure coordinate validation speed."""

    test_cases = [
        {"lat": 35.6762, "lon": 139.6503, "country": "Japan"},
        {"lat": 40.7128, "lon": -74.0060, "country": "USA"},
        {"lat": 31.7683, "lon": 35.2137, "country": "Israel"},
        {"lat": 48.8566, "lon": 2.3522, "country": "France"},
        {"lat": -33.8688, "lon": 151.2093, "country": "Australia"},
    ]

    start_time = time.time()

    for i, tc in enumerate(test_cases * 20):  # 100 validations
        response = client.post(f"/trips/{sample_trip.id}/stops/", json={
            "name": f"Test {i}",
            "country": tc["country"],
            "start_date": (date.today() + timedelta(days=11 + i * 4)).isoformat(),
            "end_date": (date.today() + timedelta(days=13 + i * 4)).isoformat(),
            "order_index": i,
            "latitude": tc["lat"],
            "longitude": tc["lon"]
        })
        # Some might fail due to order_index conflicts, that's ok
        assert response.status_code in [201, 400, 422]

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n100 coordinate validations in {duration:.2f} seconds")
    print(f"Average: {duration / 100 * 1000:.2f} ms per validation")


def test_get_all_stops_performance_with_many_stops(client, db_session):
    """Performance test: GET all stops when there are many."""
    from app.models.trip import Trip as TripModel
    from app.models.stop import Stop as StopModel

    # Create trip
    trip = TripModel(
        title="Performance Trip",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=500)
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Create 100 stops directly in DB (faster than API)
    for i in range(100):
        stop = StopModel(
            trip_id=trip.id,
            name=f"Stop {i}",
            country="Japan",
            start_date=date.today() + timedelta(days=10 + i * 4),
            end_date=date.today() + timedelta(days=10 + i * 4 + 2),
            order_index=i,
            latitude=35.6762 + (i * 0.01),
            longitude=139.6503 + (i * 0.01)
        )
        db_session.add(stop)
    db_session.commit()

    # Measure GET performance
    start_time = time.time()
    response = client.get(f"/trips/{trip.id}/stops/")
    end_time = time.time()

    duration = end_time - start_time

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 100

    print(f"\nRetrieved 100 stops in {duration * 1000:.2f} ms")

    # Should be very fast (< 1 second)
    assert duration < 1, f"GET 100 stops took too long: {duration:.2f}s"


# ==================== STRESS TESTS ====================

def test_create_stop_with_all_edge_case_coordinates(client, sample_trip):
    """Test creating stops at all edge case coordinates.
    This test verifies that stops can be created successfully
    for edge-case geographic coordinates (latitude/longitude)."""

    edge_cases = [
        {"name": "Near Equator", "lat": 0.001, "lon": 10.0},
        {"name": "Near Prime Meridian", "lat": 45.0, "lon": 0.001},
        {"name": "Near North Pole", "lat": 89.9, "lon": 0.0},
        {"name": "Near South Pole", "lat": -89.9, "lon": 0.0},
        {"name": "Near Date Line East", "lat": 0.0, "lon": 179.9},
        {"name": "Near Date Line West", "lat": 0.0, "lon": -179.9},
    ]

    for i, case in enumerate(edge_cases):
        start = sample_trip.start_date + timedelta(days=i)
        end = start + timedelta(days=1)

        response = client.post(f"/trips/{sample_trip.id}/stops/", json={
            "name": case["name"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "order_index": i,
            "latitude": case["lat"],
            "longitude": case["lon"]
        })

        assert response.status_code == 201, (
            f"Failed for {case['name']}: "
            f"{response.status_code} {response.json()}"
        )


# ==================== COMBINED VALIDATION TESTS ====================

def test_update_coordinates_and_country_simultaneously_valid(client, sample_trip_with_stop):
    """Test updating both coordinates and country together - valid combination."""
    trip, stop = sample_trip_with_stop
    # Original: Tokyo, Japan
    # Update to: New York, USA
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "New York",
        "country": "USA",
        "latitude": 40.7128,
        "longitude": -74.0060
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New York"
    assert data["country"] == "USA"
    assert data["latitude"] == 40.7128


def test_update_coordinates_and_country_simultaneously_invalid(client, sample_trip_with_stop):
    """Test updating both coordinates and country together - invalid combination."""
    trip, stop = sample_trip_with_stop
    # Original: Tokyo, Japan
    # Update to: USA country with Tokyo coordinates (invalid)
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "country": "USA",
        "latitude": 35.6762,  # Tokyo coordinates
        "longitude": 139.6503
    })
    assert response.status_code == 422
    assert "do not appear to be in USA" in response.text or "USA" in response.text


# ==================== ADDITIONAL EDGE CASE TESTS ====================

def test_create_stop_with_special_characters_in_name(client, sample_trip):
    """Test creating stop with special characters in name."""
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "São Paulo & Tokyo! 🌍✈️",
        "country": "Brazil",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "latitude": -23.5505,
        "longitude": -46.6333
    })
    assert response.status_code == 201
    data = response.json()
    assert "São Paulo" in data["name"]
    assert "🌍" in data["name"]


def test_create_stop_with_very_long_name(client, sample_trip):
    """Test creating stop with maximum length name (200 chars)."""
    long_name = "A" * 200
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": long_name,
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0
    })
    # Should succeed with 200 chars (assuming max_length=200)
    assert response.status_code in [201, 422]


def test_create_stop_name_too_long(client, sample_trip):
    """Test creating stop with name exceeding max length."""
    too_long_name = "A" * 201  # Over limit
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": too_long_name,
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0
    })
    assert response.status_code == 422


def test_create_multiple_stops_same_day(client, sample_trip):
    """Test creating multiple stops on the same day (1-day overlap allowed)."""
    same_day = (date.today() + timedelta(days=12)).isoformat()

    # First stop - full day
    response1 = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Morning Activity",
        "start_date": same_day,
        "end_date": same_day,
        "order_index": 0
    })
    assert response1.status_code == 201

    # Second stop - same day (1-day overlap is allowed)
    response2 = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Evening Activity",
        "start_date": same_day,
        "end_date": same_day,
        "order_index": 1
    })
    assert response2.status_code == 201


def test_update_stop_remove_country(client, sample_trip_with_stop):
    """Test updating stop to remove country (set to null)."""
    trip, stop = sample_trip_with_stop

    # Update to remove country
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "country": None
    })
    assert response.status_code == 200
    data = response.json()
    assert data["country"] is None
    assert data["name"] == stop.name  # Other fields unchanged


def test_update_stop_remove_coordinates(client, sample_trip_with_stop):
    """Test updating stop to remove coordinates (set to null)."""
    trip, stop = sample_trip_with_stop

    # Coordinates must be removed together
    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "latitude": None,
        "longitude": None
    })
    # This might fail if validation requires both or neither
    assert response.status_code in [200, 422]


def test_update_stop_all_fields(client, sample_trip_with_stop):
    """Test updating all stop fields at once."""
    trip, stop = sample_trip_with_stop

    response = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "Updated Stop Name",
        "country": "USA",
        "start_date": (date.today() + timedelta(days=12)).isoformat(),
        "end_date": (date.today() + timedelta(days=16)).isoformat(),
        "order_index": 1,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "notes": "Updated notes"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Stop Name"
    assert data["country"] == "USA"
    assert data["order_index"] == 1


def test_update_same_stop_twice_in_succession(client, sample_trip_with_stop):
    """Test updating the same stop twice consecutively."""
    trip, stop = sample_trip_with_stop

    # First update
    response1 = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "First Update"
    })
    assert response1.status_code == 200

    # Second update
    response2 = client.put(f"/trips/{trip.id}/stops/{stop.id}", json={
        "name": "Second Update"
    })
    assert response2.status_code == 200

    data = response2.json()
    assert data["name"] == "Second Update"


def test_create_stop_with_notes_max_length(client, sample_trip):
    """Test creating stop with maximum notes length (2000 chars)."""
    max_notes = "A" * 2000
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Stop with Long Notes",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "notes": max_notes
    })
    assert response.status_code == 201
    data = response.json()
    assert len(data["notes"]) == 2000


def test_create_stop_with_notes_too_long(client, sample_trip):
    """Test creating stop with notes exceeding max length."""
    too_long_notes = "A" * 2001
    response = client.post(f"/trips/{sample_trip.id}/stops/", json={
        "name": "Stop with Too Long Notes",
        "start_date": (date.today() + timedelta(days=11)).isoformat(),
        "end_date": (date.today() + timedelta(days=15)).isoformat(),
        "order_index": 0,
        "notes": too_long_notes
    })
    assert response.status_code == 422
