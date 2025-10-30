from fastapi import FastAPI
from app.routers import trips

app = FastAPI()  # Create a FastAPI app instance
app.include_router(trips.router)  # Register the /trips routes into the app


# A simple test route: GET /
@app.get("/")
def root():
    return {"message": "Hello from Travel Companion API"}

# (pyenv install 3.10.13 - this installs it once. don't run it again)
# pyenv local 3.10.13 - when opening new terminal, use this once (changing the interpreter locally to be this version).
# run: uvicorn app.main:app --reload --port 8000 (uvicorn - python library that runs fastapi's library on some cores, a few instances, accepting a few users at a time as a server, chatgpt).
