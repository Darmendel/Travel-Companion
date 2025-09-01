from typing import List
from app.schemas.trip import Trip

# In-memory fake DB
FAKE_DB: List[Trip] = []
NEXT_ID = {"value": 1}  # Wrap NEXT_ID in a mutable container
