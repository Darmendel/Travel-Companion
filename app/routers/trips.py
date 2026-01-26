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
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("/", response_model=List[Trip])
async def get_all_trips(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get all trips for the current user.
    SQL: SELECT * FROM trips WHERE user_id = current_user.id;

    Requires authentication.
    """
    return await TripService.get_all_trips(db, current_user.id)


@router.post("/", response_model=Trip, status_code=201)
async def create_trip(
        trip: TripCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Create a new trip for the current user.
    SQL: INSERT INTO trips (..., user_id) VALUES (..., current_user.id);

    Requires authentication.

    Pydantic validates before this runs:
    - title not empty
    - start_date not in past
    - end_date >= start_date
    """
    return await TripService.create_trip(trip, db, current_user.id)


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(
        trip_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Get trip by ID.
    SQL: SELECT * FROM trips WHERE id = ... AND user_id = current_user.id;

    Requires authentication.
    Only returns trip if it belongs to current user.

    Raises: 404 if not found or doesn't belong to user
    """
    return await TripService.get_trip(trip_id, db, current_user.id)


@router.put("/{trip_id}", response_model=Trip)
async def update_trip(
        trip_id: int,
        trip_update: TripUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Update trip (partial updates supported).
    SQL: UPDATE trips SET ... WHERE id = ... AND user_id = current_user.id;

    Requires authentication.
    Only updates trip if it belongs to current user.

    Only send fields you want to change.
    Example: {"title": "New Name"}  # dates unchanged

    Raises: 404 if not found or doesn't belong to user
             400 if dates invalid
    """
    return await TripService.update_trip(trip_id, trip_update, db, current_user.id)


@router.delete("/{trip_id}", response_model=Trip)
async def delete_trip(
        trip_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Delete trip by ID.
    SQL: DELETE FROM trips WHERE id = ... AND user_id = current_user.id;

    Requires authentication.
    Only deletes trip if it belongs to current user.

    Note: Also deletes all stops (CASCADE).
    Raises: 404 if not found or doesn't belong to user
    """
    return await TripService.delete_trip(trip_id, db, current_user.id)


# ==================== DEPENDENCY INJECTION ====================
"""
Depends(get_db) tells FastAPI:
1. Call get_db() before running the route
2. Pass the result (DB session) to the route
3. Close the session after the route finishes (even if error)

Depends(get_current_user) tells FastAPI:
1. Extract JWT token from Authorization header
2. Verify token is valid
3. Fetch user from database
4. Pass user object to the route
5. Return 401 if token invalid

Without Depends = we'd repeat get_db() and authentication code in every route.
"""

# ==================== PYDANTIC VS SQLALCHEMY ====================
"""
TripCreate/TripUpdate (Pydantic) - validates INPUT from user
TripModel (SQLAlchemy) - represents DB records
Trip (Pydantic) - formats OUTPUT to user
"""