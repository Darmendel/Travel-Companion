# app/validators/stop_validators.py
"""
Stop validators - pure validation functions without DB access.

These validators contain pure business logic that doesn't require database access.
They can be easily tested and reused across different parts of the application.
"""

from typing import List, Optional, Tuple
from datetime import date


def validate_latitude(lat: Optional[float]) -> Optional[float]:
    if lat is not None and not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    return lat


def validate_longitude(lon: Optional[float]) -> Optional[float]:
    if lon is not None and not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    return lon


def validate_realistic_coordinates(
        lat: Optional[float],
        lon: Optional[float],
        country: Optional[str] = None
) -> None:
    """
    Validate that coordinates are realistic (not null island, ocean anomalies, etc.)

    Checks:
    1. Not at (0, 0) - "Null Island" (unless legitimately in Gulf of Guinea)
    2. Not at common placeholder coordinates
    3. Optionally: rough country validation

    Args:
        lat: Latitude value
        lon: Longitude value
        country: Optional country name for boundary checking

    Raises:
        ValueError: If coordinates appear to be placeholders or don't match country
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

    # Very rough country validation
    # This is approximate and would need a proper geocoding service for accuracy
    if country:
        # Israel rough boundaries
        if country.lower() in ['israel', 'il']:
            if not (29.0 <= lat <= 33.5 and 34.0 <= lon <= 36.0):
                raise ValueError(
                    f"Coordinates ({lat}, {lon}) do not appear to be in {country}. "
                    "Please verify your location."
                )

        # Japan rough boundaries
        elif country.lower() in ['japan', 'jp']:
            if not (24.0 <= lat <= 46.0 and 123.0 <= lon <= 154.0):
                raise ValueError(
                    f"Coordinates ({lat}, {lon}) do not appear to be in {country}. "
                    "Please verify your location."
                )

        # USA rough boundaries
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


def validate_date_overlap(
        start_date: date,
        end_date: date,
        existing_stops: List[Tuple[date, date, str]],
        max_overlap_days: int = 1
) -> None:
    """
    Validate that dates don't overlap with existing stops by more than allowed.

    Allows:
    - Same-day transition (Stop A ends on day X, Stop B starts on day X)
    - One-day overlap (for travel days)

    Args:
        start_date: New stop start date
        end_date: New stop end date
        existing_stops: List of (start_date, end_date, name) tuples for existing stops
        max_overlap_days: Maximum allowed overlap in days (default: 1 for transitions)

    Raises:
        ValueError: If overlap exceeds max_overlap_days (if overlap > 1 day)

    """
    for existing_start, existing_end, stop_name in existing_stops:
        overlap_start = max(start_date, existing_start)
        overlap_end = min(end_date, existing_end)

        if overlap_start <= overlap_end:
            overlap_days = (overlap_end - overlap_start).days + 1

            if overlap_days > max_overlap_days:
                raise ValueError(
                    f"Stop dates overlap with '{stop_name}' by {overlap_days} days "
                    f"({overlap_start} to {overlap_end}). "
                    f"Maximum allowed overlap is {max_overlap_days} day(s) for transition."
                )


def validate_dates_within_range(
        start_date: date,
        end_date: date,
        range_start: date,
        range_end: date,
        range_name: str = "allowed range"
) -> None:
    """
    Validate that dates fall within a specified range.

    Args:
        start_date: Start date to validate
        end_date: End date to validate
        range_start: Beginning of allowed range
        range_end: End of allowed range
        range_name: Name of the range (for error messages)

    Raises:
        ValueError: If dates are outside the range
    """
    if start_date < range_start or end_date > range_end:
        raise ValueError(
            f"Dates must be within {range_name} dates ({range_start} to {range_end})"
        )
