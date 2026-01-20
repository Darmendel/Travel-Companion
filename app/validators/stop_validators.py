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


def validate_realistic_coordinates(lat: Optional[float], lon: Optional[float], country: Optional[str] = None) -> None:
    """
    Validate that coordinates are realistic (not null island, ocean anomalies, etc.)

    Checks:
    1. Not at (0, 0) - "Null Island" (unless legitimately in Gulf of Guinea)
    2. Not at common placeholder coordinates
    3. Optionally: rough country validation
    """
    if lat is None or lon is None:
        return  # No coordinates provided, skip validation

    # Check for "Null Island" (0, 0) - very rare legitimate location
    if lat == 0.0 and lon == 0.0:
        raise ValueError(
            "Coordinates (0, 0) appear to be a placeholder. "
            "Please provide the actual location coordinates."
        )

    # Check for other common placeholder values
    common_placeholders = [
        (0.0, 0.0),  # Null Island
        (1.0, 1.0),  # Common test value
        (90.0, 0.0),  # North Pole + Prime Meridian (unlikely)
        (-90.0, 0.0),  # South Pole + Prime Meridian (unlikely)
    ]

    if (lat, lon) in common_placeholders:
        raise ValueError(
            f"Coordinates ({lat}, {lon}) appear to be a placeholder value. "
            "Please provide actual location coordinates."
        )

    # Optional: Very rough country validation
    # This is approximate and would need a proper geocoding service for accuracy
    if country:
        # Example: Israel rough boundaries
        if country.lower() in ['israel', 'il']:
            if not (29.0 <= lat <= 33.5 and 34.0 <= lon <= 36.0):
                raise ValueError(
                    f"Coordinates ({lat}, {lon}) do not appear to be in {country}. "
                    "Please verify your location."
                )

        # Example: Japan rough boundaries
        elif country.lower() in ['japan', 'jp']:
            if not (24.0 <= lat <= 46.0 and 123.0 <= lon <= 154.0):
                raise ValueError(
                    f"Coordinates ({lat}, {lon}) do not appear to be in {country}. "
                    "Please verify your location."
                )

        # Example: USA rough boundaries
        elif country.lower() in ['united states', 'usa', 'us']:
            # Continental US + Alaska + Hawaii (very approximate)
            continental_us = (25.0 <= lat <= 49.0 and -125.0 <= lon <= -66.0)
            alaska = (51.0 <= lat <= 72.0 and -180.0 <= lon <= -130.0)
            hawaii = (18.0 <= lat <= 23.0 and -161.0 <= lon <= -154.0)

            if not (continental_us or alaska or hawaii):
                raise ValueError(
                    f"Coordinates ({lat}, {lon}) do not appear to be in {country}. "
                    "Please verify your location."
                )


def validate_unique_ids(stop_ids: List[int]) -> List[int]:
    """Ensure all stop IDs are unique."""
    if len(stop_ids) != len(set(stop_ids)):
        raise ValueError("stop_ids must not contain duplicates")
    return stop_ids