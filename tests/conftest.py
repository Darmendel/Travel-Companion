import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from app.main import app
from app.db.session import get_db, Base

# Create a temporary database (named test_db)
SQLALCHEMY_TEST_URL = "postgresql+psycopg2://dar:cabbage27@localhost:5432/test_db"  # or: "sqlite:///./test.db" - SQLite for speed


# Create test engine and session
# engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}) - for sqlite (Allows this SQLite database connection to be shared across multiple threads - SQLite’s default behavior is single-threaded)
engine = create_engine(SQLALCHEMY_TEST_URL)  # PostgreSQL
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency override - FastAPI will use this instead of the real get_db
def override_get_db():
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create all tables at the start of the test session
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Creates a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    yield db
    db.close()
    transaction.rollback()
    connection.close()
