# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://dar:cabbage27@localhost:5432/travel_app"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflash=False, bind=engine)
Base = declarative_base()

# engine = create_engine("postgresql+psycopg2://dar:cabbage27@localhost:5432/travel_app")
# with engine.connect() as conn:
#     print("✅ Connected to database!")

# In terminal:
# Switch to the postgres user (PostgreSQL system account): sudo -i -u postgres
# Enter the PostgreSQL shell: psql
# (the prompt changes from: postgres@dar-Lenovo-...KB:~$ -> to: postgres=#)
# OR enter the PostgreSQL shell with user name: psql -U dar -d travel_app -h localhost
