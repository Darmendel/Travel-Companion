# Travel Planning API

A FastAPI-based REST API for planning trips with multiple stops, featuring user authentication, trip management, and intelligent stop validation.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Trip Management**: Create, read, update, and delete trips with date validation
- **Stop Management**: Add multiple stops to trips with automatic validation
- **Smart Validations**:
  - Date overlap detection (allows 1-day transitions)
  - Geographic coordinate validation
  - Automatic date range checking
  - Stop reordering with constraint handling
- **User Isolation**: Each user can only access their own trips and stops
- **Async Architecture**: Built with modern async/await patterns for better performance

## Tech Stack

- **Framework**: FastAPI 
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Python**: 3.10+

## Project Structure

```
Travel-Companion/
├── alembic/
│   ├── versions/
│   │   ├── b0ebd22f9e5a_create_trips_table.py
│   │   ├── a1b2c3d4e5f6_create_stops_table.py
│   │   └── 7c9b2613990e_create_users_table.py
│   ├── env.py               # Alembic async configuration
│   └── README               # Alembic documentation
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── dependencies.py  # Authentication dependencies (get_current_user, etc.)
│   │   └── jwt.py           # JWT token creation and verification
│   ├── db/
│   │   ├── __init__.py
│   │   ├── config.py        # Database configuration
│   │   ├── session.py       # Database session management
│   │   └── fake_db.py       # Fake DB for testing (if needed)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── trip.py          # Trip SQLAlchemy model
│   │   ├── stop.py          # Stop SQLAlchemy model
│   │   └── user.py          # User SQLAlchemy model
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── trips.py         # Trip CRUD endpoints
│   │   └── stops.py         # Stop CRUD endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── trip.py          # Trip Pydantic schemas
│   │   ├── stop.py          # Stop Pydantic schemas
│   │   └── user.py          # User Pydantic schemas
│   ├── services/
│   │   ├── trip_service.py  # Trip business logic
│   │   ├── stop_service.py  # Stop business logic
│   │   └── user_service.py  # User business logic
│   ├── validators/
│   │   ├── common_validators.py # Shared validation functions
│   │   └── stop_validators.py   # Stop-specific validators
│   └── main.py              # Application entry point
├── tests/
│   ├── fake_db_tests/
│   │   └── conftest_fake_db.py  # Fake DB test configuration
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── test_integration.py  # Integration tests
│   ├── test_stops.py        # Stop endpoint tests
│   └── test_trips.py        # Trip endpoint tests
├── .env                     # Environment variables (not in git)
├── .gitignore              # Git ignore file
├── .python-version         # Python version specification
├── alembic.ini             # Alembic configuration
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- pip or poetry for dependency management

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travel-planning-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn sqlalchemy asyncpg alembic python-dotenv \
               python-jose[cryptography] passlib[bcrypt] python-multipart
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/travel_db
   
   # JWT Configuration
   SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days
   
   # CORS (comma-separated origins)
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   
   # Environment
   ENVIRONMENT=development  # or production
   ```

5. **Initialize the database**
   ```bash
   # Create database tables using Alembic
   alembic upgrade head
   ```

### Running the Application

**Development mode** (with auto-reload):
```bash
uvicorn app.main:app --reload --port 8000
```

**Production mode**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Documentation

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
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpassword123
```

Or use JSON endpoint:
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

Response:
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

## Validation Rules

### Trip Validation
- Title must not be empty
- Start date cannot be in the past
- End date must be after or equal to start date

### Stop Validation
- Name must not be empty
- Dates must be within the trip's date range
- Stop dates can overlap by a maximum of 1 day (for transitions)
- `order_index` must be unique within each trip
- Coordinates (if provided) must be realistic and roughly match the country

### Coordinate Validation
The API performs basic geographic validation:
- Rejects obvious placeholder values like (0, 0), (1, 1)
- Performs rough boundary checking for supported countries (Israel, Japan, USA)
- Both latitude and longitude must be provided together

## Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique, indexed
- `hashed_password`: Bcrypt hash
- `full_name`: Optional
- `is_active`: Boolean
- `is_superuser`: Boolean
- `created_at`, `updated_at`: Timestamps

### Trips Table
- `id`: Primary key
- `user_id`: Foreign key to users (CASCADE delete)
- `title`: Trip name
- `start_date`, `end_date`: Date range

### Stops Table
- `id`: Primary key
- `trip_id`: Foreign key to trips (CASCADE delete)
- `order_index`: Order within trip (unique per trip)
- `name`, `country`: Location info
- `start_date`, `end_date`: Date range
- `latitude`, `longitude`: Optional coordinates
- `notes`: Optional text

## Database Migrations

The project uses Alembic for database migrations with async support.

### Migration Files

Current migrations (in order):
1. **b0ebd22f9e5a** - Create trips table
2. **a1b2c3d4e5f6** - Create stops table
3. **7c9b2613990e** - Create users table and add foreign keys

### Migration Commands

Create a new migration after model changes:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply all pending migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

Show current migration version:
```bash
alembic current
```

Show migration history:
```bash
alembic history
```

### Async Migration Configuration

The project uses async SQLAlchemy with Alembic. The `alembic/env.py` is configured to:
- Use async engine from `app.db.session`
- Import all models automatically
- Support both online and offline migration modes
- Handle asyncpg connections properly

Key configuration in `alembic/env.py`:
```python
from app.db.session import Base, DATABASE_URL
from app.models.trip import Trip
from app.models.stop import Stop
from app.models.user import User

target_metadata = Base.metadata
```

### Example: Creating a New Migration

```bash
# 1. Modify your SQLAlchemy model
# 2. Generate migration
alembic revision --autogenerate -m "add column to trips"

# 3. Review the generated file in alembic/versions/
# 4. Test the migration
alembic upgrade head

# 5. Test rollback
alembic downgrade -1

# 6. Apply again
alembic upgrade head
```

## Architecture Patterns

### Layered Architecture
- **Routers**: Handle HTTP requests/responses, dependency injection
- **Services**: Business logic, database operations, orchestration
- **Validators**: Pure validation functions (no DB access)
- **Schemas**: Pydantic models for request/response validation
- **Models**: SQLAlchemy ORM models

### Key Design Decisions

1. **Service Layer**: Separates business logic from HTTP concerns
2. **Pure Validators**: Testable validation functions without side effects
3. **Async Throughout**: Leverages async/await for better concurrency
4. **User Isolation**: All queries filtered by `user_id` for security
5. **Two-Phase Updates**: Handles unique constraint violations during reordering

## Security Features

- **Password Hashing**: Bcrypt with automatic salt generation
- **JWT Tokens**: Secure token-based authentication
- **User Isolation**: Users can only access their own data
- **Active User Check**: Inactive accounts cannot access the API
- **CORS Protection**: Configurable allowed origins
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy

## Testing

The project includes a comprehensive test suite using pytest with async support.

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_trips.py            # Trip endpoint tests
├── test_stops.py            # Stop endpoint tests
└── test_integration.py      # End-to-end integration tests
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

#### Core Fixtures

- **`async_engine`**: Async SQLAlchemy engine for tests
- **`setup_database`**: Creates/drops tables for each test module
- **`test_user`**: Global test user (ID: 1, email: test@example.com)
- **`db_session`**: Database session for direct DB tests
- **`client`**: Authenticated HTTP client for API tests

#### Simple Fixtures (use global TEST_USER_ID)

- **`sample_trip`**: Basic trip for quick tests
- **`sample_trip_with_stop`**: Trip with one stop
- **`sample_trip_with_multiple_stops`**: Trip with three stops

#### Advanced Fixtures (for complex scenarios)

- **`trip_for_user`**: Trip associated with full user object
- **`multiple_users_with_trips`**: Multiple users with their trips (for testing isolation)

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

### Test Database Setup

The tests use a separate PostgreSQL database defined in `conftest.py`:

```python
TEST_DB_URL = "postgresql+asyncpg://user:password@localhost:5432/test_db"
```

**Create test database:**
```sql
CREATE DATABASE test_db;
```

The test suite automatically:
1. Creates all tables before each test module
2. Creates a test user (ID: 1, email: test@example.com)
3. Cleans up data between tests
4. Drops all tables after test module completes

### Fixture Usage Guide

**When to use each fixture:**

| Use Case | Fixture | Why |
|----------|---------|-----|
| API endpoint test | `client` | Authenticated HTTP client |
| Quick trip test | `sample_trip` | Simple, uses global user |
| Test with stop | `sample_trip_with_stop` | Includes one stop |
| Reordering test | `sample_trip_with_multiple_stops` | Three stops ready |
| Need user details | `trip_for_user`, `test_user` | Access to user object |
| Test user isolation | `multiple_users_with_trips` | Two users with trips |
| Direct DB operation | `db_session` | Raw database access |

## Testing

## Production Deployment

### Environment Variables for Production
```env
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@prod-host:5432/travel_db
SECRET_KEY=<generate-strong-key>
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Deployment Checklist
- [ ] Set strong `SECRET_KEY`
- [ ] Configure specific CORS origins (not `*`)
- [ ] Use environment-based configuration
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Use HTTPS in production
- [ ] Configure rate limiting
- [ ] Set up database connection pooling

### Docker Deployment (Example)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
