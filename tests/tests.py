def test_create_trip_with_100_destinations(client):
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


def test_create_trip_valid_mixed_case_destinations(client):
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


def test_create_trip_duplicate_destinations(client):
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "Paris", "Paris", "Paris", "Paris"]
    })
    assert response.status_code == 422
    assert "destinations must not contain duplicates (case-insensitive)" in response.text


def test_create_trip_duplicate_destinations_case_insensitive(client):
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "paris", "PAris", "PariS", "pArIs"]
    })
    assert response.status_code == 422
    assert "destinations must not contain duplicates (case-insensitive)" in response.text


def test_create_trip_over_limit_destinations(client):
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": list(map(lambda i: f"City{i}", range(1, 151)))  # ["City1", "City2", "City3", ..., "City150"]
    })
    assert response.status_code == 422
    assert "Too many destinations (limit is 100)" in response.text


def test_create_trip_over_limit_duplicate_destinations(client):
    response = client.post("/trips/", json={
        "title": "Broken Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": list(map(lambda i: "City", range(1, 151)))  # ["City", "City", ..., "City"] (150 duplicates)
    })
    assert response.status_code == 422
    assert "Too many destinations (limit is 100)" in response.text


def test_update_trip_success(client, sample_trip):
    response = client.put(f"/trips/{sample_trip.id}", json={
        "title": "Updated Trip",
        "destinations": ["Tokyo", "Hoi An"]
    })
    assert response.status_code == 200
    data = response.json()
    expected = [x.lower() for x in ["Tokyo", "Hoi An"]]
    assert data["title"] == "Updated Trip"
    assert data["destinations"] == expected