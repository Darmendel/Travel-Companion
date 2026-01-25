# app/models/trip.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


# ORM Model
class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Foreign key to users table
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationship to stops (one trip has many stops)
    stops = relationship(
        "Stop",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Stop.order_index",
    )

    # Relationship to user (many trips belong to one user)
    user = relationship("User", back_populates="trips")

    def __repr__(self) -> str:
        return (
            f"<Trip id={self.id} "
            f"user_id={self.user_id} "
            f"title='{self.title}' "
            f"dates={self.start_date}->{self.end_date}>"
        )