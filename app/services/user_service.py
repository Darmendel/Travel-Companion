# app/services/user_service.py
"""
User Service Layer

Handles user authentication, registration, and management.
Uses UserRepository for all database access.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate
from app.auth.jwt import get_password_hash, verify_password, create_access_token
from app.repositories.user_repository import UserRepository


class UserService:
    """Service layer for user operations."""

    @staticmethod
    async def create_user(user_data: UserCreate, db: AsyncSession) -> UserModel:
        """
        Create a new user account.

        Validates:
        - Email is not already registered
        - Password meets requirements (handled by Pydantic)

        Args:
            user_data: Validated user registration data
            db: Database session

        Returns:
            Created user model

        Raises:
            HTTPException: 400 if email already exists
        """
        repo = UserRepository(db)

        # Check if email already exists
        if await repo.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user using repository
        return await repo.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )

    @staticmethod
    async def authenticate_user(
            email: str,
            password: str,
            db: AsyncSession
    ) -> Optional[UserModel]:
        """
        Authenticate a user by email and password.

        Args:
            email: User's email
            password: Plain text password
            db: Database session

        Returns:
            User model if credentials are valid, None otherwise
        """
        repo = UserRepository(db)

        # Find user by email
        user = await repo.get_by_email(email)

        if not user:
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    async def get_user_by_id(user_id: int, db: AsyncSession) -> UserModel:
        """
        Get user by ID.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            User model

        Raises:
            HTTPException: 404 if user not found
        """
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        return user

    @staticmethod
    async def get_user_by_email(email: str, db: AsyncSession) -> Optional[UserModel]:
        """
        Get user by email.

        Args:
            email: User email
            db: Database session

        Returns:
            User model if found, None otherwise
        """
        repo = UserRepository(db)
        return await repo.get_by_email(email)

    @staticmethod
    async def update_user(
            user_id: int,
            user_update: UserUpdate,
            db: AsyncSession
    ) -> UserModel:
        """
        Update user information.

        Args:
            user_id: User ID
            user_update: Updated user data
            db: Database session

        Returns:
            Updated user model

        Raises:
            HTTPException: 404 if user not found, 400 if email already taken
        """
        repo = UserRepository(db)

        # Check user exists
        user = await UserService.get_user_by_id(user_id, db)

        update_data = user_update.model_dump(exclude_unset=True)

        # Check if email is being updated and is already taken
        if "email" in update_data:
            if await repo.email_exists(update_data["email"], exclude_user_id=user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )

        # Hash password if being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        # Update using repository
        updated_user = await repo.update_user(user_id, **update_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        return updated_user

    @staticmethod
    def create_user_token(user: UserModel) -> str:
        """
        Create JWT access token for user.

        Args:
            user: User model

        Returns:
            JWT token string
        """
        token_data = {
            "user_id": user.id,
            "email": user.email
        }
        return create_access_token(token_data)