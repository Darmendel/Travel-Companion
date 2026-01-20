# app/routers/stops.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from app.db.session import get_db
from app.models.stop import Stop as StopModel
from app.models.trip import Trip as TripModel
from app.schemas.stop import StopCreate, StopUpdate, Stop, StopReorder

router = APIRouter(prefix="/trips/{trip_id}/stops", tags=["Stops"])


def get_trip(trip_id: int, db: Session) -> TripModel:
    """Helper function to get trip or raise 404."""
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")
    return trip


def get_stop(trip_id: int, stop_id: int, db: Session) -> StopModel:
    """Helper function to get stop or raise 404."""
    stop = db.query(StopModel).filter(
        StopModel.id == stop_id,
        StopModel.trip_id == trip_id
    ).first()
    if not stop:
        raise HTTPException(status_code=404, detail=f"Stop with ID {stop_id} not found in trip {trip_id}")
    return stop


def check_date_overlap(new_stop_start, new_stop_end, trip_id: int, db: Session, exclude_stop_id: int = None):
    """
    Check if new stop dates overlap with existing stops by more than 1 day.

    Allows:
    - Same-day transition (Stop A ends on day X, Stop B starts on day X)
    - One-day overlap (for travel days)

    Warns/Blocks:
    - Overlaps of more than 1 day
    """
    # Get all other stops in the trip
    query = db.query(StopModel).filter(StopModel.trip_id == trip_id)
    if exclude_stop_id:
        query = query.filter(StopModel.id != exclude_stop_id)

    existing_stops = query.all()

    for stop in existing_stops:
        # Calculate overlap
        overlap_start = max(new_stop_start, stop.start_date)
        overlap_end = min(new_stop_end, stop.end_date)

        if overlap_start <= overlap_end:
            # There is an overlap
            overlap_days = (overlap_end - overlap_start).days + 1

            # Allow up to 1 day overlap (transition day)
            if overlap_days > 1:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Stop dates overlap with '{stop.name}' by {overlap_days} days "
                        f"({overlap_start} to {overlap_end}). "
                        f"Maximum allowed overlap is 1 day for transition."
                    )
                )


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
    # Verify trip exists
    trip = get_trip(trip_id, db)

    # Validate stop dates are within trip dates
    if stop.start_date < trip.start_date or stop.end_date > trip.end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Stop dates must be within trip dates ({trip.start_date} to {trip.end_date})"
        )

    # Check for date overlaps
    check_date_overlap(stop.start_date, stop.end_date, trip_id, db)

    # Check if order_index already exists for this trip
    existing_stop = db.query(StopModel).filter(
        StopModel.trip_id == trip_id,
        StopModel.order_index == stop.order_index
    ).first()

    if existing_stop:
        raise HTTPException(
            status_code=400,
            detail=f"Stop with order_index {stop.order_index} already exists in this trip"
        )

    # Create the stop
    new_stop = StopModel(**stop.model_dump(), trip_id=trip_id)
    db.add(new_stop)
    db.commit()
    db.refresh(new_stop)
    return new_stop


@router.get("/", response_model=List[Stop])
def get_all_stops(
        trip_id: int,
        db: Session = Depends(get_db)
):
    """Get all stops for a trip, ordered by order_index."""
    # Verify trip exists
    get_trip(trip_id, db)

    # Get all stops for this trip, ordered by order_index
    stops = db.query(StopModel).filter(
        StopModel.trip_id == trip_id
    ).order_by(StopModel.order_index).all()

    return stops


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
        {"stop_ids": [3, 1, 2]}

        This will set:
        - Stop 3 -> order_index 0
        - Stop 1 -> order_index 1
        - Stop 2 -> order_index 2
    """
    # Verify trip exists
    get_trip(trip_id, db)

    # Get all stops for this trip
    stops = db.query(StopModel).filter(StopModel.trip_id == trip_id).all()
    stop_ids_in_db = {stop.id for stop in stops}

    # Validate that all provided stop IDs exist in this trip
    provided_ids = set(reorder.stop_ids)
    if provided_ids != stop_ids_in_db:
        missing = stop_ids_in_db - provided_ids
        extra = provided_ids - stop_ids_in_db
        error_msg = []
        if missing:
            error_msg.append(f"Missing stop IDs: {sorted(missing)}")
        if extra:
            error_msg.append(f"Invalid stop IDs (not in this trip): {sorted(extra)}")
        raise HTTPException(
            status_code=400,
            detail="; ".join(error_msg)
        )

    # Update order_index for each stop
    stop_map = {stop.id: stop for stop in stops}
    for new_index, stop_id in enumerate(reorder.stop_ids):
        stop_map[stop_id].order_index = new_index

    db.commit()

    # Return updated stops in new order
    updated_stops = db.query(StopModel).filter(
        StopModel.trip_id == trip_id
    ).order_by(StopModel.order_index).all()

    return updated_stops


@router.get("/{stop_id}", response_model=Stop)
def get_stop_by_id(
        trip_id: int,
        stop_id: int,
        db: Session = Depends(get_db)
):
    """Get a specific stop by ID."""
    stop = get_stop(trip_id, stop_id, db)
    return stop


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
    """
    # Verify trip exists
    get_trip(trip_id, db)

    # Get the stop
    stop = get_stop(trip_id, stop_id, db)
    trip = stop.trip

    # Get update data (only provided fields)
    update_data = stop_update.model_dump(exclude_unset=True)

    # Validate dates if they're being updated
    new_start = update_data.get("start_date", stop.start_date)
    new_end = update_data.get("end_date", stop.end_date)

    # Check that stop dates are within trip dates
    if new_start < trip.start_date or new_end > trip.end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Stop dates must be within trip dates ({trip.start_date} to {trip.end_date})"
        )

    # Check for date overlaps (excluding current stop)
    if "start_date" in update_data or "end_date" in update_data:
        check_date_overlap(new_start, new_end, trip_id, db, exclude_stop_id=stop_id)

    # If order_index is being updated, check it's unique
    if "order_index" in update_data:
        new_order = update_data["order_index"]
        existing_stop = db.query(StopModel).filter(
            StopModel.trip_id == trip_id,
            StopModel.order_index == new_order,
            StopModel.id != stop_id  # Exclude current stop
        ).first()

        if existing_stop:
            raise HTTPException(
                status_code=400,
                detail=f"Stop with order_index {new_order} already exists in this trip"
            )

    # Apply updates
    for key, value in update_data.items():
        setattr(stop, key, value)

    db.commit()
    db.refresh(stop)
    return stop


@router.delete("/{stop_id}", response_model=Stop)
def delete_stop(
        trip_id: int,
        stop_id: int,
        db: Session = Depends(get_db)
):
    """Delete a stop from a trip."""
    stop = get_stop(trip_id, stop_id, db)

    db.delete(stop)
    db.commit()
    return stop
