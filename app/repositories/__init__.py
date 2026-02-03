# app/repositories/__init__.py
"""
Repository Layer

This module contains all repository classes that handle database access.
Repositories provide a clean abstraction over database operations.
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.trip_repository import TripRepository
from app.repositories.stop_repository import StopRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "TripRepository",
    "StopRepository",
    "UserRepository",
]