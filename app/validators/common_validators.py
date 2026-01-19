# app/validators/common_validators.py
from datetime import date, datetime


def validate_title_name(tn: str, s: str):
    """Ensure name is not empty after stripping whitespace."""
    if not tn.strip():
        raise ValueError(f"{s} must not be empty")
    return tn


def validate_start_date(start_date: date):
    """Ensure start_date isn't in the past."""
    today = datetime.today().date()
    if start_date < today:
        raise ValueError(f"start_date {start_date} cannot be in the past (today is {today})")
    return start_date


def validate_end_date(end_date: date, start_date: date | None):
    """Ensure end_date is after or equal to start_date."""
    if start_date and end_date < start_date:
        raise ValueError("end_date must be after or equal to start_date")
    return end_date
