# tests/test_stops.py
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
        "latitude": 34.0522,
        "longitude": -118.2437
    })
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 34.0522
    assert data["longitude"] == -118.2437


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
