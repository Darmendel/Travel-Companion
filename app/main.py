# Import FastAPI class to create the API application
from fastapi import FastAPI

# Import the trips router (where the /trips routes are defined)
from app.routers import trips

# Create a FastAPI app instance
app = FastAPI()

# Register the /trips routes into the app
app.include_router(trips.router)


# A simple test route: GET /
@app.get("/")
def root():
    return {"message": "Hello from Travel Companion API"}

# run: uvicorn app.main:app --reload --port 8001


# from fastapi import FastAPI
# from app.routers import trips
#
# app = FastAPI()
#
# app.include_router(trips.router)
#
# @app.get("/")
# def root():
#     return {"message": "Travel Companion API"}
#
# # Run the app - run in terminal: uvicorn app.main:app --reload
