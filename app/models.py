from sqlalchemy import Column, Float, String
from sqlalchemy.ext.declarative import declarative_base
from .database import Base


class Location(Base):
    __tablename__ = "locations_data"

    id = Column(String, primary_key=True, index=True)
    address = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
