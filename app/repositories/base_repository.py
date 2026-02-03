# app/repositories/base_repository.py
"""
Base Repository Pattern

Provides common database operations for all models.
This follows the Repository Pattern to separate data access logic.
"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql import Select

from app.db.session import Base

# Generic type for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    All model-specific repositories should inherit from this class.
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class (e.g., Trip, Stop, User)
            db: Async database session
        """
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).filter(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[ModelType]:
        """
        Get all records.

        Returns:
            List of all model instances
        """
        result = await self.db.execute(select(self.model))
        return list(result.scalars().all())

    async def get_by_filter(self, **filters) -> List[ModelType]:
        """
        Get records by filter conditions.

        Args:
            **filters: Column name and value pairs

        Example:
            repo.get_by_filter(user_id=1, is_active=True)

        Returns:
            List of matching model instances
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_one_by_filter(self, **filters) -> Optional[ModelType]:
        """
        Get a single record by filter conditions.

        Args:
            **filters: Column name and value pairs

        Returns:
            First matching model instance or None
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **data) -> ModelType:
        """
        Create a new record.

        Args:
            **data: Column name and value pairs

        Returns:
            Created model instance with ID
        """
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: int, **data) -> Optional[ModelType]:
        """
        Update a record by ID.

        Args:
            id: Primary key value
            **data: Column name and value pairs to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.db.delete(instance)
        await self.db.commit()
        return True

    async def exists(self, **filters) -> bool:
        """
        Check if a record exists by filter conditions.

        Args:
            **filters: Column name and value pairs

        Returns:
            True if at least one record exists, False otherwise
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def count(self, **filters) -> int:
        """
        Count records by filter conditions.

        Args:
            **filters: Column name and value pairs (optional)

        Returns:
            Number of matching records
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return len(list(result.scalars().all()))

    def _apply_filters(self, query: Select, **filters) -> Select:
        """
        Helper method to apply filters to a query.

        Args:
            query: SQLAlchemy select query
            **filters: Column name and value pairs

        Returns:
            Query with filters applied
        """
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query