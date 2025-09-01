from fastapi import APIRouter, HTTPException
from app.schemas.trip import TripCreate, Trip

# Create the router object
# prefix="/trips" means all routes here will start with /trips
# tags=["Trips"] will group them in the Swagger UI
router = APIRouter(prefix="/trips", tags=["Trips"])

# In-memory fake DB
FAKE_DB: list[Trip] = []
next_id = 1  # To simulate auto-incrementing IDs


# route: GET /trips
# Returns a list of hardcoded trips (as if it was from a database)
@router.get("/", response_model=list[Trip])
def get_all_trips():
    return FAKE_DB


# route: POST /trips
# Receives a JSON body (parsed automatically as a Python dict)
# and echoes it back in the response
@router.post("/", response_model=Trip)
def create_trip(trip: TripCreate):
    global next_id

    # trip.model_dump() returns a dictionary (e.g., {"title": ..., "start_date": ..., ...}).
    # **trip.model_dump() unpacks that dictionary as keyword arguments.
    trip_data = Trip(id=next_id, **trip.model_dump())

    FAKE_DB.append(trip_data)
    next_id += 1
    return trip_data


# route: GET /trips/{trip_id}
# Returns a trip by its unique ID
@router.get("/{trip_id}", response_model=Trip)
def get_trip_by_id(trip_id: int):
    for trip in FAKE_DB:
        if trip.id == trip_id:
            return trip
    # If not found, raise a 404 Not Found error
    raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")


# route: DELETE /trips/{trip_id}
# Allows users to remove a trip by ID
@router.delete("/{trip_id}", response_model=Trip)
def delete_trip(trip_id: int):
    global FAKE_DB
    for trip in FAKE_DB:
        if trip.id == trip_id:
            FAKE_DB.remove(trip)
            return trip
    raise HTTPException(status_code=404, detail="Trip not found")
