# app/routers/stops.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.stop import StopCreate, StopUpdate, Stop, StopReorder
from app.services.stop_service import StopService
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/trips/{trip_id}/stops", tags=["Stops"])


@router.post("/", response_model=Stop, status_code=201)
async def create_stop(
        trip_id: int,
        stop: StopCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Create a new stop for a trip.

    Requires authentication.

    Validates:
    - Trip exists and belongs to current user
    - Stop dates are within trip dates
    - order_index is unique within the trip
    - No overlaps with existing stops (allows 1-day overlap for transitions)
    """
    return await StopService.create_stop(trip_id, stop, db, current_user.id)


@router.get("/", response_model=List[Stop])
async def get_all_stops(
        trip_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get all stops for a trip, ordered by order_index.

    Requires authentication.
    """
    return await StopService.get_all_stops(trip_id, db, current_user.id)


@router.put("/reorder", response_model=List[Stop])
async def reorder_stops(
        trip_id: int,
        reorder: StopReorder,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Reorder stops in a trip.

    Requires authentication.

    Accepts a list of stop IDs in the desired order.
    Updates order_index for each stop accordingly.

    Example:
        PUT /trips/1/stops/reorder
        {"stop_ids": [23, 21, 22]}

        This will set:
        - Stop 23 -> order_index 0
        - Stop 21 -> order_index 1
        - Stop 22 -> order_index 2
    """
    return await StopService.reorder_stops(trip_id, reorder.stop_ids, db, current_user.id)


@router.get("/{stop_id}", response_model=Stop)
async def get_stop_by_id(
        trip_id: int,
        stop_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get a specific stop by ID.

    Requires authentication.
    """
    return await StopService.get_stop(trip_id, stop_id, db, current_user.id)


@router.put("/{stop_id}", response_model=Stop)
async def update_stop(
        trip_id: int,
        stop_id: int,
        stop_update: StopUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Update a stop.

    Requires authentication.

    Validates:
    - Trip exists and belongs to current user
    - Stop exists
    - If dates are updated, they're within trip dates
    - If order_index is updated, it's unique
    - No overlaps with other stops (allows 1-day overlap)
    - Coordinates match country
    """
    return await StopService.update_stop(trip_id, stop_id, stop_update, db, current_user.id)


@router.delete("/{stop_id}", response_model=Stop)
async def delete_stop(
        trip_id: int,
        stop_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Delete a stop from a trip.

    Requires authentication.
    """
    return await StopService.delete_stop(trip_id, stop_id, db, current_user.id)