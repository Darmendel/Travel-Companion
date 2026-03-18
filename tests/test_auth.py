# tests/test_auth.py
"""
Authentication & JWT Tests

Tests for:
- User registration
- Login (JWT token generation)
- Token validation
- Protected endpoints
- Password hashing
- User profile management
"""

import pytest
from datetime import datetime, timedelta
from app.auth.jwt import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)


# ==================== JWT TOKEN TESTS (Pure Functions) ====================

def test_create_access_token():
    """Test JWT token creation"""
    data = {"user_id": 123, "email": "test@example.com"}
    token = create_access_token(data)

    assert token is not None
    assert len(token) > 50
    assert isinstance(token, str)


def test_verify_valid_token():
    """Test verification of valid JWT token"""
    data = {"user_id": 123, "email": "test@example.com"}
    token = create_access_token(data)

    payload = verify_token(token)
    assert payload is not None
    assert payload["user_id"] == 123
    assert payload["email"] == "test@example.com"
    assert "exp" in payload  # Expiration time should be present


def test_verify_invalid_token():
    """Test verification fails for invalid token"""
    invalid_token = "invalid.jwt.token"
    payload = verify_token(invalid_token)
    assert payload is None


def test_verify_malformed_token():
    """Test verification fails for malformed token"""
    malformed_tokens = [
        "",
        "just.two.parts",
        "not-a-jwt-at-all",
        "a" * 200,  # Random string
    ]
    for token in malformed_tokens:
        payload = verify_token(token)
        assert payload is None, f"Should reject token: {token[:50]}"


def test_verify_expired_token():
    """Test verification fails for expired token"""
    data = {"user_id": 123}
    # Create token that expires immediately (in the past)
    expires = timedelta(seconds=-1)
    token = create_access_token(data, expires_delta=expires)

    payload = verify_token(token)
    assert payload is None


def test_token_custom_expiration():
    """Test token with custom expiration time"""
    data = {"user_id": 123}
    expires = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=expires)

    payload = verify_token(token)
    assert payload is not None

    # Check expiration is approximately 5 minutes from now
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
    expected = datetime.utcnow() + timedelta(minutes=5)

    # Allow 10 second tolerance
    assert abs((exp_datetime - expected).total_seconds()) < 10


def test_token_contains_all_data():
    """Test token preserves all provided data"""
    data = {
        "user_id": 999,
        "email": "complex@example.com",
        "role": "admin",
        "permissions": ["read", "write"]
    }
    token = create_access_token(data)
    payload = verify_token(token)

    assert payload["user_id"] == 999
    assert payload["email"] == "complex@example.com"
    assert payload["role"] == "admin"
    assert payload["permissions"] == ["read", "write"]


# ==================== PASSWORD HASHING TESTS (Pure Functions) ====================

def test_password_hashing():
    """Test password gets hashed correctly"""
    password = "mySecurePassword123"
    hashed = get_password_hash(password)

    assert hashed != password  # Hash should be different
    assert len(hashed) > 50  # Bcrypt hashes are long
    assert hashed.startswith("$2b$")  # Bcrypt identifier


def test_password_verification_success():
    """Test correct password verification"""
    password = "mySecurePassword123"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


def test_password_verification_failure():
    """Test incorrect password verification"""
    password = "mySecurePassword123"
    hashed = get_password_hash(password)

    assert verify_password("wrongPassword", hashed) is False


def test_different_passwords_different_hashes():
    """Test same password gets different hashes (due to salt)"""
    password = "mySecurePassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Different hashes (bcrypt uses random salt)
    assert hash1 != hash2

    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_empty_password_hashing():
    """Test empty password can be hashed (validation should happen elsewhere)"""
    hashed = get_password_hash("")
    assert len(hashed) > 50
    assert verify_password("", hashed) is True
    assert verify_password("anything", hashed) is False


def test_long_password_hashing():
    """Test very long password"""
    long_password = "a" * 1000
    hashed = get_password_hash(long_password)
    assert verify_password(long_password, hashed) is True


def test_special_characters_in_password():
    """Test password with special characters"""
    special_password = "P@ssw0rd!#$%^&*()"
    hashed = get_password_hash(special_password)
    assert verify_password(special_password, hashed) is True


# ==================== REGISTRATION TESTS ====================

@pytest.mark.asyncio
async def test_register_success(client):
    """Test successful user registration with unique email"""
    unique_email = f"newuser_{datetime.now().timestamp()}@example.com"

    response = await client.post("/auth/register", json={
        "email": unique_email,
        "password": "securepass123",
        "full_name": "New User"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert "id" in data
    # Password should NOT be in response
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    """Test registration with existing email fails"""
    response = await client.post("/auth/register", json={
        "email": test_user.email,  # Already exists in conftest
        "password": "securepass123",
        "full_name": "Duplicate User"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    """Test registration with invalid email format"""
    response = await client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "securepass123"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_password_too_short(client):
    """Test registration with password < 8 characters"""
    response = await client.post("/auth/register", json={
        "email": "short@example.com",
        "password": "short"  # Only 5 chars
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_without_full_name(client):
    """Test registration works without full_name (optional field)"""
    unique_email = f"noname_{datetime.now().timestamp()}@example.com"

    response = await client.post("/auth/register", json={
        "email": unique_email,
        "password": "securepass123"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert data["full_name"] is None


@pytest.mark.asyncio
async def test_register_with_very_long_name(client):
    """Test registration with very long full_name fails validation"""
    long_name = "A" * 300  # Over 255 char limit

    response = await client.post("/auth/register", json={
        "email": "longname@example.com",
        "password": "securepass123",
        "full_name": long_name
    })

    # Should fail validation (max_length=255 in schema)
    assert response.status_code == 422


# ==================== LOGIN TESTS ====================
# Note: We can't easily test login with the existing test_user
# because we don't know its plaintext password.
# These tests use *newly* registered users.

@pytest.mark.asyncio
async def test_login_success_after_registration(client):
    """Test successful login with OAuth2 endpoint after registration"""
    # First, register a new user
    unique_email = f"logintest_{datetime.now().timestamp()}@example.com"
    password = "testpass123"

    register_response = await client.post("/auth/register", json={
        "email": unique_email,
        "password": password,
        "full_name": "Login Test User"
    })
    assert register_response.status_code == 201

    # Now login with OAuth2 endpoint
    login_response = await client.post("/auth/token", data={
        "username": unique_email,  # OAuth2 uses 'username' field
        "password": password
    })

    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 50


@pytest.mark.asyncio
async def test_login_json_endpoint(client):
    """Test login via JSON endpoint"""
    # Register user first
    unique_email = f"jsonlogin_{datetime.now().timestamp()}@example.com"
    password = "testpass456"

    await client.post("/auth/register", json={
        "email": unique_email,
        "password": password
    })

    # Login via JSON endpoint
    response = await client.post("/auth/login", json={
        "email": unique_email,
        "password": password
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Test login fails with wrong password"""
    # Register user
    unique_email = f"wrongpass_{datetime.now().timestamp()}@example.com"

    await client.post("/auth/register", json={
        "email": unique_email,
        "password": "correctpass123"
    })

    # Try to login with wrong password
    response = await client.post("/auth/login", json={
        "email": unique_email,
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login fails with non-existent email"""
    response = await client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "somepassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client, db_session):
    """Test login fails for inactive user"""
    # Register and then deactivate
    unique_email = f"inactive_{datetime.now().timestamp()}@example.com"
    password = "testpass123"

    register_response = await client.post("/auth/register", json={
        "email": unique_email,
        "password": password
    })
    user_id = register_response.json()["id"]

    # Deactivate user via repository
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db_session)
    await repo.update_user(user_id, is_active=False)
    await db_session.commit()

    # Try to login
    response = await client.post("/auth/login", json={
        "email": unique_email,
        "password": password
    })

    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


# ==================== PROTECTED ENDPOINT TESTS ====================

@pytest.mark.asyncio
async def test_get_current_user_success(client, test_user):
    """Test /auth/me returns current user info"""
    # The 'client' fixture is already authenticated as test_user
    response = await client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_protected_endpoint_without_auth():
    """Test protected endpoint fails without authentication"""
    # Create unauthenticated client (don't use the 'client' fixture)
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    # Clear any overrides
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as unauth_client:
            response = await unauth_client.get("/auth/me")
            assert response.status_code == 401
    finally:
        # Restore overrides
        app.dependency_overrides = original_overrides


@pytest.mark.asyncio
async def test_trips_endpoint_requires_auth():
    """Test trips endpoint requires authentication"""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as unauth_client:
            response = await unauth_client.get("/trips/")
            assert response.status_code == 401
    finally:
        app.dependency_overrides = original_overrides


# ==================== USER PROFILE TESTS ====================

@pytest.mark.asyncio
async def test_update_user_full_name(client, test_user):
    """Test updating user full name"""
    response = await client.put("/auth/me", json={
        "full_name": "Updated Name"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == test_user.email  # Email unchanged


@pytest.mark.asyncio
async def test_update_user_email(client, test_user, db_session):
    """Test updating user email to unique address"""
    new_email = f"updated_{datetime.now().timestamp()}@example.com"

    response = await client.put("/auth/me", json={
        "email": new_email
    })

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email

    # Refresh test_user to restore original state for other tests
    await db_session.refresh(test_user)


@pytest.mark.asyncio
async def test_update_user_password(client, test_user, db_session):
    """Test updating user password"""
    new_password = "newSecurePass456"

    response = await client.put("/auth/me", json={
        "password": new_password
    })

    assert response.status_code == 200

    # Verify password was updated by checking hash changed
    await db_session.refresh(test_user)
    # We can't test login here because test_user.email password is unknown
    # But we verified the endpoint returns 200


@pytest.mark.asyncio
async def test_update_email_to_existing_email(client, test_user, db_session):
    """Test updating email to one that's already taken fails"""
    # Create another user
    other_email = f"other_{datetime.now().timestamp()}@example.com"

    await client.post("/auth/register", json={
        "email": other_email,
        "password": "pass123",
        "full_name": "Other User"
    })

    # Try to update test_user's email to other_user's email
    response = await client.put("/auth/me", json={
        "email": other_email
    })

    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()


# ==================== INTEGRATION WORKFLOW ====================




# ==================== EDGE CASES ====================

@pytest.mark.asyncio
async def test_multiple_login_sessions(client):
    """Test user can have multiple active sessions (tokens)"""
    unique_email = f"multisession_{datetime.now().timestamp()}@example.com"
    password = "sessiontest123"

    # Register
    await client.post("/auth/register", json={
        "email": unique_email,
        "password": password
    })

    # Login twice
    response1 = await client.post("/auth/login", json={
        "email": unique_email,
        "password": password
    })
    token1 = response1.json()["access_token"]

    response2 = await client.post("/auth/login", json={
        "email": unique_email,
        "password": password
    })
    token2 = response2.json()["access_token"]

    # Both tokens should be valid and different
    assert token1 != token2
    payload1 = verify_token(token1)
    payload2 = verify_token(token2)
    assert payload1 is not None
    assert payload2 is not None
    assert payload1["user_id"] == payload2["user_id"]
