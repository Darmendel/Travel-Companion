# app/repositories/user_repository.py
"""
User Repository

Handles all database operations for User model.
Includes user authentication and profile management queries.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User as UserModel
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    """Repository for User model with user-specific queries."""

    def __init__(self, db: AsyncSession):
        """Initialize user repository."""
        super().__init__(UserModel, db)

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get user by email address.

        SQL: SELECT * FROM users WHERE email = ?;

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        return await self.get_one_by_filter(email=email)

    async def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if an email is already registered.

        Args:
            email: Email to check
            exclude_user_id: Optional user ID to exclude (for updates)

        Returns:
            True if email exists, False otherwise
        """
        query = select(self.model).filter(self.model.email == email)

        if exclude_user_id:
            query = query.filter(self.model.id != exclude_user_id)

        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def create_user(
            self,
            email: str,
            hashed_password: str,
            full_name: Optional[str] = None,
            is_active: bool = True,
            is_superuser: bool = False
    ) -> UserModel:
        """
        Create a new user.

        SQL: INSERT INTO users (...) VALUES (...);

        Args:
            email: User's email
            hashed_password: Hashed password
            full_name: Optional full name
            is_active: Whether user is active (default: True)
            is_superuser: Whether user is superuser (default: False)

        Returns:
            Created user instance
        """
        return await self.create(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser
        )

    async def update_user(
            self,
            user_id: int,
            **update_data
    ) -> Optional[UserModel]:
        """
        Update user information.

        SQL: UPDATE users SET ... WHERE id = ?;

        Args:
            user_id: ID of the user
            **update_data: Fields to update

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, **update_data)

    async def update_password(
            self,
            user_id: int,
            hashed_password: str
    ) -> Optional[UserModel]:
        """
        Update user's password.

        Args:
            user_id: ID of the user
            hashed_password: New hashed password

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, hashed_password=hashed_password)

    async def get_active_users(self) -> list[UserModel]:
        """
        Get all active users.

        SQL: SELECT * FROM users WHERE is_active = TRUE;

        Returns:
            List of active users
        """
        return await self.get_by_filter(is_active=True)

    async def get_superusers(self) -> list[UserModel]:
        """
        Get all superusers.

        SQL: SELECT * FROM users WHERE is_superuser = TRUE;

        Returns:
            List of superusers
        """
        return await self.get_by_filter(is_superuser=True)

    async def deactivate_user(self, user_id: int) -> Optional[UserModel]:
        """
        Deactivate a user account.

        Args:
            user_id: ID of the user

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, is_active=False)

    async def activate_user(self, user_id: int) -> Optional[UserModel]:
        """
        Activate a user account.

        Args:
            user_id: ID of the user

        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, is_active=True)

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user by ID.

        SQL: DELETE FROM users WHERE id = ?;

        Note: This will cascade delete all user's trips and stops.

        Args:
            user_id: ID of the user

        Returns:
            True if deleted, False if not found
        """
        return await self.delete(user_id)

    async def count_active_users(self) -> int:
        """
        Count number of active users.

        Returns:
            Number of active users
        """
        return await self.count(is_active=True)