# tests/test_trips.py
from datetime import date, datetime, timedelta
import pytest


# client fixture comes from conftest.py automatically – no need to import

@pytest.mark.asyncio
async def test_create_trip_success(client):
    response = await client.post("/trips/", json={
        "title": "Second Test Trip",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Second Test Trip"


@pytest.mark.asyncio
async def test_create_trip_missing_fields(client):
    response = await client.post("/trips/", json={
        "title": "Incomplete Trip"
        # Missing dates
    })
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_create_trip_missing_title(client):
    response = await client.post("/trips/", json={
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_trip_empty_title(client):
    response = await client.post("/trips/", json={
        "title": "    ",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 422
    assert "title must not be empty" in response.text


@pytest.mark.asyncio
async def test_create_trip_invalid_start_date(client):
    today = datetime.today().date()
    past_date = (datetime.today() - timedelta(days=1)).date().isoformat()
    future_date = (datetime.today() + timedelta(days=30)).date().isoformat()

    response = await client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": past_date,
        "end_date": future_date
    })
    assert response.status_code == 422
    assert f"start_date {past_date} cannot be in the past (today is {today})" in response.text


@pytest.mark.asyncio
async def test_create_trip_invalid_end_date(client):
    # Pydantic checks the dates *before* it gets to the trip service.
    # FastAPI returns ValidationError (422)

    response = await client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": (date.today() + timedelta(days=20)).isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat()
    })
    assert response.status_code == 422
    assert "end_date must be after or equal to start_date" in response.text


@pytest.mark.asyncio
async def test_get_all_trips(client, sample_trip):
    response = await client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(trip["title"] == "Test Trip" for trip in data)


@pytest.mark.asyncio
async def test_get_trip_by_id_success(client, sample_trip):
    response = await client.get(f"/trips/{sample_trip.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_trip.id
    assert data["title"] == "Test Trip"


@pytest.mark.asyncio
async def test_get_trip_by_id_not_found(client):
    response = await client.get("/trips/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


@pytest.mark.asyncio
async def test_update_trip_title_success(client, sample_trip):
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "title": "Short Trip"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Short Trip"


@pytest.mark.asyncio
async def test_update_trip_not_found(client):
    response = await client.put("/trips/999", json={
        "title": "Ghost Trip"
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


@pytest.mark.asyncio
async def test_update_trip_invalid_dates_pydantic(client, sample_trip):
    """Test Pydantic validation catches invalid dates when both are in request."""
    # When both dates are in the request, Pydantic validator catches it
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "start_date": (date.today() + timedelta(days=20)).isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat()
    })
    assert response.status_code == 422  # Pydantic validation
    assert "end_date must be after" in response.text.lower()


@pytest.mark.asyncio
async def test_update_trip_invalid_dates_service(client, sample_trip):
    """Test Service validation catches invalid dates when combining request with DB data."""
    # sample_trip has start_date = today + 10
    # Update only end_date to be before the existing start_date
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "end_date": (date.today() + timedelta(days=5)).isoformat()  # Before existing start!
    })
    assert response.status_code == 400  # Service validation
    assert "must be after" in response.text.lower()  # Fixed: more flexible match


@pytest.mark.asyncio
async def test_delete_trip_success(client, sample_trip):
    response = await client.delete(f"/trips/{sample_trip.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_trip.id
    assert data["title"] == "Test Trip"


@pytest.mark.asyncio
async def test_delete_trip_not_found(client):
    response = await client.delete("/trips/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


# ==================== CREATE TRIP - ADDITIONAL TESTS ====================

@pytest.mark.asyncio
async def test_create_trip_same_start_and_end_date(client):
    """Test creating a trip that starts and ends on the same day."""
    same_date = (date.today() + timedelta(days=10)).isoformat()
    response = await client.post("/trips/", json={
        "title": "One Day Trip",
        "start_date": same_date,
        "end_date": same_date
    })
    assert response.status_code == 201
    data = response.json()
    assert data["start_date"] == data["end_date"]


@pytest.mark.asyncio
async def test_create_trip_very_long_duration(client):
    """Test creating a trip with very long duration (1 year)."""
    response = await client.post("/trips/", json={
        "title": "Year Long Adventure",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=375)).isoformat()
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Year Long Adventure"


@pytest.mark.asyncio
async def test_create_trip_with_special_characters_in_title(client):
    """Test creating trip with special characters in title."""
    response = await client.post("/trips/", json={
        "title": "Trip to São Paulo & Tokyo! 🌍",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 201
    data = response.json()
    assert "São Paulo" in data["title"]


@pytest.mark.asyncio
async def test_create_trip_with_very_long_title(client):
    """Test creating trip with maximum length title."""
    long_title = "A" * 200  # Assuming max is around 200-255
    response = await client.post("/trips/", json={
        "title": long_title,
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    # Should succeed or fail gracefully depending on max length
    assert response.status_code in [201, 422]


@pytest.mark.asyncio
async def test_create_trip_start_date_is_today(client):
    """Test creating trip starting today (edge case)."""
    response = await client.post("/trips/", json={
        "title": "Starting Today",
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat()
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_trip_far_future(client):
    """Test creating trip far in the future (5 years)."""
    response = await client.post("/trips/", json={
        "title": "Future Trip",
        "start_date": (date.today() + timedelta(days=1825)).isoformat(),  # ~5 years
        "end_date": (date.today() + timedelta(days=1835)).isoformat()
    })
    assert response.status_code == 201


# ==================== UPDATE TRIP - ADDITIONAL TESTS ====================

@pytest.mark.asyncio
async def test_update_trip_only_start_date(client, sample_trip):
    """Test updating only the start date."""
    new_start = (date.today() + timedelta(days=12)).isoformat()
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "start_date": new_start
    })
    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == new_start
    assert data["title"] == "Test Trip"  # Unchanged


@pytest.mark.asyncio
async def test_update_trip_only_end_date(client, sample_trip):
    """Test updating only the end date."""
    new_end = (date.today() + timedelta(days=25)).isoformat()
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "end_date": new_end
    })
    assert response.status_code == 200
    data = response.json()
    assert data["end_date"] == new_end
    assert data["title"] == "Test Trip"  # Unchanged


@pytest.mark.asyncio
async def test_update_trip_all_fields(client, sample_trip):
    """Test updating all fields at once."""
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "title": "Completely New Trip",
        "start_date": (date.today() + timedelta(days=15)).isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat()
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Completely New Trip"
    assert data["id"] == sample_trip.id  # ID unchanged


@pytest.mark.asyncio
async def test_update_trip_empty_body(client, sample_trip):
    """Test updating with empty JSON body."""
    response = await client.put(f"/trips/{sample_trip.id}", json={})
    assert response.status_code == 200
    data = response.json()
    # Nothing should change
    assert data["title"] == sample_trip.title
    assert data["id"] == sample_trip.id


@pytest.mark.asyncio
async def test_update_trip_invalid_field(client, sample_trip):
    """Test updating with invalid/unknown field."""
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "invalid_field": "should be ignored"
    })
    # Should either ignore or reject
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_update_trip_extend_dates(client, sample_trip):
    """Test extending trip duration."""
    # Get original duration
    original_duration = (sample_trip.end_date - sample_trip.start_date).days

    # Extend by adding 30 more days to the current end_date
    new_end = sample_trip.end_date + timedelta(days=30)

    response = await client.put(f"/trips/{sample_trip.id}", json={
        "end_date": new_end.isoformat()
    })
    assert response.status_code == 200
    data = response.json()

    # Calculate new duration
    new_duration = (
            datetime.fromisoformat(data["end_date"]).date() -
            datetime.fromisoformat(data["start_date"]).date()
    ).days

    # Should be exactly 30 days longer
    assert new_duration == original_duration + 30


@pytest.mark.asyncio
async def test_update_trip_shorten_dates(client, sample_trip):
    """Test shortening trip duration."""
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "end_date": (date.today() + timedelta(days=15)).isoformat()
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_trip_to_empty_title(client, sample_trip):
    """Test updating trip to have empty title - should fail."""
    response = await client.put(f"/trips/{sample_trip.id}", json={
        "title": "   "
    })
    assert response.status_code == 422
    assert "must not be empty" in response.text


# ==================== DELETE TRIP - ADDITIONAL TESTS ====================

@pytest.mark.asyncio
async def test_delete_trip_twice(client, sample_trip):
    """Test deleting the same trip twice - second should fail."""
    # First delete
    response1 = await client.delete(f"/trips/{sample_trip.id}")
    assert response1.status_code == 200

    # Second delete - should fail
    response2 = await client.delete(f"/trips/{sample_trip.id}")
    assert response2.status_code == 404


@pytest.mark.asyncio
async def test_delete_trip_with_stops_cascade(client, sample_trip_with_stop):
    """Test that deleting a trip also deletes its stops (CASCADE)."""
    trip, stop = sample_trip_with_stop

    # Delete the trip
    response = await client.delete(f"/trips/{trip.id}")
    assert response.status_code == 200

    # Verify trip is gone
    get_trip_response = await client.get(f"/trips/{trip.id}")
    assert get_trip_response.status_code == 404

    # Verify stop is also gone (CASCADE delete)
    get_stop_response = await client.get(f"/trips/{trip.id}/stops/{stop.id}")
    assert get_stop_response.status_code == 404


# ==================== GET ALL TRIPS - ADDITIONAL TESTS ====================

@pytest.mark.asyncio
async def test_get_all_trips_empty(client):
    """Test getting all trips when none exist."""
    response = await client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Might be empty or might have trips from other tests


@pytest.mark.asyncio
async def test_get_all_trips_multiple(client, db_session):
    """Test getting all trips when multiple exist."""
    from app.models.trip import Trip as TripModel

    # Create multiple trips
    trips = [
        TripModel(
            title=f"Trip {i}",
            start_date=date.today() + timedelta(days=10 + i * 10),
            end_date=date.today() + timedelta(days=15 + i * 10)
        )
        for i in range(3)
    ]
    for trip in trips:
        db_session.add(trip)
    await db_session.commit()

    response = await client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_get_all_trips_returns_correct_fields(client, sample_trip):
    """Test that GET /trips returns all required fields."""
    response = await client.get("/trips/")
    assert response.status_code == 200
    data = response.json()

    if len(data) > 0:
        trip = data[0]
        assert "id" in trip
        assert "title" in trip
        assert "start_date" in trip
        assert "end_date" in trip


# ==================== EDGE CASES & ERROR HANDLING ====================

@pytest.mark.asyncio
async def test_create_trip_with_null_title(client):
    """Test creating trip with null title."""
    response = await client.post("/trips/", json={
        "title": None,
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_trip_with_invalid_date_format(client):
    """Test creating trip with invalid date format."""
    response = await client.post("/trips/", json={
        "title": "Invalid Date Trip",
        "start_date": "not-a-date",
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_trip_negative_id(client):
    """Test updating trip with negative ID."""
    response = await client.put("/trips/-1", json={
        "title": "Negative ID"
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_trip_negative_id(client):
    """Test deleting trip with negative ID."""
    response = await client.delete("/trips/-1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_trip_negative_id(client):
    """Test getting trip with negative ID."""
    response = await client.get("/trips/-1")
    assert response.status_code == 404


# ==================== CONCURRENT OPERATIONS ====================

@pytest.mark.asyncio
async def test_update_same_trip_twice(client, sample_trip):
    """Test updating the same trip twice in succession."""
    # First update
    response1 = await client.put(f"/trips/{sample_trip.id}", json={
        "title": "First Update"
    })
    assert response1.status_code == 200

    # Second update
    response2 = await client.put(f"/trips/{sample_trip.id}", json={
        "title": "Second Update"
    })
    assert response2.status_code == 200

    data = response2.json()
    assert data["title"] == "Second Update"

# Test:
# 1. activate venv (once): source .venv/bin/activate
# 2. Create a PostgreSQL database in terminal: sudo -u postgres psql -> CREATE DATABASE test_db; -> \q
# 3. PYTHONPATH=. pytest tests/test_trips.py -v

# git:
# (first time - creating a new branch and working on that branch) git checkout -b BRANCH_NAME
# git status
# git add . (add ALL changes)
# git commit -m "Message..."
# git push -u origin BRANCH_NAME