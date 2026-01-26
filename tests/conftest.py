import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select
from app.main import app
from app.db.session import get_db, Base
from app.models.trip import Trip as TripModel
from app.models.stop import Stop as StopModel
from app.models.user import User as UserModel
from datetime import date, timedelta

TEST_DB_URL = "postgresql+asyncpg://dar:cabbage27@localhost:5432/test_db"

# ============================================================
# GLOBAL TEST USER - for simple fixtures
# ============================================================
TEST_USER_ID = 1
TEST_USER_EMAIL = "test@example.com"


# ============================================================
# CORE FIXTURES
# ============================================================

@pytest_asyncio.fixture(scope="module")
async def async_engine():
    """Create async engine within the event loop."""
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def setup_database(async_engine):
    """Create all tables at the start of each test module, drop them at the end."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("\nCreating tables for test database")
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("\nDropping tables after tests")


@pytest_asyncio.fixture(scope="module")
async def test_user(async_engine, setup_database):
    """
    Use this when:
    - When user.email, user.full_name, etc is needed
    - To test with different users
    - Testing authentication/authorization
    """
    AsyncTestingSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncTestingSessionLocal() as session:
        result = await session.execute(
            select(UserModel).filter(UserModel.id == TEST_USER_ID)
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            user = UserModel(
                id=TEST_USER_ID,
                email=TEST_USER_EMAIL,
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeWCxInN66qG",
                full_name="Test User",
                is_active=True,
                is_superuser=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"\n✅ Created test user: {user.email} (ID: {user.id})")
            return user
        else:
            print(f"\n✅ Test user already exists: {existing_user.email} (ID: {existing_user.id})")
            return existing_user


@pytest_asyncio.fixture
async def db_session(async_engine, setup_database, test_user):
    """
    DB Session - ensures test_user exists before any test runs.
    """
    AsyncTestingSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(async_engine, setup_database, test_user):
    """
    AUTHENTICATED CLIENT - for API tests

    Use this for:
    - API endpoint tests (test_trips.py, test_stops.py)
    - Integration tests through HTTP

    All requests are automatically authenticated as test_user!
    """
    from app.auth.dependencies import get_current_user

    AsyncTestingSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            yield session

    async def override_get_current_user():
        """Mock authentication - returns test_user"""
        return test_user

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================
# SIMPLE FIXTURES - use TEST_USER_ID constant
# ============================================================

@pytest_asyncio.fixture
async def sample_trip(db_session):
    """
    SIMPLE FIXTURE - uses global TEST_USER_ID

    Use for: Quick trips that don't need special user details
    """
    trip = TripModel(
        title="Test Trip",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20),
        user_id=TEST_USER_ID  # Global constant
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture
async def sample_trip_with_stop(db_session):
    """Simple fixture with stop - uses global TEST_USER_ID"""
    trip = TripModel(
        title="Trip with Stop",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20),
        user_id=TEST_USER_ID
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)

    stop = StopModel(
        trip_id=trip.id,
        name="Tokyo",
        country="Japan",
        start_date=date.today() + timedelta(days=11),
        end_date=date.today() + timedelta(days=15),
        order_index=0,
        latitude=35.6762,
        longitude=139.6503,
        notes="Visit Shibuya"
    )
    db_session.add(stop)
    await db_session.commit()
    await db_session.refresh(stop)

    return trip, stop


# ============================================================
# ADVANCED FIXTURES - when we need user object
# ============================================================

@pytest_asyncio.fixture
async def trip_for_user(db_session, test_user):
    """
    ADVANCED FIXTURE - uses full test_user object

    Use for: Tests that need user details or multiple users

    Example:
        async def test_user_can_only_see_own_trips(
            client, 
            trip_for_user,  # ← belongs to test_user
            test_user
        ):
            # Create another user's trip
            other_trip = TripModel(title="Other", user_id=999)

            # test_user should only see their trip
            response = await client.get("/trips/")
            assert len(response.json()) == 1
    """
    trip = TripModel(
        title="User's Trip",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20),
        user_id=test_user.id  # ← Full user object
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture
async def multiple_users_with_trips(db_session, async_engine):
    """
    COMPLEX FIXTURE - for multi-user tests

    Use for: Testing user isolation, permissions, etc.

    Returns:
        dict: {
            'user1': User(id=1, email='test@example.com'),
            'user2': User(id=2, email='other@example.com'),
            'user1_trips': [Trip, Trip],
            'user2_trips': [Trip]
        }
    """
    AsyncTestingSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncTestingSessionLocal() as session:
        # Create second user
        user2 = UserModel(
            id=2,
            email="other@example.com",
            hashed_password="$2b$12$...",
            full_name="Other User",
            is_active=True,
            is_superuser=False
        )
        session.add(user2)
        await session.commit()
        await session.refresh(user2)

        # Create trips for each user
        user1_trips = [
            TripModel(
                title=f"User1 Trip {i}",
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=20),
                user_id=TEST_USER_ID
            )
            for i in range(2)
        ]

        user2_trips = [
            TripModel(
                title="User2 Trip",
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=20),
                user_id=user2.id
            )
        ]

        for trip in user1_trips + user2_trips:
            session.add(trip)

        await session.commit()

        for trip in user1_trips + user2_trips:
            await session.refresh(trip)

        # Get user1
        result = await session.execute(
            select(UserModel).filter(UserModel.id == TEST_USER_ID)
        )
        user1 = result.scalar_one()

        return {
            'user1': user1,
            'user2': user2,
            'user1_trips': user1_trips,
            'user2_trips': user2_trips
        }


# ============================================================
# USAGE EXAMPLES IN TESTS
# ============================================================

"""
# ✅ Example 1: Simple API test
async def test_create_trip(client):
    # client is already authenticated!
    response = await client.post("/trips/", json={...})
    assert response.status_code == 201


# ✅ Example 2: Simple DB test
async def test_trip_model(sample_trip):
    # sample_trip uses TEST_USER_ID automatically
    assert sample_trip.user_id == 1


# ✅ Example 3: Test with user details
async def test_user_email(trip_for_user, test_user):
    # Need user.email? Use test_user
    assert trip_for_user.user_id == test_user.id
    assert test_user.email == "test@example.com"


# ✅ Example 4: Multi-user test
async def test_user_isolation(client, multiple_users_with_trips):
    users = multiple_users_with_trips

    # user1 should see 2 trips
    # user2 should see 1 trip
    # They shouldn't see each other's trips!
"""