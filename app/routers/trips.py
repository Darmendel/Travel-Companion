# app/routers/trips.py
"""
Async Trip Router - HTTP endpoints for trip management.

Delegates business logic to TripService.
Router handles HTTP, Service handles business logic.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.trip import TripCreate, TripUpdate, Trip
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("/", response_model=List[Trip])
async def get_all_trips(db: AsyncSession = Depends(get_db)):
    """
    Get all trips.
    SQL: SELECT * FROM trips;
    """
    return await TripService.get_all_trips(db)


@router.post("/", response_model=Trip, status_code=201)
async def create_trip(trip: TripCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new trip.
    SQL: INSERT INTO trips (...) VALUES (...);

    Pydantic validates before this runs:
    - title not empty
    - start_date not in past
    - end_date >= start_date
    """
    return await TripService.create_trip(trip, db)


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get trip by ID.
    SQL: SELECT * FROM trips WHERE id = ...;

    Raises: 404 if not found
    """
    return await TripService.get_trip(trip_id, db)


@router.put("/{trip_id}", response_model=Trip)
async def update_trip(
        trip_id: int,
        trip_update: TripUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    Update trip (partial updates supported).
    SQL: UPDATE trips SET ... WHERE id = ...;

    Only send fields you want to change.
    Example: {"title": "New Name"}  # dates unchanged

    Raises: 404 if not found, 400 if dates invalid
    """
    return await TripService.update_trip(trip_id, trip_update, db)


@router.delete("/{trip_id}", response_model=Trip)
async def delete_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete trip by ID.
    SQL: DELETE FROM trips WHERE id = ...;

    Note: Also deletes all stops (CASCADE).
    Raises: 404 if not found
    """
    return await TripService.delete_trip(trip_id, db)


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
