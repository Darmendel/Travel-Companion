from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from app.db.session import Base


# ORM Model
class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    stops = relationship(
        "Stop",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Stop.order_index",
    )

    def __repr__(self) -> str:
        return (
            f"<Trip id={self.id} "
            f"title='{self.title}' "
            f"dates={self.start_date}->{self.end_date}>"
        )
