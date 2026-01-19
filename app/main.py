# app/main.py
from fastapi import FastAPI
from app.routers import trips, stops
from app.db.session import Base, engine

# Create database tables
# Base.metadata.create_all(bind=engine)

# Create a FastAPI app instance
app = FastAPI(
    title="Travel Planning API",
    description="API for planning trips with multiple stops",
    version="1.0.0"
)

# Include routers
app.include_router(trips.router)  # Register the /trips routes into the app
app.include_router(stops.router)

# route: GET /
@app.get("/")
def root():
    """Root endpoint - health check."""
    return {
        "message": "Hello from Travel Companion API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# (pyenv install 3.10.13 - this installs it once. don't run it again)
# pyenv local 3.10.13 - when opening new terminal, use this once (changing the interpreter locally to be this version).
# run: uvicorn app.main:app --reload --port 8000 (uvicorn - python library that runs fastapi's library on some cores, a few instances, accepting a few users at a time as a server, chatgpt).
