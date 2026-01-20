# app/services/trip_service.py
"""
Service layer for Trip business logic.

This service handles all trip-related operations including:
- CRUD operations (Create, Read, Update, Delete)
- Validation of trip data
- Date range validations
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.models.trip import Trip as TripModel
from app.schemas.trip import TripCreate, TripUpdate


class TripService:
    """Service layer for Trip business logic."""

    @staticmethod
    def get_trip_or_404(trip_id: int, db: Session) -> TripModel:
        """
        Get trip by ID or raise 404 if not found.

        Args:
            trip_id: The ID of the trip to retrieve
            db: Database session

        Returns:
            TripModel: The requested trip

        Raises:
            HTTPException: 404 if trip not found
        """
        trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip with ID {trip_id} not found"
            )
        return trip

    @staticmethod
    def get_all_trips(db: Session) -> List[TripModel]:
        """
        Get all trips from the database.

        Equivalent to: SELECT * FROM trips;

        Args:
            db: Database session

        Returns:
            List[TripModel]: List of all trips
        """
        trips = db.query(TripModel).all()  # SELECT * FROM trips;
        return trips

    @staticmethod
    def create_trip(trip_data: TripCreate, db: Session) -> TripModel:
        """
        Create a new trip.

        Equivalent to: INSERT INTO trips (...) VALUES (...);

        The validation is already done by Pydantic in TripCreate schema:
        - title is not empty
        - start_date is not in the past
        - end_date is after start_date

        Args:
            trip_data: Validated trip data from Pydantic
            db: Database session

        Returns:
            TripModel: The newly created trip with generated ID
        """
        # Convert Pydantic model to SQLAlchemy model
        # trip_data.model_dump() returns a dict: {"title": ..., "start_date": ..., ...}
        # **trip_data.model_dump() unpacks that dict as keyword arguments
        new_trip = TripModel(**trip_data.model_dump())

        db.add(new_trip)  # Stage the trip for insertion
        db.commit()  # Save to database
        db.refresh(new_trip)  # Get the newly generated ID and updated state

        return new_trip

    @staticmethod
    def update_trip(
            trip_id: int,
            trip_update: TripUpdate,
            db: Session
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
            db: Database session

        Returns:
            TripModel: The updated trip

        Raises:
            HTTPException: 404 if trip not found, 400 if dates invalid
        """
        # Get the trip or raise 404
        trip = TripService.get_trip_or_404(trip_id, db)

        # Get only the fields that were provided in the request
        # exclude_unset=True means: only include fields the user sent
        update_data = trip_update.model_dump(exclude_unset=True)

        # Validate dates if they're being updated
        # We need to check the combination of new and existing values
        new_start = update_data.get("start_date", trip.start_date)
        new_end = update_data.get("end_date", trip.end_date)

        TripService.validate_trip_date_range(new_start, new_end)

        # Apply the updates
        # setattr(object, attribute_name, value) sets object.attribute_name = value
        # We use this because we don't know which fields were provided
        for key, value in update_data.items():
            setattr(trip, key, value)

        db.commit()  # Save changes to database
        db.refresh(trip)  # Refresh to get any DB-side changes

        return trip

    @staticmethod
    def delete_trip(trip_id: int, db: Session) -> TripModel:
        """
        Delete a trip by ID.

        Equivalent to: DELETE FROM trips WHERE id = ...;

        Note: This will also delete all stops in the trip due to
        CASCADE delete configured in the Trip model.

        Args:
            trip_id: ID of the trip to delete
            db: Database session

        Returns:
            TripModel: The deleted trip (before deletion)

        Raises:
            HTTPException: 404 if trip not found
        """
        # Get the trip or raise 404
        trip = TripService.get_trip_or_404(trip_id, db)

        db.delete(trip)  # Mark for deletion
        db.commit()  # Execute the DELETE

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
