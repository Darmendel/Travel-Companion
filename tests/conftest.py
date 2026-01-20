import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
from app.models.trip import Trip as TripModel
from app.models.stop import Stop as StopModel
from datetime import date, timedelta

# Create a temporary database (named test_db)
TEST_DB_URL = "postgresql+psycopg2://dar:cabbage27@localhost:5432/test_db"

# Create test engine and session
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables at the start of the test session, drop them at the end."""
    Base.metadata.drop_all(bind=engine)  # metadata = global catalog of my ORM table definitions.

    # Creates all tables defined on ORM models that inherit from Base, if they don't already exist.
    Base.metadata.create_all(bind=engine)
    print("\nCreating tables for test database")
    yield

    # Deletes all tables (*dangerous in production).
    Base.metadata.drop_all(bind=engine)
    print("\nDropping tables after tests")


@pytest.fixture()
def db_session():
    """Creates a new database session for each test."""
    connection = engine.connect()  # Manual connection to the database (rather than letting SQLAlchemy manage it automatically).
    transaction = connection.begin()  # Starts a new transaction (all inserts/updates/deletes performed through this connection wil stay inside this transaction, if not committed yet).
    db = TestingSessionLocal(
        bind=connection)  # Creates a new Session object (my ORM interface), that uses the same connection, the same transaction above.

    try:
        yield db  # Pauses the fixture and gives the test access to this db session.
    finally:  # After a test is finished, the database is rolled back to a clean state.
        db.close()  # Closes ORM session
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client that uses the test DB."""
    """Returns a TestClient with a PostgreSQL test session dependency override."""

    # Dependency override - FastAPI will use this instead of the real get_db
    # Override get_db so FastAPI uses this test session
    def override_get_db():
        # db = TestingSessionLocal()
        yield db_session

    # Clears any previous test overrides
    app.dependency_overrides.clear()

    # Replace ("override") dependencies (like get_db) - just for testing
    app.dependency_overrides[get_db] = override_get_db

    # Returns a FastAPI test client that uses this override
    with TestClient(
            app) as c:  # with TestClient(app) spins up a lightweight version of my FastAPI app (I can make real HTTP requests to it, like .get() and .post()), and when the test is over, the context manager automatically shuts it down (this is entirely in-memory).
        yield c

    # Clears overrides before next tests
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_trip(db_session):
    """Inserts a sample trip before each test that needs an existing record."""
    trip = TripModel(
        title="Test Trip",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20)
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip


@pytest.fixture()
def sample_trip_with_stop(db_session):
    """Creates a trip with one stop."""
    trip = TripModel(
        title="Trip with Stop",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=20)
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

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
    db_session.commit()
    db_session.refresh(stop)

    return trip, stop


@pytest.fixture()
def sample_trip_with_multiple_stops(db_session):
    """Creates a trip with three stops in order."""
    trip = TripModel(
        title="Trip with Multiple Stops",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=30)
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

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

    db_session.commit()
    for stop in stops:
        db_session.refresh(stop)

    return trip, stops