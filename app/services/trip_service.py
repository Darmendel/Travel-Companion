# app/services/trip_service.py
"""
Async Service layer for Trip business logic.

This service handles all trip-related operations including:
- CRUD operations (Create, Read, Update, Delete)
- Validation of trip data
- Date range validations
- User ownership verification

Uses TripRepository for all database access.
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from app.models.trip import Trip as TripModel
from app.schemas.trip import TripCreate, TripUpdate
from app.repositories.trip_repository import TripRepository


class TripService:
    """Async service layer for Trip business logic."""

    @staticmethod
    async def get_trip(trip_id: int, db: AsyncSession, user_id: int) -> TripModel:
        """
        Get trip by ID, ensuring it belongs to the user.

        Args:
            trip_id: ID of the trip
            db: Database session
            user_id: ID of the current user

        Returns:
            TripModel if found and belongs to user

        Raises:
            HTTPException: 404 if trip not found or doesn't belong to user
        """
        repo = TripRepository(db)
        trip = await repo.get_by_id_and_user(trip_id, user_id)

        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip with ID {trip_id} not found"
            )
        return trip

    @staticmethod
    async def get_all_trips(db: AsyncSession, user_id: int) -> List[TripModel]:
        """
        Get all trips for a specific user.

        Equivalent to: SELECT * FROM trips WHERE user_id = ?;

        Args:
            db: Async database session
            user_id: ID of the current user

        Returns:
            List[TripModel]: List of all trips belonging to the user
        """
        repo = TripRepository(db)
        return await repo.get_by_user_id(user_id)

    @staticmethod
    async def create_trip(trip_data: TripCreate, db: AsyncSession, user_id: int) -> TripModel:
        """
        Create a new trip for a user.

        Equivalent to: INSERT INTO trips (..., user_id) VALUES (..., ?);

        The validation is already done by Pydantic in TripCreate schema:
        - title is not empty
        - start_date is not in the past
        - end_date is after start_date

        Args:
            trip_data: Validated trip data from Pydantic
            db: Async database session
            user_id: ID of the current user (from JWT token)

        Returns:
            TripModel: The newly created trip with generated ID
        """
        repo = TripRepository(db)
        return await repo.create_for_user(
            user_id=user_id,
            title=trip_data.title,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date
        )

    @staticmethod
    async def update_trip(
            trip_id: int,
            trip_update: TripUpdate,
            db: AsyncSession,
            user_id: int
    ) -> TripModel:
        """
        Update an existing trip, ensuring it belongs to the user.

        Equivalent to: UPDATE trips SET ... WHERE id = ? AND user_id = ?;

        Validates:
        - Trip exists and belongs to user
        - If dates are updated, end_date must be after start_date

        Args:
            trip_id: ID of the trip to update
            trip_update: Partial update data (only provided fields)
            db: Async database session
            user_id: ID of the current user

        Returns:
            TripModel: The updated trip

        Raises:
            HTTPException: 404 if trip not found or doesn't belong to user
                          400 if dates invalid
        """
        # Verify trip exists and belongs to user
        trip = await TripService.get_trip(trip_id, db, user_id)

        # Get only the fields that were provided in the request
        update_data = trip_update.model_dump(exclude_unset=True)

        # Validate dates if they're being updated
        new_start = update_data.get("start_date", trip.start_date)
        new_end = update_data.get("end_date", trip.end_date)

        TripService.validate_trip_date_range(new_start, new_end)

        # Update using repository
        repo = TripRepository(db)
        updated_trip = await repo.update_trip(trip_id, **update_data)

        if not updated_trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip with ID {trip_id} not found"
            )

        return updated_trip

    @staticmethod
    async def delete_trip(trip_id: int, db: AsyncSession, user_id: int) -> TripModel:
        """
        Delete a trip by ID, ensuring it belongs to the user.

        Equivalent to: DELETE FROM trips WHERE id = ? AND user_id = ?;

        Note: This will also delete all stops in the trip due to
        CASCADE delete configured in the Trip model.

        Args:
            trip_id: ID of the trip to delete
            db: Async database session
            user_id: ID of the current user

        Returns:
            TripModel: The deleted trip (before deletion)

        Raises:
            HTTPException: 404 if trip not found or doesn't belong to user
        """
        # Verify trip exists and belongs to user
        trip = await TripService.get_trip(trip_id, db, user_id)

        # Delete using repository
        repo = TripRepository(db)
        await repo.delete_by_id(trip_id)

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