import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read DATABASE_URL from the environment variables.
# If DATABASE_URL is not set (e.g. when running locally without export),
# fall back to a default local database URL.
#
# This allows the same codebase to work with different databases
# (local / test / production) without changing the code.
DATABASE_URL = os.getenv(
    "DATABASE_URL",  # os.getenv("DATABASE_URL") looks for an environment variable named DATABASE_URL
    "postgresql+psycopg2://dar:cabbage27@localhost:5432/travel_app",  # if DATABASE_URL doesn't exist - uses this (default url in case DATABASE_URL is missing)
)

# Create the SQLAlchemy engine (handles DB connections)
engine = create_engine(DATABASE_URL)

# Create a configured session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # session factory

# Base class for all ORM models (every model inherits from this)
# Base is a special SQLAlchemy class factory that keeps track of all ORM models that inherit from it (Trip, User, etc)
Base = declarative_base()

# Dependency for FastAPI routes - creates a SQLAlchemy session (this session is passed into my route as the db argument).
# (FastAPI dependency that provides a session per request - Every API call will get its own Session instance so requests don’t clash)
def get_db():
    """A dependency function that yields a new database session for each request and closes it afterward."""
    db = SessionLocal()  # creates a new SQLAlchemy session
    try:
        yield db  # gives it to the route temporarily
    finally:
        db.close()  # closes it automatically when done


# Base.metadata.create_all(bind=engine)


# Quick test for standalone execution
# run in terminal: python -m app.db.session
# The -m flag tells Python to run a module (a .py file inside a package) as if it were a standalone script
# (instead of typing: python path/to/your/file/app/db/session.py)
# if __name__ == "__main__":
#     with engine.connect() as conn:
#         print("✅ Connected to database!")

# In terminal:
# Switch to the postgres user (PostgreSQL system account): sudo -i -u postgres
# Enter the PostgreSQL shell: psql
# (the prompt changes from: postgres@dar-Lenovo-...KB:~$ -> to: postgres=#)
# OR enter the PostgreSQL shell with user name: psql -U dar -d travel_app -h localhost
