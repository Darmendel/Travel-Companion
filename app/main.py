from fastapi import FastAPI
from app.routers import trips

app = FastAPI()  # Create a FastAPI app instance
app.include_router(trips.router)  # Register the /trips routes into the app


# A simple test route: GET /
@app.get("/")
def root():
    return {"message": "Hello from Travel Companion API"}

# run: uvicorn app.main:app --reload --port 8000
