# Import APIRouter to define a group of related routes
from fastapi import APIRouter

# Create the router object
# prefix="/trips" means all routes here will start with /trips
# tags=["Trips"] will group them in the Swagger UI
router = APIRouter(prefix="/trips", tags=["Trips"])


# Example route: GET /trips
# Returns a list of hardcoded trips (as if it was from a database)
@router.get("/")
def get_all_trips():
    return [
        {"id": 1, "title": "Japan Summer 2025"},
        {"id": 2, "title": "London Paris 2025"}
    ]


# Example route: POST /trips
# Receives a JSON body (parsed automatically as a Python dict)
# and echoes it back in the response
@router.post("/")
def create_trip(trip: dict):
    return {
        "message": "Trip received!",
        "trip": trip
    }


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.models.trip import Trip
# from app.schemas.trip import TripCreate, TripOut
# from app.db.dependency import get_db
#
# # Create the Trip Router
# router = APIRouter(
#     prefix="/trips",
#     tags=["Trips"]
# )
#
# @router.post("/", response_model=TripOut)
# def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
#     db_trip = Trip(**trip.dict())
#     db.add(db_trip)
#     db.commit()
#     db.refresh(db_trip)
#     return db_trip
#
# @router.get("/", response_model=list[TripOut])
# def read_trips(db: Session = Depends(get_db)):
#     return db.query(Trip).all()
