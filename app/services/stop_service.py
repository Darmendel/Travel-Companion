# app/services/stop_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.models.stop import Stop as StopModel
from app.models.trip import Trip as TripModel
from app.schemas.stop import StopCreate, StopUpdate
from app.validators.stop_validators import validate_realistic_coordinates


class StopService:
    """Service layer for Stop business logic."""

    @staticmethod
    def get_trip_or_404(trip_id: int, db: Session) -> TripModel:
        """Get trip or raise 404."""
        trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip with ID {trip_id} not found"
            )
        return trip

    @staticmethod
    def get_stop_or_404(trip_id: int, stop_id: int, db: Session) -> StopModel:
        """Get stop or raise 404."""
        stop = db.query(StopModel).filter(
            StopModel.id == stop_id,
            StopModel.trip_id == trip_id
        ).first()
        if not stop:
            raise HTTPException(
                status_code=404,
                detail=f"Stop with ID {stop_id} not found in trip {trip_id}"
            )
        return stop

    @staticmethod
    def validate_dates_within_trip(
        start_date: date,
        end_date: date,
        trip: TripModel
    ) -> None:
        """Validate that stop dates are within trip dates."""
        if start_date < trip.start_date or end_date > trip.end_date:
            raise HTTPException(
                status_code=400,
                detail=f"Stop dates must be within trip dates ({trip.start_date} to {trip.end_date})"
            )

    @staticmethod
    def check_date_overlap(
        start_date: date,
        end_date: date,
        trip_id: int,
        db: Session,
        exclude_stop_id: Optional[int] = None
    ) -> None:
        """
        Check if stop dates overlap with existing stops by more than 1 day.

        Allows:
        - Same-day transition (Stop A ends on day X, Stop B starts on day X)
        - One-day overlap (for travel days)

        Raises HTTPException if overlap > 1 day.
        """
        query = db.query(StopModel).filter(StopModel.trip_id == trip_id)
        if exclude_stop_id:
            query = query.filter(StopModel.id != exclude_stop_id)

        existing_stops = query.all()

        for stop in existing_stops:
            overlap_start = max(start_date, stop.start_date)
            overlap_end = min(end_date, stop.end_date)

            if overlap_start <= overlap_end:
                overlap_days = (overlap_end - overlap_start).days + 1

                if overlap_days > 1:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Stop dates overlap with '{stop.name}' by {overlap_days} days "
                            f"({overlap_start} to {overlap_end}). "
                            f"Maximum allowed overlap is 1 day for transition."
                        )
                    )

    @staticmethod
    def validate_order_index_unique(
        order_index: int,
        trip_id: int,
        db: Session,
        exclude_stop_id: Optional[int] = None
    ) -> None:
        """Validate that order_index is unique within the trip."""
        query = db.query(StopModel).filter(
            StopModel.trip_id == trip_id,
            StopModel.order_index == order_index
        )
        if exclude_stop_id:
            query = query.filter(StopModel.id != exclude_stop_id)

        existing_stop = query.first()
        if existing_stop:
            raise HTTPException(
                status_code=400,
                detail=f"Stop with order_index {order_index} already exists in this trip"
            )

    @staticmethod
    def validate_coordinates_with_country(
        latitude: Optional[float],
        longitude: Optional[float],
        country: Optional[str]
    ) -> None:
        """
        Validate that coordinates match the country.
        Raises HTTPException(422) if validation fails.
        """
        try:
            validate_realistic_coordinates(latitude, longitude, country)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    @staticmethod
    def create_stop(
        trip_id: int,
        stop_data: StopCreate,
        db: Session
    ) -> StopModel:
        """
        Create a new stop with full validation.

        Validates:
        - Trip exists
        - Stop dates are within trip dates
        - No date overlaps (allows 1-day overlap)
        - order_index is unique
        - Coordinates match country (done by Pydantic in StopCreate)
        """
        # Verify trip exists
        trip = StopService.get_trip_or_404(trip_id, db)

        # Validate dates within trip
        StopService.validate_dates_within_trip(
            stop_data.start_date,
            stop_data.end_date,
            trip
        )

        # Check for date overlaps
        StopService.check_date_overlap(
            stop_data.start_date,
            stop_data.end_date,
            trip_id,
            db
        )

        # Check order_index uniqueness
        StopService.validate_order_index_unique(
            stop_data.order_index,
            trip_id,
            db
        )

        # Create the stop
        new_stop = StopModel(**stop_data.model_dump(), trip_id=trip_id)
        db.add(new_stop)
        db.commit()
        db.refresh(new_stop)
        return new_stop

    @staticmethod
    def get_all_stops(trip_id: int, db: Session) -> List[StopModel]:
        """Get all stops for a trip, ordered by order_index."""
        # Verify trip exists
        StopService.get_trip_or_404(trip_id, db)

        stops = db.query(StopModel).filter(
            StopModel.trip_id == trip_id
        ).order_by(StopModel.order_index).all()

        return stops

    @staticmethod
    def update_stop(
        trip_id: int,
        stop_id: int,
        stop_update: StopUpdate,
        db: Session
    ) -> StopModel:
        """
        Update a stop with full validation.

        Validates:
        - Trip exists
        - Stop exists
        - If dates updated: within trip dates, no overlaps
        - If order_index updated: unique
        - If country/coordinates updated: they match each other
        """
        # Verify trip exists
        StopService.get_trip_or_404(trip_id, db)

        # Get the stop
        stop = StopService.get_stop_or_404(trip_id, stop_id, db)
        trip = stop.trip

        # Get update data (only provided fields)
        update_data = stop_update.model_dump(exclude_unset=True)

        # Determine final values (new if provided, otherwise existing)
        final_start = update_data.get("start_date", stop.start_date)
        final_end = update_data.get("end_date", stop.end_date)
        final_lat = update_data.get("latitude", stop.latitude)
        final_lon = update_data.get("longitude", stop.longitude)
        final_country = update_data.get("country", stop.country)

        # Validate dates within trip
        StopService.validate_dates_within_trip(final_start, final_end, trip)

        # Check for date overlaps if dates are being updated
        if "start_date" in update_data or "end_date" in update_data:
            StopService.check_date_overlap(
                final_start,
                final_end,
                trip_id,
                db,
                exclude_stop_id=stop_id
            )

        # Validate order_index if being updated
        if "order_index" in update_data:
            StopService.validate_order_index_unique(
                update_data["order_index"],
                trip_id,
                db,
                exclude_stop_id=stop_id
            )

        # Validate coordinates with country
        # This handles both cases:
        # 1. Updating country but keeping existing coordinates
        # 2. Updating coordinates but keeping existing country
        # 3. Updating both
        if "country" in update_data or "latitude" in update_data or "longitude" in update_data:
            StopService.validate_coordinates_with_country(
                final_lat,
                final_lon,
                final_country
            )

        # Apply updates
        for key, value in update_data.items():
            setattr(stop, key, value)

        db.commit()
        db.refresh(stop)
        return stop

    @staticmethod
    def delete_stop(trip_id: int, stop_id: int, db: Session) -> StopModel:
        """Delete a stop from a trip."""
        stop = StopService.get_stop_or_404(trip_id, stop_id, db)
        db.delete(stop)
        db.commit()
        return stop

    @staticmethod
    def reorder_stops(
        trip_id: int,
        stop_ids: List[int],
        db: Session
    ) -> List[StopModel]:
        """
        Reorder stops in a trip.

        Validates:
        - Trip exists
        - All provided stop IDs exist in this trip
        - No missing or extra IDs

        Uses two-phase update to avoid unique constraint violations.
        """
        # Verify trip exists
        StopService.get_trip_or_404(trip_id, db)

        # Get all stops for this trip
        stops = db.query(StopModel).filter(StopModel.trip_id == trip_id).all()
        stop_ids_in_db = {stop.id for stop in stops}

        # Validate that all provided stop IDs exist in this trip
        provided_ids = set(stop_ids)
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

        # Create stop map for easy access
        stop_map = {stop.id: stop for stop in stops}

        # Phase 1: Set temporary negative indices to avoid constraint violations
        for temp_index, stop_id in enumerate(stop_ids):
            stop_map[stop_id].order_index = -(temp_index + 1)
        db.flush()

        # Phase 2: Set final positive indices
        for new_index, stop_id in enumerate(stop_ids):
            stop_map[stop_id].order_index = new_index

        db.commit()

        # Return updated stops in new order
        updated_stops = db.query(StopModel).filter(
            StopModel.trip_id == trip_id
        ).order_by(StopModel.order_index).all()

        return updated_stops
