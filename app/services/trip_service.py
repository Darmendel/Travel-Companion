# app/services/trip_service.py
"""
Async Service layer for Trip business logic.

This service handles all trip-related operations including:
- CRUD operations (Create, Read, Update, Delete)
- Validation of trip data
- Date range validations
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import date

from app.models.trip import Trip as TripModel
from app.schemas.trip import TripCreate, TripUpdate


class TripService:
    """Async service layer for Trip business logic."""

    @staticmethod
    async def get_trip(trip_id: int, db: AsyncSession) -> TripModel:
        """Get trip by ID or raise 404 if not found."""
        result = await db.execute(
            select(TripModel).filter(TripModel.id == trip_id)
        )
        trip = result.scalar_one_or_none()

        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip with ID {trip_id} not found"
            )
        return trip

    @staticmethod
    async def get_all_trips(db: AsyncSession) -> List[TripModel]:
        """
        Get all trips from the database.

        Equivalent to: SELECT * FROM trips;

        Args:
            db: Async database session

        Returns:
            List[TripModel]: List of all trips
        """
        result = await db.execute(select(TripModel))
        trips = result.scalars().all()
        return list(trips)

    @staticmethod
    async def create_trip(trip_data: TripCreate, db: AsyncSession) -> TripModel:
        """
        Create a new trip.

        Equivalent to: INSERT INTO trips (...) VALUES (...);

        The validation is already done by Pydantic in TripCreate schema:
        - title is not empty
        - start_date is not in the past
        - end_date is after start_date

        Args:
            trip_data: Validated trip data from Pydantic
            db: Async database session

        Returns:
            TripModel: The newly created trip with generated ID
        """
        # Convert Pydantic model to SQLAlchemy model
        # trip_data.model_dump() returns a dict: {"title": ..., "start_date": ..., ...}
        # **trip_data.model_dump() unpacks that dict as keyword arguments
        new_trip = TripModel(**trip_data.model_dump())

        db.add(new_trip)
        await db.commit()
        await db.refresh(new_trip)  # Get the newly generated ID and updated state

        return new_trip

    @staticmethod
    async def update_trip(
            trip_id: int,
            trip_update: TripUpdate,
            db: AsyncSession
    ) -> TripModel:
        """
        Update an existing trip.

        Equivalent to: UPDATE trips SET ... WHERE id = ...;

        Validates:
        - Trip exists
        - If dates are updated, end_date must be after start_date

        Args:
            trip_id: ID of the trip to update
            trip_update: Partial update data (only provided fields)
            db: Async database session

        Returns:
            TripModel: The updated trip

        Raises:
            HTTPException: 404 if trip not found, 400 if dates invalid
        """
        trip = await TripService.get_trip(trip_id, db)

        # Get only the fields that were provided in the request
        # exclude_unset=True means: only include fields the user sent
        update_data = trip_update.model_dump(exclude_unset=True)

        # Validate dates if they're being updated
        new_start = update_data.get("start_date", trip.start_date)
        new_end = update_data.get("end_date", trip.end_date)

        TripService.validate_trip_date_range(new_start, new_end)

        # Apply the updates
        for key, value in update_data.items():
            setattr(trip, key, value)

        await db.commit()
        await db.refresh(trip)

        return trip

    @staticmethod
    async def delete_trip(trip_id: int, db: AsyncSession) -> TripModel:
        """
        Delete a trip by ID.

        Equivalent to: DELETE FROM trips WHERE id = ...;

        Note: This will also delete all stops in the trip due to
        CASCADE delete configured in the Trip model.

        Args:
            trip_id: ID of the trip to delete
            db: Async database session

        Returns:
            TripModel: The deleted trip (before deletion)

        Raises:
            HTTPException: 404 if trip not found
        """
        trip = await TripService.get_trip(trip_id, db)

        await db.delete(trip)
        await db.commit()

        return trip

    @staticmethod
    def validate_trip_date_range(
            start_date: date,
            end_date: date
    ) -> None:
        """
        Validate that trip date range is valid.

        This is a helper method for future use cases where we might need
        additional date validations beyond what Pydantic does.

        Args:
            start_date: Trip start date
            end_date: Trip end date

        Raises:
            HTTPException: 400 if date range is invalid
        """
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail=f"Trip end date ({end_date}) must be after or equal to start date ({start_date})"
            )
