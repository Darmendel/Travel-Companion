from pydantic import BaseModel, ConfigDict, field_validator, Field, constr
from typing import List
from datetime import date, datetime


# This model defines the structure expected in POST requests
# Validates input when creating a new trip.
class TripCreate(BaseModel):
    title: str = Field(..., min_length=1)  # prevents empty title
    # description: str | None = None
    start_date: date
    end_date: date
    destinations: List[str]  # destinations: List[constr(min_length=1, max_length=50)] = Field(..., max_items=100)

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, title):
        if not title.strip():
            raise ValueError("title must not be empty")
        return title

    @field_validator('start_date')
    @classmethod
    def start_date_must_not_be_in_past(cls, start_date_value):
        today = datetime.today().date()
        if start_date_value < today:
            raise ValueError(f"start_date {start_date_value} cannot be in the past (today is {today})")
        return start_date_value

    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, end_date_value, info):
        start_date_value = info.data.get('start_date')
        if start_date_value and end_date_value < start_date_value:
            raise ValueError("end_date must be after or equal to start_date")
        return end_date_value

    @field_validator('destinations')
    @classmethod
    def destinations_must_be_unique(cls, destinations_list):
        # limit to 100 destinations
        # Enforce a Reasonable Max Length. This prevents malicious or bloated input like ["Paris"] * 1000000
        if len(destinations_list) > 100:
            raise ValueError("Too many destinations (limit is 100)")

        cleaned = [d.strip().lower() for d in destinations_list]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("destinations must not contain duplicates (case-insensitive)")
        return cleaned


# Defines how a trip is returned in responses.
class Trip(TripCreate):
    id: int  # id field (from the DB), which the client doesn’t send, but the server includes in responses.
    title: str  # Name of the trip (required string)
    start_date: date
    end_date: date
    destinations: List[str]

    class Config:
        model_config = ConfigDict(from_attributes=True)  # Enables compatibility with ORM objects (e.g., SQLAlchemy) -
        # This tells FastAPI it can read data from SQLAlchemy models (like .id, .name, etc.)
        # and convert them to Pydantic JSON.
