from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_trip_success():
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


def test_create_trip_missing_fields():
    response = client.post("/trips/", json={
        "title": "Incomplete Trip"
        # Missing dates and destinations
    })
    assert response.status_code == 422  # Unprocessable Entity


def test_create_trip_missing_title():
    response = client.post("/trips/", json={
        "start_date": "2025-09-01",
        "end_date": "2025-09-10",
        "destinations": ["New York"]
    })
    assert response.status_code == 422


def test_create_trip_invalid_dates():
    # End date before start date – Pydantic won’t validate this unless we add custom logic
    # But FastAPI will still allow it unless we write our own validator
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-09-10",
        "end_date": "2025-09-01",
        "destinations": ["Nowhere"]
    })
    assert response.status_code == 200  # It still works unless we add validation!


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
