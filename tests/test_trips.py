from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app

client = TestClient(app)


def test_create_trip_success():
    response = client.post("/trips/", json={
        "title": "Test Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "London", "Tokyo"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Trip"
    assert data["id"] == 1  # Assuming it's the first trip


def test_create_trip_missing_fields():
    response = client.post("/trips/", json={
        "title": "Incomplete Trip"
        # Missing dates and destinations
    })
    assert response.status_code == 422  # Unprocessable Entity


def test_create_trip_missing_title():
    response = client.post("/trips/", json={
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["New York"]
    })
    assert response.status_code == 422


def test_create_trip_empty_title():
    response = client.post("/trips/", json={
        "title": "    ",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["New York"]
    })
    assert response.status_code == 422
    assert "title must not be empty" in response.text


def test_create_trip_invalid_start_date():
    today = datetime.today().date()
    past_date = (datetime.today() - timedelta(days=1)).date().isoformat()
    future_date = (datetime.today() + timedelta(days=30)).date().isoformat()

    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": past_date,
        "end_date": future_date,
        "destinations": ["Nowhere"]
    })
    assert response.status_code == 422
    assert f"start_date {past_date} cannot be in the past (today is {today})" in response.text


def test_create_trip_invalid_end_date():
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-10",
        "end_date": "2025-11-01",
        "destinations": ["Nowhere"]
    })
    assert response.status_code == 422
    assert "end_date must be after or equal to start_date" in response.text


def test_create_trip_with_100_destinations():
    destinations = [f"City{i}" for i in range(1, 101)]
    response = client.post("/trips/", json={
        "title": "Big Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": destinations
    })
    assert response.status_code == 200
    data = response.json()
    expected = [x.lower() for x in destinations]
    assert data["destinations"] == expected


def test_create_trip_valid_mixed_case_destinations():
    response = client.post("/trips/", json={
        "title": "Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "LondoN", "ToKyo", "ROME", "berlin"]
    })
    assert response.status_code == 200
    data = response.json()
    expected = [x.lower() for x in ["Paris", "LondoN", "ToKyo", "ROME", "berlin"]]
    assert data["destinations"] == expected


def test_create_trip_duplicate_destinations():
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "Paris", "Paris", "Paris", "Paris"]
    })
    assert response.status_code == 422
    assert "destinations must not contain duplicates (case-insensitive)" in response.text


def test_create_trip_duplicate_destinations_case_insensitive():
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "paris", "PAris", "PariS", "pArIs"]
    })
    assert response.status_code == 422
    assert "destinations must not contain duplicates (case-insensitive)" in response.text


def test_create_trip_over_limit_destinations():
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": list(map(lambda i: f"City{i}", range(1, 151)))  # ["City1", "City2", "City3", ..., "City150"]
    })
    assert response.status_code == 422
    assert "Too many destinations (limit is 100)" in response.text


def test_create_trip_over_limit_duplicate_destinations():
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": list(map(lambda i: "City", range(1, 151)))  # ["City", "City", ..., "City"] (150 duplicates)
    })
    assert response.status_code == 422
    assert "Too many destinations (limit is 100)" in response.text


def test_get_all_trips():
    response = client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(trip["title"] == "Test Trip" for trip in data)


def test_get_trip_by_id_success():
    response = client.get("/trips/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Trip"


def test_get_trip_by_id_not_found():
    response = client.get("/trips/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


def test_delete_trip_success():
    response = client.delete("/trips/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Trip"


def test_delete_trip_not_found():
    response = client.delete("/trips/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


# Test: PYTHONPATH=. pytest


# git:
# (first time - creating a new branch and working on that branch) git checkout -b BRANCH_NAME
# git status
# git add . (add ALL changes)
# git commit -m "Message..."
# git push -u origin BRANCH_NAME
