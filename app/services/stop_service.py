# app/services/stop_service.py
"""
Async Service layer for Stop business logic.

This service handles all stop-related operations including:
- CRUD operations for stops
- Validation orchestration (calls pure validators)
- Database access
- Date overlap checking
- Reordering stops within a trip

The service layer is responsible for:
1. Database access
2. Orchestrating validations (calling validators)
3. Converting ValueError to HTTPException
4. Business logic that requires DB state
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date

from app.models.stop import Stop as StopModel
from app.models.trip import Trip as TripModel
from app.schemas.stop import StopCreate, StopUpdate
from app.validators.stop_validators import (
    validate_realistic_coordinates,
    validate_date_overlap,
    validate_dates_within_range
)
from app.services.trip_service import TripService


class StopService:
    """Async service layer for Stop business logic."""

    @staticmethod
    async def get_stop(trip_id: int, stop_id: int, db: AsyncSession) -> StopModel:
        """Get stop or raise 404."""
        result = await db.execute(
            select(StopModel).filter(
                StopModel.id == stop_id,
                StopModel.trip_id == trip_id
            )
        )
        stop = result.scalar_one_or_none()

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
        """
        Validate that stop dates are within trip dates.

        Raises:
            HTTPException: 400 if dates are outside trip range
        """
        try:
            validate_dates_within_range(
                start_date, end_date,
                trip.start_date, trip.end_date,
                range_name="trip"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def check_date_overlap(
            start_date: date,
            end_date: date,
            trip_id: int,
            db: AsyncSession,
            exclude_stop_id: Optional[int] = None
    ) -> None:
        """
        Check if stop dates overlap with existing stops by more than 1 day.

        Allows:
        - Same-day transition (Stop A ends on day X, Stop B starts on day X)
        - One-day overlap (for travel days)

        Args:
            start_date: Stop start date
            end_date: Stop end date
            trip_id: ID of the trip
            db: Async database session
            exclude_stop_id: Optional stop ID to exclude from check (for updates)

        Raises:
            HTTPException: 400 if overlap > 1 day
        """
        # Fetch existing stops from database
        query = select(StopModel).filter(StopModel.trip_id == trip_id)
        if exclude_stop_id:
            query = query.filter(StopModel.id != exclude_stop_id)

        result = await db.execute(query)
        existing_stops = result.scalars().all()

        # Transform to simple data structure (tuples)
        existing_dates = [
            (stop.start_date, stop.end_date, stop.name)
            for stop in existing_stops
        ]

        # Call pure validator
        try:
            validate_date_overlap(start_date, end_date, existing_dates)
        except ValueError as e:
            # Convert ValueError to HTTPException
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def validate_order_index_unique(
            order_index: int,
            trip_id: int,
            db: AsyncSession,
            exclude_stop_id: Optional[int] = None
    ) -> None:
        """
        Validate that order_index is unique within the trip.

        Args:
            order_index: Order index to validate
            trip_id: ID of the trip
            db: Async database session
            exclude_stop_id: Optional stop ID to exclude from check (for updates)

        Raises:
            HTTPException: 400 if order_index already exists
        """
        query = select(StopModel).filter(
            StopModel.trip_id == trip_id,
            StopModel.order_index == order_index
        )
        if exclude_stop_id:
            query = query.filter(StopModel.id != exclude_stop_id)

        result = await db.execute(query)
        existing_stop = result.scalar_one_or_none()

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

        Raises:
            HTTPException: 422 if validation fails
        """
        try:
            validate_realistic_coordinates(latitude, longitude, country)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    @staticmethod
    async def create_stop(
            trip_id: int,
            stop_data: StopCreate,
            db: AsyncSession
    ) -> StopModel:
        """
        Create a new stop with full validation.

        Validates:
        - Trip exists (via TripService)
        - Stop dates are within trip dates
        - No date overlaps (allows 1-day overlap)
        - order_index is unique
        - Coordinates match country (done by Pydantic in StopCreate)

        Args:
            trip_id: ID of the trip
            stop_data: Validated stop data from Pydantic
            db: Async database session

        Returns:
            StopModel: The newly created stop

        Raises:
            HTTPException: 400/404/422 for various validation failures
        """
        # Verify trip exists using TripService
        trip = await TripService.get_trip(trip_id, db)

        # Validate dates within trip
        StopService.validate_dates_within_trip(
            stop_data.start_date,
            stop_data.end_date,
            trip
        )

        # Check for date overlaps
        await StopService.check_date_overlap(
            stop_data.start_date,
            stop_data.end_date,
            trip_id,
            db
        )

        # Check order_index uniqueness
        await StopService.validate_order_index_unique(
            stop_data.order_index,
            trip_id,
            db
        )

        # Create the stop
        new_stop = StopModel(**stop_data.model_dump(), trip_id=trip_id)
        db.add(new_stop)
        await db.commit()
        await db.refresh(new_stop)
        return new_stop

    @staticmethod
    async def get_all_stops(trip_id: int, db: AsyncSession) -> List[StopModel]:
        """
        Get all stops for a trip, ordered by order_index.

        Validates:
        - Trip exists (via TripService)

        Args:
            trip_id: ID of the trip
            db: Async database session

        Returns:
            List[StopModel]: List of stops ordered by order_index

        Raises:
            HTTPException: 404 if trip not found
        """
        # Verify trip exists using TripService
        await TripService.get_trip(trip_id, db)

        result = await db.execute(
            select(StopModel)
            .filter(StopModel.trip_id == trip_id)
            .order_by(StopModel.order_index)
        )
        stops = result.scalars().all()

        return list(stops)

    @staticmethod
    async def update_stop(
            trip_id: int,
            stop_id: int,
            stop_update: StopUpdate,
            db: AsyncSession
    ) -> StopModel:
        """
        Update a stop with full validation.

        Validates:
        - Trip exists (via TripService)
        - Stop exists
        - If dates updated: within trip dates, no overlaps
        - If order_index updated: unique
        - If country/coordinates updated: they match each other

        Args:
            trip_id: ID of the trip
            stop_id: ID of the stop
            stop_update: Partial update data
            db: Async database session

        Returns:
            StopModel: The updated stop

        Raises:
            HTTPException: 400/404/422 for various validation failures
        """
        # Verify trip exists using TripService
        trip = await TripService.get_trip(trip_id, db)

        # Get the stop
        stop = await StopService.get_stop(trip_id, stop_id, db)

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
            await StopService.check_date_overlap(
                final_start,
                final_end,
                trip_id,
                db,
                exclude_stop_id=stop_id
            )

        # Validate order_index if being updated
        if "order_index" in update_data:
            await StopService.validate_order_index_unique(
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

        await db.commit()
        await db.refresh(stop)
        return stop

    @staticmethod
    async def delete_stop(trip_id: int, stop_id: int, db: AsyncSession) -> StopModel:
        """
        Delete a stop from a trip.

        Args:
            trip_id: ID of the trip
            stop_id: ID of the stop
            db: Async database session

        Returns:
            StopModel: The deleted stop (before deletion)

        Raises:
            HTTPException: 404 if stop not found
        """
        stop = await StopService.get_stop(trip_id, stop_id, db)
        await db.delete(stop)
        await db.commit()
        return stop

    @staticmethod
    async def reorder_stops(
            trip_id: int,
            stop_ids: List[int],
            db: AsyncSession
    ) -> List[StopModel]:
        """
        Reorder stops in a trip.

        Validates:
        - Trip exists (via TripService)
        - All provided stop IDs exist in this trip
        - No missing or extra IDs

        Uses two-phase update to avoid unique constraint violations.

        Args:
            trip_id: ID of the trip
            stop_ids: List of stop IDs in desired order
            db: Async database session

        Returns:
            List[StopModel]: Updated stops in new order

        Raises:
            HTTPException: 400/404 for validation failures
        """
        # Verify trip exists using TripService
        await TripService.get_trip(trip_id, db)

        # Get all stops for this trip
        result = await db.execute(
            select(StopModel).filter(StopModel.trip_id == trip_id)
        )
        stops = result.scalars().all()
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
        await db.flush()

        # Phase 2: Set final positive indices
        for new_index, stop_id in enumerate(stop_ids):
            stop_map[stop_id].order_index = new_index

        await db.commit()

        # Return updated stops in new order
        result = await db.execute(
            select(StopModel)
            .filter(StopModel.trip_id == trip_id)
            .order_by(StopModel.order_index)
        )
        updated_stops = result.scalars().all()

        return list(updated_stops)