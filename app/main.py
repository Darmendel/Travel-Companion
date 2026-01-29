# app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import trips, stops, auth

# Load environment variables
load_dotenv()

# CORS Configuration
# Default to localhost only for security
# In production, set CORS_ORIGINS in .env to your actual frontend domain
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Validate CORS origins in production
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production" and "*" in CORS_ORIGINS:
    raise ValueError(
        "CORS_ORIGINS cannot be '*' in production!\n"
        "Please set specific allowed origins in your .env file.\n"
        "Example: CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com"
    )


# Create a FastAPI app instance
app = FastAPI(
    title="Travel Planning API",
    description="API for planning trips with multiple stops",
    version="2.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(trips.router)
app.include_router(stops.router)
app.include_router(auth.router)


@app.get("/")
def root():
    """Root endpoint - health check."""
    return {
        "message": "Hello from Travel Companion API",
        "status": "running",
        "environment": ENVIRONMENT,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT
    }


# Development notes:
# - Run: uvicorn app.main:app --reload --port 8000
# - Docs: http://localhost:8000/docs