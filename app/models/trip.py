from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base
from app.db.types import StringList

Base = declarative_base()

class TripModel(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    destinations = Column(String, nullable=False)  # Storing as comma-separated string *for now*
    # destinations = Column(StringList, nullable=False)

    def __repr__(self):
        return f"<TripModel(id={self.id}, title={self.title})>"