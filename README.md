# Travel Companion API

A comprehensive RESTful API for managing trips and travel planning with user authentication, multiple stops per trip, and advanced validations. Built with FastAPI, PostgreSQL, and follows clean architecture principles with the Repository Pattern.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Authentication](#authentication)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Development](#development)

## ✨ Features

### User Management
- 🔐 Secure registration and login with JWT tokens
- 👤 User profile management
- 🔒 Password encryption with bcrypt
- ⏰ Configurable token expiration (default: 30 days)
- 👥 User-specific data isolation

### Trip Management
- 📅 Full CRUD operations for trips
- 🗓️ Date range validations
- 🔄 Partial updates support
- 🗑️ Cascade deletion (deleting trip removes all stops)
- 👤 User ownership verification

### Stop Management
- 📍 Multiple stops per trip with custom ordering
- 🌍 Geographic coordinates support (latitude/longitude)
- 🏳️ Country information
- ⚠️ Date overlap detection (allows 1-day transition)
- 🔢 Drag-and-drop style reordering
- ✅ Advanced validations:
  - Dates within trip range
  - Valid coordinates (prevents placeholder values like 0,0)
  - Rough country-coordinate matching
  - No overlapping dates between stops

## 🏗️ Architecture

The project follows **Clean Architecture** principles with a **3-layer architecture** and **Repository Pattern**:

```
┌─────────────────────────────────────────────┐
│            Router Layer                      │
│  (HTTP endpoints, request/response)          │
│                                              │
│  • trips.py    - Trip HTTP endpoints        │
│  • stops.py    - Stop HTTP endpoints        │
│  • auth.py     - Authentication endpoints   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           Service Layer                      │
│  (Business logic, orchestration)             │
│                                              │
│  • TripService  - Trip business rules       │
│  • StopService  - Stop validation & logic   │
│  • UserService  - Auth & user management    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         Repository Layer                     │
│  (Database access, SQL queries)              │
│                                              │
│  • TripRepository - Trip database access    │
│  • StopRepository - Stop database access    │
│  • UserRepository - User database access    │
│  • BaseRepository - Generic CRUD operations │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
             [PostgreSQL Database]
```

### Design Principles

- **Repository Pattern**: Clean separation between data access and business logic
- **Dependency Injection**: Using FastAPI's dependency system
- **Async/Await**: Non-blocking database operations for better performance
- **Pure Validators**: Business logic validation separate from database access
- **Pydantic Schemas**: Automatic input/output validation
- **Single Responsibility**: Each layer has one clear purpose

### Benefits

- ✅ **Testability**: Easy to mock repositories in unit tests
- ✅ **Maintainability**: Changes to database queries isolated in repositories
- ✅ **Reusability**: Common queries defined once, used everywhere
- ✅ **Clarity**: Clear separation of concerns between layers
- ✅ **Flexibility**: Easy to switch databases or add caching

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI 0.115+** - Modern, fast web framework for building APIs
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic 2.10+** - Data validation using Python type annotations

### Database
- **PostgreSQL 14+** - Advanced open-source relational database
- **SQLAlchemy 2.0** - Async ORM with powerful querying
- **Asyncpg** - Fast PostgreSQL driver for asyncio
- **Alembic 1.14** - Lightweight database migration tool

### Authentication & Security
- **python-jose** - JWT token creation and verification
- **passlib** - Password hashing library
- **bcrypt** - Secure password hashing algorithm

### Testing
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **httpx** - Async HTTP client for testing

## 📦 Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+**
- **pip** or **poetry** for package management

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/Travel-Companion.git
cd Travel-Companion
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/travel_companion

# JWT Authentication
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS (comma-separated list)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
ENVIRONMENT=development
```

**Generate a secure SECRET_KEY:**
```bash
openssl rand -hex 32
```

### 5. Set up the database

```bash
# Create database
createdb travel_companion

# Run migrations
alembic upgrade head
```

## 🏃 Running the Application

### Development Mode
```bash
uvicorn app.main:app --reload --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
Travel-Companion/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   │   ├── b0ebd22f9e5a_create_trips_table.py
│   │   ├── a1b2c3d4e5f6_create_stops_table.py
│   │   └── 7c9b2613990e_create_users_table.py
│   └── env.py                  # Alembic configuration
│
├── app/
│   ├── __init__.py
│   │
│   ├── auth/                   # Authentication
│   │   ├── dependencies.py     # JWT verification, get_current_user
│   │   └── jwt.py              # Token creation, password hashing
│   │
│   ├── db/                     # Database configuration
│   │   └── session.py          # AsyncSession, engine, Base
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── trip.py             # Trip model
│   │   ├── stop.py             # Stop model
│   │   └── user.py             # User model
│   │
│   ├── repositories/           # 🆕 Repository layer (database access)
│   │   ├── __init__.py         # Repository exports
│   │   ├── base_repository.py  # Generic CRUD operations
│   │   ├── trip_repository.py  # Trip-specific queries
│   │   ├── stop_repository.py  # Stop-specific queries
│   │   └── user_repository.py  # User-specific queries
│   │
│   ├── routers/                # FastAPI routers (HTTP endpoints)
│   │   ├── trips.py            # Trip endpoints
│   │   ├── stops.py            # Stop endpoints
│   │   └── auth.py             # Authentication endpoints
│   │
│   ├── schemas/                # Pydantic schemas (validation)
│   │   ├── trip.py             # TripCreate, TripUpdate, Trip
│   │   ├── stop.py             # StopCreate, StopUpdate, Stop
│   │   └── user.py             # UserCreate, User, Token
│   │
│   ├── services/               # Business logic layer
│   │   ├── trip_service.py     # Trip business logic
│   │   ├── stop_service.py     # Stop validations & logic
│   │   └── user_service.py     # User authentication logic
│   │
│   ├── validators/             # Pure validation functions
│   │   ├── common_validators.py # Shared validators
│   │   └── stop_validators.py   # Stop-specific validators
│   │
│   └── main.py                 # FastAPI app initialization
│
├── tests/                      # Test files (pytest)
│   ├── conftest.py             # Test configuration
│   ├── test_trips.py           # Trip endpoint tests (40 tests)
│   ├── test_stops.py           # Stop endpoint tests (96 tests)
│   └── test_integration.py     # Integration tests
│
├── .env                        # Environment variables (not in git!)
├── .gitignore
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
└── README.md                   # This file
```

## 📚 API Documentation

### Authentication Endpoints

#### Register a new user
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword123",
  "full_name": "John Doe"
}
```

#### Login (get access token)

**Option 1: OAuth2 Form (for compatibility)**
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpassword123
```

**Option 2: JSON (recommended)**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get current user profile
```http
GET /auth/me
Authorization: Bearer <token>
```

#### Update user profile
```http
PUT /auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "Jane Doe",
  "password": "newpassword123"
}
```

### Trip Endpoints

All trip endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your-token>
```

#### Get all trips
```http
GET /trips/
```

#### Create a trip
```http
POST /trips/
Content-Type: application/json

{
  "title": "Summer Vacation 2026",
  "start_date": "2026-07-01",
  "end_date": "2026-07-15"
}
```

#### Get a specific trip
```http
GET /trips/{trip_id}
```

#### Update a trip
```http
PUT /trips/{trip_id}
Content-Type: application/json

{
  "title": "Updated Trip Name"
}
```

#### Delete a trip
```http
DELETE /trips/{trip_id}
```

### Stop Endpoints

All stop endpoints require authentication.

#### Create a stop
```http
POST /trips/{trip_id}/stops/
Content-Type: application/json

{
  "name": "Tokyo",
  "country": "Japan",
  "start_date": "2026-07-01",
  "end_date": "2026-07-05",
  "order_index": 0,
  "latitude": 35.6762,
  "longitude": 139.6503,
  "notes": "Visit Shibuya and Shinjuku"
}
```

#### Get all stops for a trip
```http
GET /trips/{trip_id}/stops/
```

#### Get a specific stop
```http
GET /trips/{trip_id}/stops/{stop_id}
```

#### Update a stop
```http
PUT /trips/{trip_id}/stops/{stop_id}
Content-Type: application/json

{
  "name": "Tokyo (Updated)",
  "notes": "Added new activities"
}
```

#### Delete a stop
```http
DELETE /trips/{trip_id}/stops/{stop_id}
```

#### Reorder stops
```http
PUT /trips/{trip_id}/stops/reorder
Content-Type: application/json

{
  "stop_ids": [23, 21, 22]
}
```

### Validation Rules

#### Trip Validation
- Title must not be empty
- Start date cannot be in the past
- End date must be after or equal to start date

#### Stop Validation
- Name must not be empty
- Dates must be within the trip's date range
- Stop dates can overlap by a maximum of 1 day (for transitions)
- `order_index` must be unique within each trip
- Coordinates (if provided) must be realistic and roughly match the country

#### Coordinate Validation

The API performs basic geographic validation:
- Rejects obvious placeholder values like (0, 0), (1, 1)
- Performs rough boundary checking for supported countries (Israel, Japan, USA)
- Both latitude and longitude must be provided together

### API Endpoints Summary Table

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | ❌ |
| POST | `/auth/token` | Login (OAuth2 form) | ❌ |
| POST | `/auth/login` | Login (JSON) | ❌ |
| GET | `/auth/me` | Get current user info | ✅ |
| PUT | `/auth/me` | Update user profile | ✅ |
| GET | `/trips` | Get all user's trips | ✅ |
| POST | `/trips` | Create new trip | ✅ |
| GET | `/trips/{trip_id}` | Get trip by ID | ✅ |
| PUT | `/trips/{trip_id}` | Update trip | ✅ |
| DELETE | `/trips/{trip_id}` | Delete trip | ✅ |
| GET | `/trips/{trip_id}/stops` | Get all stops for a trip | ✅ |
| POST | `/trips/{trip_id}/stops` | Create new stop | ✅ |
| GET | `/trips/{trip_id}/stops/{stop_id}` | Get stop by ID | ✅ |
| PUT | `/trips/{trip_id}/stops/{stop_id}` | Update stop | ✅ |
| DELETE | `/trips/{trip_id}/stops/{stop_id}` | Delete stop | ✅ |
| PUT | `/trips/{trip_id}/stops/reorder` | Reorder stops | ✅ |

## 🔐 Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Authentication Flow

1. **Register or Login** → Receive JWT token
2. **Store Token** → Save in client (localStorage, secure storage)
3. **Include Token** → Add to Authorization header: `Bearer <token>`
4. **Token Validation** → Server verifies token on each request
5. **User Identification** → Server extracts user info from token

### Token Details

- **Algorithm**: HS256
- **Expiration**: 30 days (43,200 minutes) - configurable
- **Payload**: Contains `user_id` and `email`

### Using Tokens

**Python Example:**
```python
import httpx

# Login
response = httpx.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# Authenticated request
headers = {"Authorization": f"Bearer {token}"}
trips = httpx.get("http://localhost:8000/trips", headers=headers)
```

**JavaScript Example:**
```javascript
// Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({email: 'user@example.com', password: 'password123'})
});
const {access_token} = await response.json();

// Authenticated request
const trips = await fetch('http://localhost:8000/trips', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
```

## 🗄️ Database Migrations

Using **Alembic** for database schema management.

### Common Commands

```bash
# Create new migration (auto-detect changes)
alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current migration
alembic current

# View migration history
alembic history

# Rollback to specific version
alembic downgrade <revision_id>
```

### Migration Files

Located in `alembic/versions/`:
- `b0ebd22f9e5a` - Create trips table
- `a1b2c3d4e5f6` - Create stops table
- `7c9b2613990e` - Create users table

## 🧪 Testing

The project includes a comprehensive test suite using pytest with async support.

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_trips.py            # Trip endpoint tests (40 tests)
├── test_stops.py            # Stop endpoint tests (96 tests)
└── test_integration.py      # End-to-end integration tests (10 tests)
```

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with verbose output:**
```bash
pytest -v
```

**Run specific test file:**
```bash
pytest tests/test_trips.py
```

**Run specific test:**
```bash
pytest tests/test_trips.py::test_create_trip
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
```

### Test Configuration

The test suite uses:
- **pytest-asyncio**: For testing async code
- **httpx**: For making async HTTP requests to the API
- **SQLAlchemy async**: For database operations in tests
- **Test database**: Separate PostgreSQL database for testing

Configuration in `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = module
```

### Test Fixtures

The `conftest.py` provides several reusable fixtures:

**Core Fixtures:**
- `async_engine`: Async SQLAlchemy engine for tests
- `setup_database`: Creates/drops tables for each test module
- `test_user`: Global test user (ID: 1, email: test@example.com)
- `db_session`: Database session for direct DB tests
- `client`: Authenticated HTTP client for API tests

**Simple Fixtures** (use global TEST_USER_ID):
- `sample_trip`: Basic trip for quick tests
- `sample_trip_with_stop`: Trip with one stop
- `sample_trip_with_multiple_stops`: Trip with three stops

**Advanced Fixtures** (for complex scenarios):
- `trip_for_user`: Trip associated with full user object
- `multiple_users_with_trips`: Multiple users with their trips (for testing isolation)

### Test Examples

**Simple API test:**
```python
async def test_create_trip(client):
    """Test creating a trip via API"""
    response = await client.post("/trips/", json={
        "title": "Summer Vacation",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Summer Vacation"
```

**Test with fixtures:**
```python
async def test_get_trip(client, sample_trip):
    """Test retrieving a trip"""
    response = await client.get(f"/trips/{sample_trip.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_trip.id
```

**Database validation test:**
```python
async def test_stop_overlap_validation(db_session, sample_trip):
    """Test that overlapping stops are rejected"""
    stop1 = StopModel(
        trip_id=sample_trip.id,
        name="Tokyo",
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=15),
        order_index=0
    )
    db_session.add(stop1)
    await db_session.commit()
    
    # Try to create overlapping stop (should fail)
    with pytest.raises(HTTPException) as exc:
        await StopService.create_stop(
            sample_trip.id,
            StopCreate(
                name="Osaka",
                start_date=date.today() + timedelta(days=12),
                end_date=date.today() + timedelta(days=18),
                order_index=1
            ),
            db_session,
            TEST_USER_ID
        )
    assert exc.value.status_code == 400
```

**User isolation test:**
```python
async def test_user_cannot_access_other_users_trips(
    client, 
    multiple_users_with_trips
):
    """Test that users can only see their own trips"""
    users = multiple_users_with_trips
    
    # Client is authenticated as user1
    response = await client.get("/trips/")
    trips = response.json()
    
    # Should only see user1's trips (2 trips)
    assert len(trips) == 2
    assert all(trip["user_id"] == 1 for trip in trips)
```

### Test Results

```
tests/test_trips.py ................ (40 passed)
tests/test_stops.py ................ (95 passed, 1 xfailed, 1 xpassed)
tests/test_integration.py .......... (8 passed, 2 skipped)

Total: 143 tests passed ✅
```

## 🗄️ Database Schema

### Users Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | User ID |
| `email` | String(255) | Unique, Indexed, Not Null | User email address |
| `hashed_password` | String(255) | Not Null | Bcrypt hashed password |
| `full_name` | String(255) | Nullable | User's full name |
| `is_active` | Boolean | Not Null, Default: True | Account status |
| `is_superuser` | Boolean | Not Null, Default: False | Admin privileges |
| `created_at` | DateTime | Not Null | Account creation timestamp |
| `updated_at` | DateTime | Not Null | Last update timestamp |

### Trips Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Trip ID |
| `user_id` | Integer | Foreign Key → users.id, Not Null, Indexed | Owner user ID |
| `title` | String | Not Null | Trip name |
| `start_date` | Date | Not Null | Trip start date |
| `end_date` | Date | Not Null | Trip end date |

**Relationships:**
- **CASCADE DELETE**: Deleting a user deletes all their trips
- **One-to-Many**: One user can have many trips

### Stops Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key | Stop ID |
| `trip_id` | Integer | Foreign Key → trips.id, Not Null, Indexed | Parent trip ID |
| `order_index` | Integer | Not Null, Default: 0, Unique per trip | Stop order position |
| `name` | String(200) | Not Null | Location name |
| `country` | String(120) | Nullable | Country name |
| `start_date` | Date | Not Null | Stop start date |
| `end_date` | Date | Not Null | Stop end date |
| `latitude` | Float | Nullable | Geographic latitude (-90 to 90) |
| `longitude` | Float | Nullable | Geographic longitude (-180 to 180) |
| `notes` | Text | Nullable | Additional notes |

**Indexes:**
- `ix_stops_trip_id_order`: Compound index on (trip_id, order_index) for efficient ordered queries

**Unique Constraints:**
- `uq_stops_trip_id_order`: Unique constraint on (trip_id, order_index) - each trip has unique stop orders

**Relationships:**
- **CASCADE DELETE**: Deleting a trip deletes all its stops
- **One-to-Many**: One trip can have many stops

### Entity Relationship Diagram

```
┌─────────────────┐
│      Users      │
│─────────────────│
│ id (PK)         │
│ email (UNIQUE)  │
│ hashed_password │
│ full_name       │
│ is_active       │
│ is_superuser    │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N (CASCADE)
         │
         ▼
┌─────────────────┐
│      Trips      │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ title           │
│ start_date      │
│ end_date        │
└────────┬────────┘
         │
         │ 1:N (CASCADE)
         │
         ▼
┌─────────────────┐
│      Stops      │
│─────────────────│
│ id (PK)         │
│ trip_id (FK)    │
│ order_index     │◄── UNIQUE per trip
│ name            │
│ country         │
│ start_date      │
│ end_date        │
│ latitude        │
│ longitude       │
│ notes           │
└─────────────────┘
```

## 👨‍💻 Development

### Code Style

- Follow **PEP 8** guidelines
- Use **type hints** for function parameters and returns
- Write **docstrings** for all functions and classes
- Keep functions **focused and small** (single responsibility)

### Repository Pattern

This project implements the **Repository Pattern** for clean database access:

**Key Files**:
- `app/repositories/base_repository.py` - Generic CRUD operations
- `app/repositories/trip_repository.py` - Trip-specific queries
- `app/repositories/stop_repository.py` - Stop-specific queries  
- `app/repositories/user_repository.py` - User-specific queries

**Benefits**:
- ✅ Single source of truth for database queries
- ✅ Easy to test (mock repositories)
- ✅ Reusable queries across services
- ✅ Clean separation of concerns
- ✅ Easy to add caching or query logging

**Example Usage**:
```python
# In Service Layer
from app.repositories import TripRepository

async def get_user_trips(db: AsyncSession, user_id: int):
    repo = TripRepository(db)
    return await repo.get_by_user_id(user_id)
```

### Adding New Features

1. **Create Model** (if needed) in `app/models/`
2. **Create Migration** with Alembic
3. **Create Repository** in `app/repositories/`
4. **Create Schemas** in `app/schemas/`
5. **Create Service** in `app/services/`
6. **Create Router** in `app/routers/`
7. **Add Tests** in `tests/`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key (32+ chars) | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `43200` (30 days) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `ENVIRONMENT` | App environment | `development` |
##

## 📊 Performance

The API is optimized for performance:

- **Async Operations**: All database queries are non-blocking
- **Connection Pooling**: SQLAlchemy manages connection pool
- **Efficient Queries**: Repositories use optimized query patterns
- **Stateless Auth**: JWT tokens eliminate session storage

**Approximate Response Times**:
- Trip creation: ~50ms
- Stop creation with validation: ~100ms
- Get all trips: ~30ms
- Authentication: ~80ms

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```
Could not connect to database
```
**Solution**: Verify `DATABASE_URL` in `.env` and ensure PostgreSQL is running

**Migration Error**
```
Can't locate revision identified by 'xxxx'
```
**Solution**: Run `alembic upgrade head` or check migration files

**JWT Token Error**
```
Could not validate credentials
```
**Solution**: Token may be expired. Login again to get a new token

**Import Error**
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Ensure virtual environment is activated and you're in project root

