import pytest
from app.db.fake_db import FAKE_DB, NEXT_ID
from app.schemas.trip import Trip
from datetime import date


@pytest.fixture()
def sample_trip():
    return {
        "title": "Test Trip",
        "start_date": "2025-11-01",
        "end_date": "2025-11-10",
        "destinations": ["Paris", "London", "Tokyo"]
    }


@pytest.fixture(autouse=True)
def reset_fake_db(sample_trip):
    FAKE_DB.clear()
    FAKE_DB.append(Trip(id=1, **sample_trip))
    NEXT_ID["value"] = 2  # Reset NEXT_ID back to 1 (assuming the above trip has id=0)
