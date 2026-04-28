from sqlalchemy import create_engine, Column, Integer, String, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    source_url = Column(String)
    facility_type = Column(String)  # hospital, clinic, etc.
    organization_type = Column(String)
    
    # Location
    address_line1 = Column(String)
    address_line2 = Column(String)
    address_city = Column(String, index=True)
    address_state_or_region = Column(String, index=True)
    address_country = Column(String, default="Ghana")
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Healthcare data
    specialties = Column(JSON)  # List of specialties
    procedures = Column(JSON)  # List of procedures
    equipment = Column(JSON)  # List of equipment
    capabilities = Column(JSON)  # List of capabilities
    
    # Capacity
    number_doctors = Column(Integer)
    capacity = Column(Integer)
    
    # Contact
    phone_numbers = Column(JSON)
    email = Column(String)
    websites = Column(JSON)
    
    # Additional info
    year_established = Column(Integer)
    description = Column(Text)
    mission_statement = Column(Text)
    
    # Scoring
    facility_reliability_score = Column(Float, default=1.0)
    medical_desert_score = Column(Float, default=0.0)
    
    # Raw data for reference
    raw_data = Column(JSON)


class MedicalDesert(Base):
    __tablename__ = "medical_deserts"
    
    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, index=True)
    region_type = Column(String)  # city, state, etc.
    
    # Scores
    physician_density_score = Column(Float)
    hospital_density_score = Column(Float)
    medical_desert_score = Column(Float)
    
    # Counts
    total_facilities = Column(Integer)
    total_doctors = Column(Integer)
    total_capacity = Column(Integer)
    
    # Gap analysis
    population_estimate = Column(Integer)
    facilities_per_100k = Column(Float)
    doctors_per_100k = Column(Float)
    
    # Coordinates for visualization
    center_latitude = Column(Float)
    center_longitude = Column(Float)
    radius_km = Column(Float)


class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"))
    facility = relationship("Facility")
    
    anomaly_type = Column(String)  # capability_equipment_mismatch, unrealistic_claim, missing_infrastructure
    severity = Column(String)  # low, medium, high
    description = Column(Text)
    confidence_score = Column(Float)
    
    # Details
    detected_field = Column(String)
    expected_value = Column(String)
    actual_value = Column(String)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
