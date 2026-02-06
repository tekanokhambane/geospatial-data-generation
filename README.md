# Geospatial Data Generation API

A FastAPI-based REST API for searching locations within a specified radius using geospatial data stored in PostgreSQL with PostGIS.

## Table of Contents

- [Design Choices](#design-choices)
- [Database Schema](#database-schema)
- [Assumptions](#assumptions)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Environment Variables](#environment-variables)

---

## Design Choices

### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Web Framework** | FastAPI | High performance, automatic OpenAPI documentation, async support, and type validation with Pydantic |
| **ORM** | SQLAlchemy | Mature, well-documented ORM with excellent PostgreSQL support |
| **Database** | PostgreSQL + PostGIS | Industry-standard for geospatial data; PostGIS provides optimized spatial queries and indexing |
| **Containerization** | Docker Compose | Simplifies deployment, ensures consistency across environments, and manages service dependencies |

### Architecture Decisions

1. **Haversine Formula for Distance Calculation**: Used to calculate the great-circle distance between two points on Earth, providing accurate distance measurements for geospatial queries.

2. **Reverse Geocoding**: Integrated Google Maps API to convert coordinates to human-readable addresses during data ingestion. Falls back gracefully if the API is unavailable.

3. **Health Checks**: Docker Compose uses PostgreSQL health checks to ensure the database is ready before starting the application.

4. **Data Ingestion at Startup**: The entrypoint script runs data ingestion automatically when the container starts, ensuring the database is populated with sample data.

5. **PostGIS Geography Type**: Uses `GEOGRAPHY(POINT, 4326)` for storing coordinates, which provides accurate distance calculations on a spherical Earth model using the WGS 84 coordinate system.

---

## Database Schema

### Table: `locations_data`

| Column    | Type                    | Constraints | Description                                      |
|-----------|-------------------------|-------------|--------------------------------------------------|
| id        | UUID                    | PRIMARY KEY | Unique identifier for each location              |
| timestamp | TIMESTAMP               |             | When the transaction/event occurred              |
| latitude  | DOUBLE PRECISION        |             | Geographic latitude coordinate                   |
| longitude | DOUBLE PRECISION        |             | Geographic longitude coordinate                  |
| address   | TEXT                    |             | Human-readable address (reverse geocoded)        |
| geom      | GEOGRAPHY(POINT, 4326)  |             | PostGIS geometry for spatial queries             |

### Extensions

- **PostGIS**: Enabled for geospatial functionality (`CREATE EXTENSION IF NOT EXISTS postgis`)

### SQLAlchemy Model

```python
class Location(Base):
    __tablename__ = "locations_data"
    
    id = Column(String, primary_key=True, index=True)
    address = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
```

---

## Assumptions

1. **Input Data Format**: The `transactions.csv` file contains columns: `id`, `timestamp`, `latitude`, `longitude`

2. **Coordinate System**: All coordinates use WGS 84 (EPSG:4326), the standard GPS coordinate system

3. **Search Radius**: The default search radius of 1000 meters is suitable for most urban location searches

4. **Google API Key**: A valid Google Maps API key is required for reverse geocoding; if unavailable, addresses will be stored as `NULL`

5. **Single Instance**: The application is designed for single-instance deployment; horizontal scaling would require additional configuration

6. **Data Volume**: The Haversine calculation is performed in Python for simplicity; for large datasets, PostGIS spatial queries (`ST_DWithin`) should be used for better performance

---

## Getting Started

### Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)
- Google Maps API Key (optional, for reverse geocoding)

### Step-by-Step Instructions

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd geospatial-data-generation
```

#### Step 2: Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=locations_db

# Port Configuration
DB_PORT=5431
APP_PORT=8000

# Google API Key (required for reverse geocoding in ingestion)
GOOGLE_API_KEY=your_google_api_key_here
```

#### Step 3: Build and Run with Docker Compose

```bash
docker-compose up --build
```

This single command will:

1. **Build the application image** - Installs Python dependencies and copies application code
2. **Start PostgreSQL with PostGIS** - Initializes the database with geospatial extensions
3. **Wait for database readiness** - Health checks ensure the database is accepting connections
4. **Run data ingestion** - Automatically executes `scripts/ingestion.py` which:
   - Creates the `locations_data` table with PostGIS geometry column
   - Reads `transactions.csv`
   - Reverse geocodes coordinates to addresses (if Google API key is provided)
   - Inserts all data into the database
5. **Start the FastAPI server** - Application becomes available on port 8000

#### Step 4: Verify the Application

Check if the application is running:

```bash
curl http://localhost:8000/docs
```

This should open the Swagger UI documentation.

#### Step 5: Test the API

```bash
curl "http://localhost:8000/locations/search?lat=-26.2041&lon=28.0473&radius=5000"
```

### Stopping the Application

```bash
docker-compose down
```

To also remove the database volume (all data will be lost):

```bash
docker-compose down -v
```

### Rebuilding After Code Changes

```bash
docker-compose down
docker-compose up --build
```

---

## API Documentation

### Interactive Documentation

When the application is running, access the interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### Search Locations

Search for locations within a specified radius from a center point.

```
GET /locations/search
```

**Query Parameters:**

| Parameter | Type  | Required | Default | Description                              |
|-----------|-------|----------|---------|------------------------------------------|
| `lat`     | float | Yes      | -       | Latitude of the center point (-90 to 90) |
| `lon`     | float | Yes      | -       | Longitude of the center point (-180 to 180) |
| `radius`  | float | No       | 1000    | Search radius in meters                  |

**Response Schema:**

```json
[
  {
    "id": "string (UUID)",
    "address": "string",
    "latitude": "number (float)",
    "longitude": "number (float)"
  }
]
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/locations/search?lat=-26.2041&lon=28.0473&radius=5000"
```

**Example Response (200 OK):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "address": "123 Main St, Johannesburg, South Africa",
    "latitude": -26.2041,
    "longitude": 28.0473
  },
  {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "address": "456 Park Ave, Johannesburg, South Africa",
    "latitude": -26.2050,
    "longitude": 28.0480
  }
]
```

**Error Response (404 Not Found):**

```json
{
  "detail": "No locations found within the specified radius"
}
```

**Response Codes:**

| Code | Description                                    |
|------|------------------------------------------------|
| 200  | Success - Returns array of locations           |
| 404  | No locations found within the specified radius |
| 422  | Validation error - Invalid query parameters    |

---

## Environment Variables

| Variable          | Required | Default      | Description                                |
|-------------------|----------|--------------|--------------------------------------------|
| POSTGRES_USER     | No       | postgres     | PostgreSQL username                        |
| POSTGRES_PASSWORD | Yes      | -            | PostgreSQL password                        |
| POSTGRES_DB       | No       | locations_db | Database name                              |
| DB_PORT           | No       | 5431         | External port for database access          |
| APP_PORT          | No       | 8000         | External port for API access               |
| DATABASE_URL      | No       | (composed)   | Full database connection string            |
| GOOGLE_API_KEY    | No       | -            | Google Maps API key for reverse geocoding  |

---

## Project Structure

```
geospatial-data-generation/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and endpoints
│   ├── models.py        # SQLAlchemy ORM models
│   └── database.py      # Database connection configuration
├── scripts/
│   ├── ingestion.py     # Data ingestion and geocoding script
│   ├── mock_data.py     # Mock data generation utilities
│   └── test_db.py       # Database testing script
├── transactions.csv     # Sample transaction data with coordinates
├── Dockerfile           # Application container definition
├── docker-compose.yml   # Multi-container orchestration
├── entrypoint.sh        # Container startup script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

---

## License

MIT
