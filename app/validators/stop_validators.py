# app/validators/stop_validators.py
from typing import Optional, List


def validate_latitude(lat: Optional[float]) -> Optional[float]:
    """Validate latitude if longitude is also provided."""
    if lat is not None and not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    return lat


def validate_longitude(lat: float, lon: Optional[float]) -> Optional[float]:
    """Validate longitude and ensure both lat/lon are provided together."""

    # If one is provided, both must be provided
    if (lat is not None and lon is None) or (lat is None and lon is not None):
        raise ValueError("Both latitude and longitude must be provided together")

    if lon is not None and not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180")

    return lon


# def validate_lat_lon_pair(lat: Optional[float], lon: Optional[float]) -> Optional[float]:
#     if (not lat) ^ (not lon):
#         raise ValueError("Both latitude and longitude must be provided together or omitted together")


def validate_unique_ids(stop_ids: List[int]) -> List[int]:
    """Ensure all stop IDs are unique."""
    if len(stop_ids) != len(set(stop_ids)):
         raise ValueError("stop_ids must not contain duplicates")
    return stop_ids
