from fastapi import FastAPI, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
from . import models
from .database import SessionLocal, engine
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


class Location(BaseModel):
    id: str
    address: str
    latitude: float
    longitude: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/locations/search")
async def search_locations(
    lat: float = Query(..., description="Latitude of the center point"),
    lon: float = Query(..., description="Longitude of the center point"),
    radius: float = Query(1000, description="Search radius in meters"),
    db: db_dependency = None,
) -> List[Location]:
    results = query_locations_within_radius(db, lat, lon, radius)
    if not results:
        raise HTTPException(
            status_code=404, detail="No locations found within the specified radius"
        )
    return results


def query_locations_within_radius(
    db: Session, lat: float, lon: float, radius: float
) -> List[Location]:
    """
    Fetch locations within a given radius using SQLAlchemy.
    Uses the Haversine formula to calculate distance.
    """
    # Fetch all locations and filter by distance
    locations = db.query(models.Location).all()

    result = []
    for loc in locations:
        # Haversine formula to calculate distance in meters
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Earth's radius in meters
        lat1, lon1 = radians(lat), radians(lon)
        lat2, lon2 = radians(float(loc.latitude)), radians(float(loc.longitude))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        if distance <= radius:
            result.append(
                Location(
                    id=str(loc.id),
                    address=str(loc.address),
                    latitude=float(loc.latitude),
                    longitude=float(loc.longitude),
                )
            )

    return result
