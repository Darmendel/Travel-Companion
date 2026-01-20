# app/routers/stops.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.stop import StopCreate, StopUpdate, Stop, StopReorder
from app.services.stop_service import StopService

router = APIRouter(prefix="/trips/{trip_id}/stops", tags=["Stops"])


@router.post("/", response_model=Stop, status_code=201)
def create_stop(
        trip_id: int,
        stop: StopCreate,
        db: Session = Depends(get_db)
):
    """Create a new stop for a trip.

    Validates:
    - Trip exists
    - Stop dates are within trip dates
    - order_index is unique within the trip
    - No overlaps with existing stops (allows 1-day overlap for transitions)
    """
    return StopService.create_stop(trip_id, stop, db)


@router.get("/", response_model=List[Stop])
def get_all_stops(
        trip_id: int,
        db: Session = Depends(get_db)
):
    """Get all stops for a trip, ordered by order_index."""
    return StopService.get_all_stops(trip_id, db)


@router.put("/reorder", response_model=List[Stop])
def reorder_stops(
        trip_id: int,
        reorder: StopReorder,
        db: Session = Depends(get_db)
):
    """Reorder stops in a trip.

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
    return StopService.reorder_stops(trip_id, reorder.stop_ids, db)


@router.get("/{stop_id}", response_model=Stop)
def get_stop_by_id(
        trip_id: int,
        stop_id: int,
        db: Session = Depends(get_db)
):
    """Get a specific stop by ID."""
    return StopService.get_stop_or_404(trip_id, stop_id, db)


@router.put("/{stop_id}", response_model=Stop)
def update_stop(
        trip_id: int,
        stop_id: int,
        stop_update: StopUpdate,
        db: Session = Depends(get_db)
):
    """Update a stop.

    Validates:
    - Trip exists
    - Stop exists
    - If dates are updated, they're within trip dates
    - If order_index is updated, it's unique
    - No overlaps with other stops (allows 1-day overlap)
    - Coordinates match country
    """
    return StopService.update_stop(trip_id, stop_id, stop_update, db)


@router.delete("/{stop_id}", response_model=Stop)
def delete_stop(
        trip_id: int,
        stop_id: int,
        db: Session = Depends(get_db)
):
    """Delete a stop from a trip."""
    return StopService.delete_stop(trip_id, stop_id, db)
