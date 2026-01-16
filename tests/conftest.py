import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
from app.models.trip import Trip as TripModel

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
    db = TestingSessionLocal(bind=connection)  # Creates a new Session object (my ORM interface), that uses the same connection, the same transaction above.

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
        try:
            yield db_session
        finally:
            db_session.close()
    
    # Clears any previous test overrides
    app.dependency_overrides.clear()

    # Replace (“override”) dependencies (like get_db) - just for testing
    app.dependency_overrides[get_db] = override_get_db

    # Returns a FastAPI test client that uses this override
    with TestClient(app) as c:  # with TestClient(app) spins up a lightweight version of my FastAPI app (I can make real HTTP requests to it, like .get() and .post()), and when the test is over, the context manager automatically shuts it down (this is entirely in-memory).
        yield c
    
    # Clears overrides before next tests
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_trip(db_session):
    """Inserts a sample trip before each test that needs an existing record."""
    trip = TripModel(
        title="Test Trip",
        start_date="2025-11-01",
        end_date="2025-11-10"
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip
