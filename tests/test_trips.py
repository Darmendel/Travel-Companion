from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_trip():
    response = client.post("/trips/", json={
        "title": "Test Trip",
        "start_date": "2025-09-01",
        "end_date": "2025-09-10",
        "destinations": ["Paris", "London", "Tokyo"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Trip"
    assert data["id"] == 1  # Assuming it's the first trip


def test_get_all_trips():
    response = client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # ?


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


# Test: PYTHONPATH=. pytest
