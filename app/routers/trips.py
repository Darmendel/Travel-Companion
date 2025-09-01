from fastapi import APIRouter, HTTPException
from app.schemas.trip import TripCreate, TripUpdate, Trip
from app.db.fake_db import FAKE_DB, NEXT_ID

# Create the router object
# prefix="/trips" means all routes here will start with /trips
# tags=["Trips"] will group them in the Swagger UI
router = APIRouter(prefix="/trips", tags=["Trips"])


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

    # trip.model_dump() returns a dictionary (e.g., {"title": ..., "start_date": ..., ...}).
    # **trip.model_dump() unpacks that dictionary as keyword arguments.
    trip_data = Trip(id=NEXT_ID["value"], **trip.model_dump())

    FAKE_DB.append(trip_data)
    NEXT_ID["value"] += 1
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


# route: PUT /trips/(trip_id}
# Updates a trip, given its unique ID
@router.put("/{trip_id}", response_model=Trip)
def update_trip(trip_id: int, trip_update: TripUpdate):
    for i, trip in enumerate(FAKE_DB):
        if trip.id == trip_id:
            # update_data is the new data, and trip_data is the data of the trip (with trip_id)
            update_data = trip_update.model_dump(exclude_unset=True)  # gives us only the fields the user included in the request body.
            trip_data = trip.model_dump()

            # Manually validate end_date with new start_date if both are present
            if "end_date" in update_data and "start_date" not in update_data:
                # Needed for validation: end_date must be compared to start_date
                update_data["start_date"] = trip_data["start_date"]

            trip_data.update(update_data)  # changing trip_data to be update_data
            updated = Trip(**trip_data)
            FAKE_DB[i] = updated
            return updated

    # If not found, raise a 404 Not Found error
    raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")


# route: DELETE /trips/{trip_id}
# Allows users to remove a trip by ID
@router.delete("/{trip_id}", response_model=Trip)
def delete_trip(trip_id: int):
    for trip in FAKE_DB:
        if trip.id == trip_id:
            FAKE_DB.remove(trip)
            return trip
    raise HTTPException(status_code=404, detail=f"Trip with ID {trip_id} not found")
