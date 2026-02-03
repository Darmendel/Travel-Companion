# app/repositories/trip_repository.py
"""
Trip Repository

Handles all database operations for Trip model.
Separates data access logic from business logic in TripService.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.models.trip import Trip as TripModel
from app.repositories.base_repository import BaseRepository


class TripRepository(BaseRepository[TripModel]):
    """Repository for Trip model with trip-specific queries."""

    def __init__(self, db: AsyncSession):
        """Initialize trip repository."""
        super().__init__(TripModel, db)

    async def get_by_user_id(self, user_id: int) -> List[TripModel]:
        """
        Get all trips for a specific user.

        SQL: SELECT * FROM trips WHERE user_id = ?;

        Args:
            user_id: ID of the user

        Returns:
            List of trips belonging to the user
        """
        return await self.get_by_filter(user_id=user_id)

    async def get_by_id_and_user(
            self,
            trip_id: int,
            user_id: int
    ) -> Optional[TripModel]:
        """
        Get a trip by ID that belongs to a specific user.

        SQL: SELECT * FROM trips WHERE id = ? AND user_id = ?;

        Args:
            trip_id: ID of the trip
            user_id: ID of the user

        Returns:
            Trip if found and belongs to user, None otherwise
        """
        return await self.get_one_by_filter(id=trip_id, user_id=user_id)

    async def create_for_user(
            self,
            user_id: int,
            title: str,
            start_date: date,
            end_date: date
    ) -> TripModel:
        """
        Create a new trip for a user.

        SQL: INSERT INTO trips (user_id, title, start_date, end_date)
             VALUES (?, ?, ?, ?);

        Args:
            user_id: ID of the user
            title: Trip title
            start_date: Trip start date
            end_date: Trip end date

        Returns:
            Created trip instance
        """
        return await self.create(
            user_id=user_id,
            title=title,
            start_date=start_date,
            end_date=end_date
        )

    async def update_trip(
            self,
            trip_id: int,
            **update_data
    ) -> Optional[TripModel]:
        """
        Update a trip by ID.

        SQL: UPDATE trips SET ... WHERE id = ?;

        Args:
            trip_id: ID of the trip
            **update_data: Fields to update

        Returns:
            Updated trip or None if not found
        """
        return await self.update(trip_id, **update_data)

    async def delete_by_id(self, trip_id: int) -> bool:
        """
        Delete a trip by ID.

        SQL: DELETE FROM trips WHERE id = ?;

        Note: This will cascade delete all stops due to foreign key constraint.

        Args:
            trip_id: ID of the trip

        Returns:
            True if deleted, False if not found
        """
        return await self.delete(trip_id)

    async def get_trips_by_date_range(
            self,
            user_id: int,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> List[TripModel]:
        """
        Get trips within a date range for a user.

        Args:
            user_id: ID of the user
            start_date: Optional minimum start date
            end_date: Optional maximum end date

        Returns:
            List of matching trips
        """
        query = select(self.model).filter(self.model.user_id == user_id)

        if start_date:
            query = query.filter(self.model.start_date >= start_date)
        if end_date:
            query = query.filter(self.model.end_date <= end_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_user_trips(self, user_id: int) -> int:
        """
        Count total trips for a user.

        Args:
            user_id: ID of the user

        Returns:
            Number of trips
        """
        return await self.count(user_id=user_id)