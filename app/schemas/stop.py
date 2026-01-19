# app/schemas/stop.py
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List
from datetime import date, timedelta

from app.validators.common_validators import (
    validate_title_name,
    validate_start_date,
    validate_end_date
)

from app.validators.stop_validators import (
    validate_latitude,
    validate_longitude,
    # validate_lat_lon_pair,
    validate_unique_ids
)


class StopCreate(BaseModel):
    """Schema for creating a new stop.
    This is what a client sends when creating a stop."""
    name: str = Field(..., min_length=1, max_length=200)
    country: Optional[str] = Field(None, max_length=120)  # later - add validation that country exists
    start_date: date
    end_date: date
    order_index: int = Field(..., ge=0)  # Must be >= 0  # validation - in router
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Ensure name is not empty after stripping whitespace."""
        return validate_title_name(name, "Stop name")

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, start_date_value) -> date:
        """Ensure start_date isn't in the past."""
        return validate_start_date(start_date_value)

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, end_date_value: date, info) -> date:
        """Ensure end_date is after or equal to start_date."""
        start_date_value = info.data.get('start_date')
        return validate_end_date(end_date_value, start_date_value)

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, lat: Optional[float]) -> Optional[float]:
        """Validate latitude if longitude is also provided."""
        return validate_latitude(lat)

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, lon: Optional[float], info) -> Optional[float]:
        """Validate longitude and ensure both lat/lon are provided together."""
        lat = info.data.get('latitude')
        return validate_longitude(lat, lon)

    # @model_validator(mode='after')
    # @classmethod
    # def validate_lat_lon_pair(cls, lat: Optional[float], lon: Optional[float]) -> Optional[float]:
    #


class StopUpdate(BaseModel):
    """Schema for updating a stop. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    country: Optional[str] = Field(None, max_length=120)  # what if the user tries change the country, but the stop (name) isn't in that country?
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    order_index: Optional[int] = Field(None, ge=0)  # validation - in router
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator('name')
    @classmethod
    def validate_name(cls, name: Optional[str]) -> Optional[str]:
        return validate_title_name(name, "Stop name") if name else None

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, start_date_value):
        return validate_start_date(start_date_value) if start_date_value else None

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, end_date_value: Optional[date], info) -> Optional[date]:
        start_date_value = info.data.get('start_date')
        return validate_end_date(end_date_value, start_date_value) if end_date_value else None

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, lat: Optional[float]) -> Optional[float]:
        return validate_latitude(lat)

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, lon: Optional[float], info) -> Optional[float]:
        lat = info.data.get('latitude')
        return validate_longitude(lat, lon)


class Stop(StopCreate):
    """Schema for returning a stop in a trip."""
    id: int
    trip_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={  # An example for Swagger
            "examples": [{
                "id": 1,
                "trip_id": 1,
                "name": "Tokyo",
                "country": "Japan",
                "start_date": (date.today() + timedelta(days=10)).isoformat(),
                "end_date": (date.today() + timedelta(days=20)).isoformat(),
                "order_index": 0,
                "latitude": 35.6762,
                "longitude": 139.6503,
                "notes": "Visit Shibuya and Shinjuku"
            }]
        }
    )


class StopReorder(BaseModel):
    """Schema for reordering stops in a trip."""
    stop_ids: List[int] = Field(..., min_length=1)

    @field_validator('stop_ids')
    @classmethod
    def validate_unique_ids(cls, stop_ids: List[int]) -> List[int]:
        return validate_unique_ids(stop_ids)

    model_config = ConfigDict(
        json_schema_extra={  # An example for Swagger
            "examples": [{
                "stop_ids": [3, 1, 2]
            }]
        }
    )
