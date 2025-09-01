from datetime import date, datetime
from typing import List


def validate_title(title: str):
    if not title.strip():
        raise ValueError("title must not be empty")
    return title


def validate_start_date(start_date: date):
    today = datetime.today().date()
    if start_date < today:
        raise ValueError(f"start_date {start_date} cannot be in the past (today is {today})")
    return start_date


def validate_end_date(end_date: date, start_date: date | None):
    if start_date and end_date < start_date:
        raise ValueError("end_date must be after or equal to start_date")
    return end_date


def validate_destinations(destinations: List[str]):
    # limit to 100 destinations
    # Enforce a Reasonable Max Length. This prevents malicious or bloated input like ["Paris"] * 1000000
    if len(destinations) > 100:
        raise ValueError("Too many destinations (limit is 100)")

    cleaned = [d.strip().lower() for d in destinations]
    if len(cleaned) != len(set(cleaned)):
        raise ValueError("destinations must not contain duplicates (case-insensitive)")
    return cleaned
