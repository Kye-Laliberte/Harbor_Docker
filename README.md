# Harbor Management app

A robust FastAPI-based REST API for managing comprehensive harbor operations, including ships, docks, voyages, and docking procedures with full timezone awareness and cargo management.

## 📋 Project Overview

This application provides a complete harbor management system designed to handle:
- **Ship Management**: Track vessel inventory, cargo capacity, and operational status
- **Harbor Operations**: Manage multiple ports with timezone-aware logistics
- **Dock Management**: Handle individual berthing locations with size and capacity constraints
- **Docking Procedures**: Record and validate ship arrivals/departures with clearance tracking
- **Voyage Planning**: Schedule and track inter-harbor shipping routes

## 🛠 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy |
| **Database** | PostgreSQL (with timezone support) |
| **Migrations** | Alembic |
| **Containerization** | Docker & Docker Compose |
| **Language** | Python 3.8+ |
| **Validation** | Pydantic v2 |

## 📁 Project Structure

```
Docker-api/
├── app/                              # Main application package
│   ├── core/
│   │   └── config.py                # Configuration & environment variables
│   ├── routes/                      # API endpoints (routers)
│   │   ├── ships.py                 # Ship CRUD operations
│   │   ├── docks.py                 # Dock management
│   │   ├── harbors.py               # Harbor operations
│   │   ├── dockings.py              # Docking workflow
│   │   └── voyages.py               # Voyage management
│   ├── services/                    # Business logic layer
│   │   ├── ship_service.py          # Ship operations & validation
│   │   ├── dock_service.py          # Dock operations
│   │   ├── docking_service.py       # Docking logic & overlap detection
│   │   ├── harbor_service.py        # Harbor operations
│   │   └── voyage_service.py        # Voyage CRUD & workflow
│   ├── models.py                    # SQLAlchemy ORM model definitions
│   ├── schemas.py                   # Pydantic validation schemas
│   ├── enums.py                     # Application enumerations
│   ├── database.py                  # Database connection & session management
│   ├── dependencies.py              # FastAPI dependencies
│   └── main.py                      # Application entry point
├── alembic/                         # Database migrations
│   ├── versions/                    # Migration version scripts
│   ├── env.py                       # Alembic environment configuration
│   └── script.py.mako               # Migration template
├── sql/
│   └── schema.sql                   # Initial database schema
├── tests/                           # Test suite
│   ├── test_endpoints.py            # Endpoint integration tests
│   ├── test_docking_voyage_flow.py  # Workflow integration tests
│   └── test_voyage_service.py       # Service-level tests
├── Dockerfile                       # Container image definition
├── docker-compose.yml               # Multi-container orchestration
├── alembic.ini                      # Alembic configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🏗 Core Domain Models

### Ship
- **Unique Identifier**: `registration_number`
- **Capacity Management**: `cargo_capacity`, `current_cargo` (with validation)
- **Classification**: `ship_size` (1=SMALL, 2=MEDIUM, 3=LARGE)
- **Status Tracking**: DOCKED, SAILING, MAINTENANCE
- **Relationships**: Associated voyages and docking records

### Harbor
- **Location**: Name and timezone identifier (e.g., "UTC", "America/New_York")
- **Coordinates**: Optional latitude and longitude for route-distance calculations; both are required before creating a voyage
- **Infrastructure**: Multiple docks per harbor
- **Voyage Relationships**: Departure and destination points
- **Timezone Handling**: All operations respect harbor-specific timezones

### Dock
- **Unique Identifier**: `dock_code`
- **Constraints**:
  - Size compatibility: `dock_size >= ship_size`
  - Cargo limit: `cargo_capacity` must accommodate ship's current cargo
- **Status**: ACTIVE (available), INACTIVE (occupied), MAINTENANCE
- **Harbor Assignment**: Each dock belongs to one harbor

### Docking
- **Purpose**: Records a ship's arrival and departure at a dock
- **Dates**: 
  - `arrival_date`: When ship arrived (required)
  - `departure_date`: When ship departed (optional, for active dockings)
- **Clearance**: PENDING → APPROVED → DENIED workflow
- **Validation**: No overlapping docking windows for same ship or dock

### Voyage
- **Route**: Departure harbor → Destination harbor
- **Schedule**:
  - `departure_date`: When ship leaves
  - `estimated_arrival`: Expected arrival time
  - `arrival_date`: Actual arrival (null until completed)
- **Status**: SCHEDULED, DEPARTED, ARRIVED, CANCELLED
- **Business Rules**: Ship must be DOCKED to start voyage

### Voyage and Docking Lifecycle

1. Create a pending docking with `POST /dockings/create`.
2. Approve it with `POST /dockings/{docking_id}/approve`.
3. Enter the ship into the dock with `PUT /dockings/{docking_id}/arrive/`.
4. Create a scheduled voyage with `POST /voyages/create`.
5. Approve it with `POST /voyages/{voyage_id}/approve`.
6. Release the ship with `POST /voyages/{voyage_id}/leave_dock`.
7. Record arrival with `POST /voyages/{voyage_id}/arrive`; the completed voyage becomes ML training data.

Voyage statuses are `scheduled -> approved -> departed -> arrived`. Docking clearance is `pending -> approved`, and entering the dock changes the ship to `DOCKED` and the dock to `INACTIVE`.
- **Estimated Arrival**: Calculated from harbor distance and learned ship speed; clients may omit `estimated_arrival`

## Travel-Time Learning

Completed voyages are supervised training samples. When `POST /voyages/{voyage_id}/arrive` records an actual arrival, the API adds that voyage's observed distance-over-time speed to the training set. New predictions use a linear regression over route distance, vessel size, and ship identity. Known ships receive a learned ship-specific effect; unseen ships fall back to the shared distance-and-size model. The model is calculated from voyage history and is not persisted on the `ships` table. Harbor coordinates are stored in `latitude` and `longitude`.

## 📊 Enumerations Reference

### DockStatus
```
ACTIVE      → Dock is operational and accepting new dockings
INACTIVE    → Dock is occupied or temporarily unavailable
MAINTENANCE → Dock undergoing maintenance
```

### ShipStatus
```
DOCKED      → Ship is moored at a dock
SAILING     → Ship is in transit between harbors
MAINTENANCE → Ship undergoing repairs/maintenance
```

### ShipClearanceStatus
```
PENDING     → Clearance request submitted
APPROVED    → Ship approved to depart
DENIED      → Departure denied
```

### VoyageStatus
```
SCHEDULED   → Voyage planned but not yet departed
DEPARTED    → Ship has left departure harbor
ARRIVED     → Ship reached destination
CANCELLED   → Voyage was cancelled
```

### VesselSize (Dock/Ship Compatibility)
```
1 = SMALL    → Smaller vessels (fishing boats, tugs)
2 = MEDIUM   → Standard cargo ships
3 = LARGE    → Large container ships, tankers
```

Dock must be large enough to accommodate ship: `dock_size >= ship_size`

## 🔌 API Endpoints

### Ships (`/ships`)
```
GET    /ships/list                      List all ships (paginated)
POST   /ships/new                       Create new ship
GET    /ships/{ship_id}/get             Get ship details
PUT    /ships/{ship_id}/update          Update ship information
DELETE /ships/{ship_id}/delete          Delete ship
```

### Harbors (`/harbors`)
```
GET    /harbors/list                    List all harbors
POST   /harbors/new                     Create harbor
GET    /harbors/{harbor_id}/get         Get harbor details
PUT    /harbors/{harbor_id}/update      Update harbor
DELETE /harbors/{harbor_id}/delete      Delete harbor
```

### Docks (`/docks`)
```
GET    /docks/list                      List all docks
POST   /docks/new                       Create dock
GET    /docks/{dock_id}/get             Get dock details
PUT    /docks/{dock_id}/update          Update dock
DELETE /docks/{dock_id}/delete          Delete dock
```

### Dockings (`/dockings`)
```
GET    /dockings/list                   List all dockings (paginated)
POST   /dockings/create                 Create new docking
GET    /dockings/{docking_id}/get       Get docking details
PUT    /dockings/{docking_id}/arrive    Mark ship arrived & update statuses
DELETE /dockings/{docking_id}/delete    Delete docking
```

### Voyages (`/voyages`)
```
GET    /voyages/list                    List all voyages (paginated)
POST   /voyages/new                     Create voyage
GET    /voyages/{voyage_id}/get         Get voyage details
PUT    /voyages/{voyage_id}/update      Update voyage
DELETE /voyages/{voyage_id}/delete      Delete voyage
```

Prediction endpoint:

```text
GET /voyages/predict?ship_id=1&departure_harbor_id=1&destination_harbor_id=2
```

The response contains predicted ship speed in km/h, route distance in km, and average voyage time in hours. Completed voyages recorded through `POST /voyages/{voyage_id}/arrive` provide the supervised training samples. Before valid training data exists, `model_trained` is `false` and the API uses a 20 km/h cold-start baseline.

## ⚙️ Business Rules & Constraints

### Docking Validation Rules
1. **Ship Status**: Only SAILING ships can dock (except initial docking)
2. **Dock Status**: Only ACTIVE docks accept new dockings
3. **Size Compatibility**: `dock_size >= ship_size` required
4. **Cargo Capacity**: Dock must accommodate ship's current cargo load
5. **No Overlaps**: Ship and dock cannot have concurrent dockings
6. **Date Ordering**: Departure date must be after arrival date
7. **Voyage Conflict**: No pending/in-progress voyages during docking

### Voyage Business Rules
1. **Ship Status**: Ship must be DOCKED to start voyage
2. **Active Docking**: Ship must have active docking (no departure_date) at departure harbor
3. **Harbor Validation**: Both departure and destination harbors must exist
4. **Date Ordering**: Estimated arrival > departure date
5. **Harbor Matching**: Docking must be at departure harbor

### Cargo Management
1. **Current Cargo Constraint**: `current_cargo <= cargo_capacity` for ships
2. **Dock Capacity**: Dock must accept ship's current cargo
3. **Validation Level**: Enforced at both Pydantic schema and database model levels

### Database Constraints
- `ck_ship_current_cargo`: current_cargo >= 0
- `ck_ship_cargo_capacity`: cargo_capacity >= 0
- `ck_available_cargo`: current_cargo <= cargo_capacity
- `ck_dock_size`: dock_size IN (1, 2, 3)
- `ck_departure_after_arrival`: departure_date IS NULL OR departure_date > arrival_date
- `ck_arival_order_check`: departure_date <= estimated_arrival

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose (recommended)
- PostgreSQL 12+ (if running locally)
- Python 3.8+ (for local development)

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd Docker-api

# Start services (PostgreSQL + FastAPI)
docker-compose up -d

# Run database migrations
docker-compose exec web alembic upgrade head

# Check if running
curl http://localhost:8000/docs
```

**Services:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs (Swagger UI)
- Alternative Docs: http://localhost:8000/redoc (ReDoc)
- PostgreSQL: localhost:5432

### Option 2: Local Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
# Create .env file with:
# DATABASE_URL=postgresql://user:password@localhost:5432/harbor_db
# SQLALCHEMY_ECHO=True

# Create database
createdb harbor_db  # or via PostgreSQL admin tool

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🗄️ Database Migrations

Migrations are version-controlled in `alembic/versions/` directory.

### Key Migrations
- Initial schema setup
- Enum types creation
- Constraint additions
- Timestamp timezone conversions
- Schema refinements

### Create a New Migration
```bash
# After modifying models.py
alembic revision --autogenerate -m "description of changes"

# Review generated migration in alembic/versions/
# Then apply:
alembic upgrade head
```

### Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

## 🧪 Testing not yet added.

Test suite is located in `tests/` directory:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_endpoints.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Files not yet set up
- `test_endpoints.py`: API endpoint integration tests
- `test_docking_voyage_flow.py`: Complex workflow scenarios
- `test_voyage_service.py`: Service-level business logic tests

## 📝 Configuration

### Environment Variables (app/core/config.py)
```
DATABASE_URL          # PostgreSQL connection string
                      # Format: postgresql://user:password@host:port/database
SQLALCHEMY_ECHO       # Enable SQL logging (default: True)
```

### Example .env File
```
DATABASE_URL=postgresql://harbor_user:secure_password@localhost:5432/harbor_db
SQLALCHEMY_ECHO=False
```

## 🔍 Error Handling

The API returns standard HTTP status codes:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK - Success | GET request successful |
| 201 | Created - Resource created | POST successful |
| 204 | No Content - Deleted successfully | DELETE successful |
| 400 | Bad Request - Validation/business rule violation | Invalid cargo, overlapping dock |
| 404 | Not Found - Resource doesn't exist | Ship ID not found |
| 500 | Server Error - Unexpected error | Database connection failed |

### Common Error Responses
```json
{
  "detail": "Ship is not sailing (current status: docked)"
}
```

## 🔐 Timezone Handling

The API is timezone-aware:

```python
# Harbor timezone (stored as string identifier)
harbor.timezone = "America/New_York"  # Timezone name

# Event timestamps (always stored as TIMESTAMP with timezone)
docking.arrival_date = datetime.now(timezone.utc)  # UTC-aware
voyage.departure_date = datetime.now(timezone.utc)  # UTC-aware
```

This allows:
- Accurate event tracking across time zones
- Proper voyage scheduling across harbors
- Timezone-aware queries and reporting

## 🐳 Docker Compose Services

### PostgreSQL Service
- **Image**: postgres:15
- **Port**: 5432
- **Database**: harbor_db
- **Volumes**: Persisted to `postgres_data/`
- **Initialization**: Runs schema.sql on first start

### Web Service (FastAPI)
- **Image**: Built from Dockerfile
- **Port**: 8000
- **Dependencies**: PostgreSQL must be healthy
- **Auto-reload**: Enabled for development

### Volumes
- `postgres_data/`: PostgreSQL data persistence
- `./alembic/`: Migration scripts mounted

## 📈 Scalability & Performance

### Indexing Strategy
- Primary keys indexed automatically
- Foreign keys indexed for join performance
- Consider adding indexes on frequently queried fields:
  - `ships.registration_number`
  - `docks.dock_code`
  - `dockings.ship_id`, `dockings.dock_id`
  - `voyages.ship_id`

### Pagination
All list endpoints support pagination:
```
GET /ships/list?skip=0&limit=100
GET /dockings/list?skip=20&limit=50
```

## 🚧 Future Enhancements

- [ ] Authentication & Authorization (JWT tokens)
- [ ] Role-based access control (Captain, Harbor Master, Admin)
- [ ] Rate limiting per user/IP
- [ ] WebSocket support for real-time updates
- [ ] Advanced voyage planning with route optimization
- [ ] Cargo manifest tracking
- [ ] cargo load and unload 
- [ ] Weather integration for voyage safety
- [ ] Cost tracking and billing
- [ ] Audit logging for compliance
- [ ] GraphQL API alongside REST
- [ ] Mobile app support

## 🐛 Known Issues

All identified bugs have been fixed. See commit history for details.


## 💬 Support

For issues, questions, or feature requests:
1. Check existing issues in repository
2. Review test cases in `tests/`
3. Check API documentation at `/docs` endpoint
4. Open a new issue with detailed description

## 🤝 Contributing

1. Create feature branch from `main`
2. Make changes and add tests
3. Run tests: `pytest tests/`
4. Create pull request with description

---
**Last Updated**: 2026-09-17  
**API Version**: 1.0  
**Python Version**: 3.8+  
**Database**: PostgreSQL 12+
