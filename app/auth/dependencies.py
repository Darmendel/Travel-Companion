# app/auth/dependencies.py
"""
FastAPI Dependencies for Authentication

Provides dependency functions for protecting routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.auth.jwt import verify_token

# OAuth2 scheme - tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    This is a FastAPI dependency that:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token is valid
    3. Fetches the user from database
    4. Returns the user object

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException: 401 if token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    # Extract user_id from token
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user is active.

    This is an additional layer on top of get_current_user
    for routes that explicitly need active users only.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User object if active

    Raises:
        HTTPException: 403 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


# Optional: For admin-only routes
async def get_current_superuser(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user is a superuser.

    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: User = Depends(get_current_superuser)
        ):
            # Only superusers can access this
            ...

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User object if superuser

    Raises:
        HTTPException: 403 if user is not superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user