# app/routers/trips.py
"""
Trip Router - HTTP endpoints for trip management.

Delegates business logic to TripService.
Router handles HTTP, Service handles business logic.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.trip import TripCreate, TripUpdate, Trip
from app.services.trip_service import TripService

# prefix="/trips" - all routes start with /trips
# tags=["Trips"] - groups routes in Swagger UI
router = APIRouter(prefix="/trips", tags=["Trips"])

# ==================== DEPENDENCY INJECTION ====================
"""
Depends(get_db) tells FastAPI:
1. Call get_db() before running the route
2. Pass the result (DB session) to the route
3. Close the session after the route finishes (even if error)

Without Depends = we'd repeat get_db() code in every route.
"""

# ==================== PYDANTIC VS SQLALCHEMY ====================
"""
TripCreate/TripUpdate (Pydantic) - validates INPUT from user
TripModel (SQLAlchemy) - represents DB records
Trip (Pydantic) - formats OUTPUT to user
"""


@router.get("/", response_model=List[Trip])
def get_all_trips(db: Session = Depends(get_db)):
    """
    Get all trips.
    SQL: SELECT * FROM trips;
    """
    return TripService.get_all_trips(db)


@router.post("/", response_model=Trip, status_code=201)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    """
    Create a new trip.
    SQL: INSERT INTO trips (...) VALUES (...);

    Pydantic validates before this runs:
    - title not empty
    - start_date not in past
    - end_date >= start_date
    """
    return TripService.create_trip(trip, db)


@router.get("/{trip_id}", response_model=Trip)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """
    Get trip by ID.
    SQL: SELECT * FROM trips WHERE id = ...;

    Raises: 404 if not found
    """
    return TripService.get_trip_or_404(trip_id, db)


@router.put("/{trip_id}", response_model=Trip)
def update_trip(
        trip_id: int,
        trip_update: TripUpdate,
        db: Session = Depends(get_db)
):
    """
    Update trip (partial updates supported).
    SQL: UPDATE trips SET ... WHERE id = ...;

    Only send fields you want to change.
    Example: {"title": "New Name"}  # dates unchanged

    Raises: 404 if not found, 400 if dates invalid
    """
    return TripService.update_trip(trip_id, trip_update, db)


@router.delete("/{trip_id}", response_model=Trip)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    """
    Delete trip by ID.
    SQL: DELETE FROM trips WHERE id = ...;

    Note: Also deletes all stops (CASCADE).
    Raises: 404 if not found
    """
    return TripService.delete_trip(trip_id, db)


# ==================== WHY SERVICE LAYER? ====================
"""
Router: HTTP only (get request → return response)
Service: Business logic (validation, DB operations)

Benefits:
- Reusable: call service from CLI, background jobs, etc.
- Testable: test business logic without HTTP
- Clean: router stays simple and readable
"""

# ==================== ROUTE ORDER MATTERS ====================
"""
FastAPI matches routes top-to-bottom, first match wins.
Static routes BEFORE dynamic routes:

✅ Correct:
    @router.get("/search")      # static first
    @router.get("/{trip_id}")   # dynamic after

❌ Wrong:
    @router.get("/{trip_id}")   # catches "/search"!
    @router.get("/search")      # never reached
"""