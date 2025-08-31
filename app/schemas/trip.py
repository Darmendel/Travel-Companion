from pydantic import BaseModel
from typing import List
from datetime import date


# This model defines the structure expected in POST requests
# Validates input when creating a new trip.
class TripCreate(BaseModel):
    title: str  # Name of the trip (required string)
    # description: str | None = None
    start_date: date
    end_date: date
    destinations: List[str]


# Defines how a trip is returned in responses.
class Trip(TripCreate):
    id: int  # id field (from the DB), which the client doesn’t send, but the server includes in responses.
    title: str  # Name of the trip (required string)
    start_date: date
    end_date: date
    destinations: List[str]

    class Config:
        orm_mode = True  # Enables compatibility with ORM objects (e.g., SQLAlchemy) -
        # This tells FastAPI it can read data from SQLAlchemy models (like .id, .name, etc.)
        # and convert them to Pydantic JSON.
