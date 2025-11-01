import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
from app.models.trip import Trip as TripModel

# Create a temporary database (named test_db)
SQLALCHEMY_TEST_URL = "postgresql+psycopg2://dar:cabbage27@localhost:5432/test_db"  # or: "sqlite:///./test.db" - SQLite for speed
# SQLALCHEMY_TEST_URL = "sqlite:///./test.db"  # for SQLite

# Create test engine and session
# engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})  # for sqlite (Allows this SQLite database connection to be shared across multiple threads - SQLite’s default behavior is single-threaded)
engine = create_engine(SQLALCHEMY_TEST_URL)  # PostgreSQL
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables at the start of the test session, drop them at the end."""
    print("\n🧱 Creating tables for test database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    print("\n🧹 Dropping tables after tests...")
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Creates a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)

    try:
        yield db
    finally:
        db.close()
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
    with TestClient(app) as c:
        yield c
    
    # Clears overrides before next tests
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_trip(db_session):
    """Inserts a sample trip before each test that needs an existing record."""
    trip = TripModel(
        title="Test Trip",
        start_date="2025-11-01",
        end_date="2025-11-10",
        destinations=["Paris", "London", "Tokyo"]
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip


# run in terminal: PYTHONPATH=. pytest -v
