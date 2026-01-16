from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional
from datetime import date

from app.validators.trip_validators import (
    validate_title,
    validate_start_date,
    validate_end_date
)


# This model defines the structure expected in POST requests
# Validates input when creating a new trip.
class TripCreate(BaseModel):
    title: str = Field(..., min_length=1)  # prevents empty title
    start_date: date
    end_date: date

    @field_validator('title')
    @classmethod
    def validate_title(cls, title):
        return validate_title(title)

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, start_date_value):
        return validate_start_date(start_date_value)

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, end_date_value, info):
        start_date_value = info.data.get('start_date')
        return validate_end_date(end_date_value, start_date_value)


class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, title):
        return validate_title(title) if title else None

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, start_date_value):
        return validate_start_date(start_date_value) if start_date_value else None

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, end_date_value, info):
        start_date_value = info.data.get('start_date')
        return validate_end_date(end_date_value, start_date_value) if end_date_value else None


# Defines how a trip is returned in responses.
class Trip(TripCreate):
    id: int  # id field (from the DB), which the client doesn’t send, but the server includes in responses.
    title: str  # Name of the trip (required string)
    start_date: date
    end_date: date

    class Config:
        model_config = ConfigDict(from_attributes=True)  # Enables compatibility with ORM objects (e.g., SQLAlchemy) -
        # This tells FastAPI it can read data from SQLAlchemy models (like .id, .name, etc.)
        # and convert them to Pydantic JSON.
