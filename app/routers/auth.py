# app/routers/auth.py
"""
Authentication Router

Endpoints for user registration, login, and profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, User, Token, UserUpdate
from app.services.user_service import UserService
from app.auth.dependencies import get_current_user, get_current_active_user
from app.models.user import User as UserModel

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Request body:
    ```json
    {
        "email": "user@example.com",
        "password": "strongpassword123",
        "full_name": "John Doe"  // optional
    }
    ```

    Returns:
    - User object (without password)

    Raises:
    - 400: Email already registered
    - 422: Invalid email format or password too short
    """
    user = await UserService.create_user(user_data, db)
    return user


@router.post("/token", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get access token.

    This endpoint uses OAuth2PasswordRequestForm, so it expects:
    - username: user's email
    - password: user's password

    Form data (application/x-www-form-urlencoded):
    - username=user@example.com
    - password=strongpassword123

    Returns:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
    ```

    Usage:
    After receiving the token, include it in all authenticated requests:
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```

    Raises:
    - 401: Invalid credentials
    """
    # Authenticate user (username field contains the email)
    user = await UserService.authenticate_user(
        form_data.username,  # OAuth2 standard uses 'username' field
        form_data.password,
        db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token = UserService.create_user_token(user)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login_json(
        email: str,
        password: str,
        db: AsyncSession = Depends(get_db)
):
    """
    Alternative login endpoint that accepts JSON.

    This is more convenient for modern frontends than the form-based /token endpoint.

    Request body:
    ```json
    {
        "email": "user@example.com",
        "password": "strongpassword123"
    }
    ```

    Returns same as /token endpoint.
    """
    user = await UserService.authenticate_user(email, password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = UserService.create_user_token(user)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get current user's profile information.

    Requires authentication (Bearer token in Authorization header).

    Returns:
    ```json
    {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_active": true,
        "created_at": "2024-01-01T12:00:00"
    }
    ```
    """
    return current_user


@router.put("/me", response_model=User)
async def update_current_user_info(
        user_update: UserUpdate,
        current_user: UserModel = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.

    Requires authentication.

    Request body (all fields optional):
    ```json
    {
        "email": "newemail@example.com",
        "full_name": "Jane Doe",
        "password": "newpassword123"
    }
    ```

    Returns updated user object.

    Raises:
    - 400: New email already taken by another user
    """
    updated_user = await UserService.update_user(
        current_user.id,
        user_update,
        db
    )
    return updated_user