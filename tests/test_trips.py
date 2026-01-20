from datetime import date, datetime, timedelta

# client fixture comes from conftest.py automatically — no need to import
def test_create_trip_success(client):
    response = client.post("/trips/", json={
        "title": "Second Test Trip",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    print(response.status_code, response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Second Test Trip"


def test_create_trip_missing_fields(client):
    response = client.post("/trips/", json={
        "title": "Incomplete Trip"
        # Missing dates and destinations
    })
    assert response.status_code == 422  # Unprocessable Entity


def test_create_trip_missing_title(client):
    response = client.post("/trips/", json={
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 422


def test_create_trip_empty_title(client):
    response = client.post("/trips/", json={
        "title": "    ",
        "start_date": (date.today() + timedelta(days=10)).isoformat(),
        "end_date": (date.today() + timedelta(days=20)).isoformat()
    })
    assert response.status_code == 422
    assert "title must not be empty" in response.text


def test_create_trip_invalid_start_date(client):
    today = datetime.today().date()
    past_date = (datetime.today() - timedelta(days=1)).date().isoformat()
    future_date = (datetime.today() + timedelta(days=30)).date().isoformat()

    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": past_date,
        "end_date": future_date
    })
    assert response.status_code == 422
    assert f"start_date {past_date} cannot be in the past (today is {today})" in response.text


def test_create_trip_invalid_end_date(client):
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": (date.today() + timedelta(days=20)).isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat()
    })
    assert response.status_code == 422
    assert "end_date must be after or equal to start_date" in response.text


# def test_create_trip_with_100_destinations(client):
#     destinations = [f"City{i}" for i in range(1, 101)]
#     response = client.post("/trips/", json={
#         "title": "Big Trip",
#         "start_date": "2025-11-01",
#         "end_date": "2025-11-10",
#         "destinations": destinations
#     })
#     assert response.status_code == 200
#     data = response.json()
#     expected = [x.lower() for x in destinations]
#     assert data["destinations"] == expected


# def test_create_trip_valid_mixed_case_destinations(client):
#     response = client.post("/trips/", json={
#         "title": "Trip",
#         "start_date": "2025-11-01",
#         "end_date": "2025-11-10",
#         "destinations": ["Paris", "LondoN", "ToKyo", "ROME", "berlin"]
#     })
#     assert response.status_code == 200
#     data = response.json()
#     expected = [x.lower() for x in ["Paris", "LondoN", "ToKyo", "ROME", "berlin"]]
#     assert data["destinations"] == expected


# def test_create_trip_duplicate_destinations(client):
#     response = client.post("/trips/", json={
#         "title": "Broken Trip",
#         "start_date": "2025-11-01",
#         "end_date": "2025-11-10",
#         "destinations": ["Paris", "Paris", "Paris", "Paris", "Paris"]
#     })
#     assert response.status_code == 422
#     assert "destinations must not contain duplicates (case-insensitive)" in response.text


# def test_create_trip_duplicate_destinations_case_insensitive(client):
#     response = client.post("/trips/", json={
#         "title": "Broken Trip",
#         "start_date": "2025-11-01",
#         "end_date": "2025-11-10",
#         "destinations": ["Paris", "paris", "PAris", "PariS", "pArIs"]
#     })
#     assert response.status_code == 422
#     assert "destinations must not contain duplicates (case-insensitive)" in response.text


# def test_create_trip_over_limit_destinations(client):
#     response = client.post("/trips/", json={
#         "title": "Broken Trip",
#         "start_date": "2025-11-01",
#         "end_date": "2025-11-10",
#         "destinations": list(map(lambda i: f"City{i}", range(1, 151)))  # ["City1", "City2", "City3", ..., "City150"]
#     })
#     assert response.status_code == 422
#     assert "Too many destinations (limit is 100)" in response.text


# def test_create_trip_over_limit_duplicate_destinations(client):
#     response = client.post("/trips/", json={
#         "title": "Broken Trip",
#         "start_date": "2025-11-01",
#         "end_date": "2025-11-10",
#         "destinations": list(map(lambda i: "City", range(1, 151)))  # ["City", "City", ..., "City"] (150 duplicates)
#     })
#     assert response.status_code == 422
#     assert "Too many destinations (limit is 100)" in response.text


def test_get_all_trips(client, sample_trip):
    response = client.get("/trips/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(trip["title"] == "Test Trip" for trip in data)


def test_get_trip_by_id_success(client, sample_trip):
    response = client.get(f"/trips/{sample_trip.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_trip.id
    assert data["title"] == "Test Trip"


def test_get_trip_by_id_not_found(client):
    response = client.get("/trips/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


# def test_update_trip_success(client, sample_trip):
#     response = client.put(f"/trips/{sample_trip.id}", json={
#         "title": "Updated Trip",
#         "destinations": ["Tokyo", "Hoi An"]
#     })
#     assert response.status_code == 200
#     data = response.json()
#     expected = [x.lower() for x in ["Tokyo", "Hoi An"]]
#     assert data["title"] == "Updated Trip"
#     assert data["destinations"] == expected


def test_update_trip_title_success(client, sample_trip):
    response = client.put(f"/trips/{sample_trip.id}", json={
        "title": "Short Trip"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Short Trip"


def test_update_trip_not_found(client):
    response = client.put("/trips/999", json={
        "title": "Ghost Trip"
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


def test_update_trip_invalid_dates(client):
    response = client.put("/trips/1", json={
        "start_date": (date.today() + timedelta(days=20)).isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat()
    })
    assert response.status_code == 422
    assert "end_date must be after or equal to start_date" in response.text


def test_delete_trip_success(client, sample_trip):
    response = client.delete(f"/trips/{sample_trip.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_trip.id
    assert data["title"] == "Test Trip"


def test_delete_trip_not_found(client):
    response = client.delete("/trips/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip with ID 999 not found"


# Test:
# 1. activate venv (once): source .venv/bin/activate
# 2. Create a PostgreSQL database in terminal: sudo -u postgres psql -> CREATE DATABASE test_db; -> \q
# 3. PYTHONPATH=. pytest


# git:
# (first time - creating a new branch and working on that branch) git checkout -b BRANCH_NAME
# git status
# git add . (add ALL changes)
# git commit -m "Message..."
# git push -u origin BRANCH_NAME
