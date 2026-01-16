# app/models/stop.py
from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class Stop(Base):
    __tablename__ = "stops"
    id = Column(Integer, primary_key=True, index=True)

    # Many stops -> one trip
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False, default=0)

    name = Column(String(200), nullable=False)      # e.g., "Tokyo", "Tel Aviv"
    country = Column(String(120), nullable=True)    # optional

    # Duration of the stop
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)  # limit by Pydantic: notes: Optional[str] = Field(None, max_length=2000)

    # Relationship back to Trip
    trip = relationship("Trip", back_populates="stops")

    __table_args__ = (
        Index("ix_stops_trip_id_order", "trip_id", "order_index"),  # index: quickly fetch stops for trip, ordered by index
        UniqueConstraint("trip_id", "order_index", name="uq_stops_trip_id_order"),  # in every trip: every stop has to have a *unique* order_index
    )

    def __repr__(self) -> str:
        return (
            f"<Stop id={self.id} "
            f"trip_id={self.trip_id} "
            f"name='{self.name}' "
            f"order_index={self.order_index} "
            f"dates={self.start_date}->{self.end_date}>"
        )