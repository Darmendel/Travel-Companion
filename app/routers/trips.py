from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.trip import Trip as TripModel
from app.schemas.trip import TripCreate, TripUpdate, Trip


# Create the router object
# prefix="/trips" means all routes here will start with /trips
# tags=["Trips"] will group them in the Swagger UI
router = APIRouter(prefix="/trips", tags=["Trips"])


# route: GET /trips - Get all trips
# Returns a list of all trips in the database
# SELECT * FROM trips;
""" get_db() = dependency injection - FastAPI automatically "injects" (db) into my route -
before running this route, FastAPI calls get_db() function, take whatever it returns,
and pass it into this parameter called db.
When FastAPI sees Depends(get_db), it calls get_db(), then the -yield db- gives my route
a working database session.
* Depends is a FastAPI utility that tells the FastAPI framework: this function (my route)
need somthing before it can run - please run that other function first and give me its
result. That "other function" (get_db) is called a: dependency.
* Without Depends - its needed to run get_db's code again and again *in every single route* - 
very repetitive..
After the route finishes, FastAPI ensures the session is *closed safely*, even if an
error happens.

1. FastAPI -> opens connection
2. SQLAlchemy -> queries data
3. FastAPI -> closes connection"""
@router.get("/", response_model=list[Trip])
def get_all_trips(db: Session = Depends(get_db)):
    trips = db.query(TripModel).all()  # SELECT * FROM trips;
    return trips


# input in POST/UPDATE: TripCreate / TripUpdate - (Pydantic input) for validation
# output in POST/UPDDATE: TripModel - (SQLAlchemy) for DB operations
# output in GET/DELETE: Trip - (Pydantic output) for responses


# route: POST /trips - Create a new trip
# Receives a JSON body (parsed automatically as a Python dict)
# and echoes it back in the response
# INSERT INTO trips (...) VALUES (...);
""" * FastAPI will run the TripCreate validation first *before* running this route
(if one of the TripCreate's field isn't valid - this route function never runs)"""
@router.post("/", response_model=Trip)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):

    # TripCreate is a Pydantic model, so trip.model_dump() gives a dict:
    # trip.model_dump() returns a dictionary (e.g., {"title": ..., "start_date": ..., ...}).
    # **trip.model_dump() unpacks that dictionary as keyword arguments.
    # output in POST/UPDDATE: TripModel - (SQLAlchemy) for DB operations:
    # using TripModel(**trip.model_dump()) instead of Trip(**trip.model_dump()).
    new_trip = TripModel(**trip.model_dump())

    db.add(new_trip)  # stage new trip for insertion
    db.commit()  # commit = save to db
    db.refresh(new_trip)  # get the newly generated ID and updated state
    return new_trip


# route: GET /trips/{trip_id} - Get a specific trip by its ID
# Returns a trip by its unique ID
# SELECT * FROM trips WHERE id = ...;
@router.get("/{trip_id}", response_model=Trip)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()

    # If not found, raise a 404 Not Found error
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")
    return trip
    


# route: PUT /trips/(trip_id} - Update a trip
# Updates a trip, given its unique ID
# UPDATE trips SET ... WHERE id = ...;
@router.put("/{trip_id}", response_model=Trip)
def update_trip(trip_id: int, trip_update: TripUpdate, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()

    # If not found, raise a 404 Not Found error
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")
    
    update_data = trip_update.model_dump(exclude_unset=True)  # gives only the fields the user included in the request body

    # Manual validation for dates (incase that only end_date is being updated)
    new_start = update_data.get("start_date", trip.start_date)
    new_end = update_data.get("end_date", trip.end_date)

    if new_end < new_start:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    
    # Apply only provided fields
    for key, value in update_data.items():
        setattr(trip, key, value)  # setattr(object, attribute_name, value)
    # Using setattr for dynamic data:
    # When we don’t know what keys will come in from a request, we use setattr() to apply changes flexibly

    db.commit()  # Skip commit() -> Nothing gets saved to PostgreSQL
    db.refresh(trip)  # Skip refresh -> Data is saved, but your Python object may have outdated fields (like missing new ID or timestamps)
    return trip


# route: DELETE /trips/{trip_id}
# Allows users to remove a trip by ID
# DELETE FROM trips WHERE id = ...;
@router.delete("/{trip_id}", response_model=Trip)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()

    # If not found, raise a 404 Not Found error
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")
    
    db.delete(trip)
    db.commit()
    return trip
