import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.db.session import get_db, Base
from app.models.trip import Trip as TripModel
from app.models.stop import Stop as StopModel
from datetime import date, timedelta

# Create a temporary async database (named test_db)
TEST_DB_URL = "postgresql+asyncpg://dar:cabbage27@localhost:5432/test_db"


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


@pytest_asyncio.fixture
async def db_session(async_engine, setup_database):
    """Creates a new async database session for each test."""
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
async def client(async_engine, setup_database):
    """FastAPI async test client that uses the test DB."""

    AsyncTestingSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Dependency override - each request gets its own session
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            yield session

    app.dependency_overrides.clear()  # Clears any previous test overrides
    app.dependency_overrides[get_db] = override_get_db  # Replace ("override") dependencies (like get_db) - just for testing

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()  # Clears overrides before next tests


@pytest_asyncio.fixture
async def sample_trip(db_session):
    """Inserts a sample trip before each test that needs an existing record."""
    trip = TripModel(
        title="Test Trip",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20)
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest_asyncio.fixture
async def sample_trip_with_stop(db_session):
    """Creates a trip with one stop."""
    trip = TripModel(
        title="Trip with Stop",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20)
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


@pytest_asyncio.fixture
async def sample_trip_with_multiple_stops(db_session):
    """Creates a trip with three stops in order."""
    trip = TripModel(
        title="Trip with Multiple Stops",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=30)
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)

    stops = []
    stop_data = [
        {"name": "Tokyo", "country": "Japan", "days": (11, 15), "order": 0},
        {"name": "Kyoto", "country": "Japan", "days": (16, 20), "order": 1},
        {"name": "Osaka", "country": "Japan", "days": (21, 25), "order": 2},
    ]

    for data in stop_data:
        stop = StopModel(
            trip_id=trip.id,
            name=data["name"],
            country=data["country"],
            start_date=date.today() + timedelta(days=data["days"][0]),
            end_date=date.today() + timedelta(days=data["days"][1]),
            order_index=data["order"]
        )
        db_session.add(stop)
        stops.append(stop)

    await db_session.commit()
    for stop in stops:
        await db_session.refresh(stop)

    return trip, stops