# app/repositories/stop_repository.py
"""
Stop Repository

Handles all database operations for Stop model.
Includes stop-specific queries like ordering, overlaps, and filtering.
"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date

from app.models.stop import Stop as StopModel
from app.repositories.base_repository import BaseRepository


class StopRepository(BaseRepository[StopModel]):
    """Repository for Stop model with stop-specific queries."""

    def __init__(self, db: AsyncSession):
        """Initialize stop repository."""
        super().__init__(StopModel, db)

    async def get_by_trip_id(
            self,
            trip_id: int,
            order_by_index: bool = True
    ) -> List[StopModel]:
        """
        Get all stops for a specific trip.

        SQL: SELECT * FROM stops WHERE trip_id = ? ORDER BY order_index;

        Args:
            trip_id: ID of the trip
            order_by_index: Whether to order by order_index (default: True)

        Returns:
            List of stops in the trip
        """
        query = select(self.model).filter(self.model.trip_id == trip_id)

        if order_by_index:
            query = query.order_by(self.model.order_index)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id_and_trip(
            self,
            stop_id: int,
            trip_id: int
    ) -> Optional[StopModel]:
        """
        Get a stop by ID that belongs to a specific trip.

        SQL: SELECT * FROM stops WHERE id = ? AND trip_id = ?;

        Args:
            stop_id: ID of the stop
            trip_id: ID of the trip

        Returns:
            Stop if found and belongs to trip, None otherwise
        """
        return await self.get_one_by_filter(id=stop_id, trip_id=trip_id)

    async def get_by_order_index(
            self,
            trip_id: int,
            order_index: int
    ) -> Optional[StopModel]:
        """
        Get a stop by order_index within a trip.

        SQL: SELECT * FROM stops WHERE trip_id = ? AND order_index = ?;

        Args:
            trip_id: ID of the trip
            order_index: Order index of the stop

        Returns:
            Stop if found, None otherwise
        """
        return await self.get_one_by_filter(
            trip_id=trip_id,
            order_index=order_index
        )

    async def create_stop(
            self,
            trip_id: int,
            name: str,
            start_date: date,
            end_date: date,
            order_index: int,
            country: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            notes: Optional[str] = None
    ) -> StopModel:
        """
        Create a new stop.

        SQL: INSERT INTO stops (...) VALUES (...);

        Args:
            trip_id: ID of the trip
            name: Stop name
            start_date: Stop start date
            end_date: Stop end date
            order_index: Order position in trip
            country: Optional country name
            latitude: Optional latitude
            longitude: Optional longitude
            notes: Optional notes

        Returns:
            Created stop instance
        """
        return await self.create(
            trip_id=trip_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            order_index=order_index,
            country=country,
            latitude=latitude,
            longitude=longitude,
            notes=notes
        )

    async def update_stop(
            self,
            stop_id: int,
            **update_data
    ) -> Optional[StopModel]:
        """
        Update a stop by ID.

        SQL: UPDATE stops SET ... WHERE id = ?;

        Args:
            stop_id: ID of the stop
            **update_data: Fields to update

        Returns:
            Updated stop or None if not found
        """
        return await self.update(stop_id, **update_data)

    async def delete_by_id(self, stop_id: int) -> bool:
        """
        Delete a stop by ID.

        SQL: DELETE FROM stops WHERE id = ?;

        Args:
            stop_id: ID of the stop

        Returns:
            True if deleted, False if not found
        """
        return await self.delete(stop_id)

    async def get_stops_with_date_overlap(
            self,
            trip_id: int,
            start_date: date,
            end_date: date,
            exclude_stop_id: Optional[int] = None
    ) -> List[Tuple[date, date, str]]:
        """
        Get stops that overlap with given date range.

        Returns simplified tuples for validation, not full models.

        Args:
            trip_id: ID of the trip
            start_date: Start date to check
            end_date: End date to check
            exclude_stop_id: Optional stop ID to exclude from check

        Returns:
            List of tuples: (start_date, end_date, name)
        """
        query = select(
            self.model.start_date,
            self.model.end_date,
            self.model.name
        ).filter(self.model.trip_id == trip_id)

        if exclude_stop_id:
            query = query.filter(self.model.id != exclude_stop_id)

        # Check for any overlap
        # Stops overlap if: start_date <= other_end_date AND end_date >= other_start_date
        query = query.filter(
            and_(
                self.model.start_date <= end_date,
                self.model.end_date >= start_date
            )
        )

        result = await self.db.execute(query)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def order_index_exists(
            self,
            trip_id: int,
            order_index: int,
            exclude_stop_id: Optional[int] = None
    ) -> bool:
        """
        Check if an order_index already exists in a trip.

        Args:
            trip_id: ID of the trip
            order_index: Order index to check
            exclude_stop_id: Optional stop ID to exclude from check

        Returns:
            True if order_index exists, False otherwise
        """
        query = select(self.model).filter(
            and_(
                self.model.trip_id == trip_id,
                self.model.order_index == order_index
            )
        )

        if exclude_stop_id:
            query = query.filter(self.model.id != exclude_stop_id)

        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def get_max_order_index(self, trip_id: int) -> Optional[int]:
        """
        Get the maximum order_index in a trip.

        Args:
            trip_id: ID of the trip

        Returns:
            Maximum order_index or None if no stops
        """
        stops = await self.get_by_trip_id(trip_id, order_by_index=False)
        if not stops:
            return None
        return max(stop.order_index for stop in stops)

    async def bulk_update_order_indices(
            self,
            stop_id_to_order: dict[int, int]
    ) -> None:
        """
        Update order_indices for multiple stops in bulk.

        Used for reordering stops efficiently.

        Args:
            stop_id_to_order: Dictionary mapping stop_id to new order_index
        """
        for stop_id, new_order in stop_id_to_order.items():
            stop = await self.get_by_id(stop_id)
            if stop:
                stop.order_index = new_order

        await self.db.flush()

    async def get_stops_by_ids(
            self,
            stop_ids: List[int],
            trip_id: Optional[int] = None
    ) -> List[StopModel]:
        """
        Get multiple stops by their IDs.

        Args:
            stop_ids: List of stop IDs
            trip_id: Optional trip ID to filter by

        Returns:
            List of stops
        """
        query = select(self.model).filter(self.model.id.in_(stop_ids))

        if trip_id is not None:
            query = query.filter(self.model.trip_id == trip_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_stops_in_trip(self, trip_id: int) -> int:
        """
        Count number of stops in a trip.

        Args:
            trip_id: ID of the trip

        Returns:
            Number of stops
        """
        return await self.count(trip_id=trip_id)