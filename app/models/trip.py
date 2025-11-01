from sqlalchemy import Column, Integer, String, Date, ARRAY
from app.db.session import Base


# ORM Model
class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    destinations = Column(ARRAY(String), nullable=False)

    def __repr__(self):
        return f"<TripModel(id={self.id}, title={self.title})>"
