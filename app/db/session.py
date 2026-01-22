import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Read DATABASE_URL from the environment variables.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dar:cabbage27@localhost:5432/travel_app",  # if DATABASE_URL doesn't exist - uses this
)

# Create the async SQLAlchemy engine (handles DB connections)
engine = create_async_engine(DATABASE_URL, echo=False)

# Create a configured async session class (session factory)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all ORM models (every model inherits from this)
# Base is a special SQLAlchemy class factory that keeps track of all ORM models that inherit from it (Trip, User, etc)
Base = declarative_base()


# Async dependency for FastAPI routes
async def get_db():
    """
    Async dependency function that yields a new database session for each request
    and closes it afterward.
    """
    async with AsyncSessionLocal() as session:  # creates a new SQLAlchemy session
        try:
            yield session
        finally:
            await session.close()


# Note: To create tables, use async context:
# async def init_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
