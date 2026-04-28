from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
from pathlib import Path
from collections import Counter, defaultdict

from database import init_db, get_db, Facility, Anomaly, MedicalDesert
from agents import (
    supervisor, text_to_sql, vector_search, 
    medical_reasoning, geospatial
)
from geospatial import detect_underserved_regions, is_valid_ghana_coordinate
from data_ingestion import DataIngestionPipeline
from intelligence_agent import healthcare_intelligence_agent

app = FastAPI(title="Healthcare Intelligence AI", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None


class GeospatialRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float
    facility_type: Optional[str] = None


class MedicalDesertRequest(BaseModel):
    region_name: str
    region_type: Optional[str] = "city"


class FacilityResponse(BaseModel):
    id: int
    unique_id: str
    name: str
    facility_type: str
    address_city: Optional[str]
    address_state_or_region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    specialties: Optional[List[str]]
    procedures: Optional[List[str]]
    equipment: Optional[List[str]]
    capabilities: Optional[List[str]]
    number_doctors: Optional[int]
    capacity: Optional[int]
    facility_reliability_score: float
    medical_desert_score: float
    
    class Config:
        from_attributes = True


class AnomalyResponse(BaseModel):
    id: int
    facility_id: int
    anomaly_type: str
    severity: str
    description: str
    confidence_score: float
    
    class Config:
        from_attributes = True


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    db = next(get_db())
    try:
        if db.query(Facility).count() == 0:
            csv_path = Path(__file__).resolve().parents[2] / "Virtue Foundation Ghana v0.3 - Sheet1.csv"
            if csv_path.exists():
                DataIngestionPipeline().process_csv(str(csv_path), db)
    finally:
        db.close()


# Health check
@app.get("/")
async def root():
    return {
        "message": "Healthcare Intelligence AI API",
        "version": "1.0.0",
        "status": "running"
    }


# Query endpoint - main AI agent interface
@app.post("/api/query")
async def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Process natural language query using multi-agent system"""
    try:
        return healthcare_intelligence_agent.answer_query(
            request.query,
            db,
            request.parameters,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Geospatial endpoints
@app.post("/api/geospatial/nearby")
async def find_nearby(
    request: GeospatialRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Find facilities within a radius of a point"""
    try:
        facilities = geospatial.find_nearby_facilities(
            request.latitude,
            request.longitude,
            request.radius_km,
            db,
            request.facility_type
        )
        
        return {
            "center": {"lat": request.latitude, "lon": request.longitude},
            "radius_km": request.radius_km,
            "count": len(facilities),
            "facilities": facilities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/geospatial/medical-desert")
async def calculate_desert_score(
    request: MedicalDesertRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Calculate medical desert score for a region"""
    try:
        score_data = geospatial.calculate_medical_desert(
            request.region_name,
            db
        )
        
        return {
            "region": request.region_name,
            "region_type": request.region_type,
            **score_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/geospatial/underserved")
async def get_underserved_regions(
    threshold: float = Query(0.7, ge=0, le=1),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get all underserved regions"""
    try:
        underserved = detect_underserved_regions(db, threshold)
        
        return {
            "threshold": threshold,
            "count": len(underserved),
            "regions": underserved
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Facility endpoints
@app.get("/api/facilities", response_model=List[FacilityResponse])
async def get_facilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    facility_type: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get facilities with optional filters"""
    try:
        query = db.query(Facility)
        
        if facility_type:
            query = query.filter(Facility.facility_type == facility_type)
        
        if city:
            query = query.filter(Facility.address_city == city)
        
        facilities = query.offset(skip).limit(limit).all()
        return facilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/facilities/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific facility by ID"""
    try:
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        return facility
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/facilities/{facility_id}/analysis")
async def get_facility_analysis(
    facility_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed analysis of a facility including anomalies"""
    try:
        analysis = medical_reasoning.analyze_facility(facility_id, db)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Anomaly endpoints
@app.get("/api/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get anomalies with optional filters"""
    try:
        query = db.query(Anomaly)
        
        if severity:
            query = query.filter(Anomaly.severity == severity)
        
        anomalies = query.offset(skip).limit(limit).all()
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints
@app.get("/api/stats/overview")
async def get_overview_stats(db: Session = Depends(get_db)):
    """Get overview statistics"""
    try:
        total_facilities = db.query(Facility).count()
        total_hospitals = db.query(Facility).filter(Facility.facility_type == "hospital").count()
        total_clinics = db.query(Facility).filter(Facility.facility_type == "clinic").count()
        total_anomalies = db.query(Anomaly).count()
        total_regions = len([row for row in db.query(Facility.address_city).distinct().all() if row[0]])
        mapped_facilities = db.query(Facility).filter(
            Facility.latitude.isnot(None),
            Facility.longitude.isnot(None)
        ).all()
        mapped_facilities = [
            facility
            for facility in mapped_facilities
            if is_valid_ghana_coordinate(facility.latitude, facility.longitude)
        ]
        high_risk_regions = detect_underserved_regions(db, 0.8)
        facilities_with_idp = db.query(Facility).filter(
            (Facility.procedures != None) | (Facility.equipment != None) | (Facility.capabilities != None)
        ).count()
        
        # Calculate average reliability score
        avg_reliability = db.query(Facility.facility_reliability_score).all()
        if avg_reliability:
            avg_reliability = sum([s[0] or 0 for s in avg_reliability]) / len(avg_reliability)
        else:
            avg_reliability = 0.0
        
        return {
            "total_facilities": total_facilities,
            "total_hospitals": total_hospitals,
            "total_clinics": total_clinics,
            "total_anomalies": total_anomalies,
            "average_reliability_score": avg_reliability,
            "total_regions": total_regions,
            "facilities_with_idp_facts": facilities_with_idp,
            "mapped_facilities": len(mapped_facilities),
            "high_risk_regions": len(high_risk_regions),
            "claim_verification_rate": (total_anomalies / total_facilities) if total_facilities else 0.0,
            "map_coverage_rate": (len(mapped_facilities) / total_facilities) if total_facilities else 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/by-region")
async def get_stats_by_region(db: Session = Depends(get_db)):
    """Get statistics grouped by region/city"""
    try:
        from sqlalchemy import func
        
        stats = db.query(
            Facility.address_city,
            func.count(Facility.id).label('count'),
            func.sum(Facility.number_doctors).label('total_doctors'),
            func.sum(Facility.capacity).label('total_capacity'),
            func.avg(Facility.facility_reliability_score).label('avg_reliability')
        ).group_by(Facility.address_city).all()
        
        return [
            {
                "city": stat[0],
                "facility_count": stat[1],
                "total_doctors": stat[2] or 0,
                "total_capacity": stat[3] or 0,
                "avg_reliability": stat[4] or 0.0
            }
            for stat in stats
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data ingestion endpoint
@app.post("/api/ingest")
async def ingest_data(
    csv_path: str = Query(..., description="Path to CSV file"),
    db: Session = Depends(get_db)
):
    """Ingest data from CSV file"""
    try:
        pipeline = DataIngestionPipeline()
        pipeline.process_csv(csv_path, db)
        
        return {
            "message": "Data ingestion completed successfully",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Map data endpoint
@app.get("/api/map/facilities")
async def get_map_facilities(
    facility_type: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get facilities formatted for map visualization"""
    try:
        query = db.query(Facility).filter(
            Facility.latitude.isnot(None),
            Facility.longitude.isnot(None)
        )
        
        if facility_type:
            query = query.filter(Facility.facility_type == facility_type)
        
        if city:
            query = query.filter(Facility.address_city == city)
        
        facilities = [
            facility
            for facility in query.all()
            if is_valid_ghana_coordinate(facility.latitude, facility.longitude)
        ]

        grouped = defaultdict(list)
        for facility in facilities:
            key = (
                (facility.name or "").strip().lower(),
                (facility.address_city or "").strip().lower(),
                round(facility.latitude or 0, 4),
                round(facility.longitude or 0, 4),
            )
            grouped[key].append(facility)

        def merge_list(rows, field_name):
            values = []
            for row in rows:
                for item in getattr(row, field_name) or []:
                    if item and item not in values:
                        values.append(item)
            return values

        merged_facilities = []
        for rows in grouped.values():
            primary = max(
                rows,
                key=lambda row: (
                    len(row.specialties or []),
                    len(row.capabilities or []),
                    row.facility_reliability_score or 0,
                ),
            )
            type_counts = Counter([row.facility_type for row in rows if row.facility_type])
            reliability_values = [row.facility_reliability_score or 0 for row in rows]
            doctors = [row.number_doctors for row in rows if row.number_doctors is not None]
            capacities = [row.capacity for row in rows if row.capacity is not None]

            merged_facilities.append({
                "id": primary.id,
                "name": primary.name,
                "type": type_counts.most_common(1)[0][0] if type_counts else primary.facility_type,
                "lat": primary.latitude,
                "lon": primary.longitude,
                "city": primary.address_city,
                "specialties": merge_list(rows, "specialties"),
                "procedures": merge_list(rows, "procedures"),
                "equipment": merge_list(rows, "equipment"),
                "capabilities": merge_list(rows, "capabilities"),
                "reliability_score": sum(reliability_values) / max(len(reliability_values), 1),
                "best_row_reliability": max(reliability_values) if reliability_values else 0,
                "evidence_rows": len(rows),
                "doctors": sum(doctors) if doctors else None,
                "capacity": max(capacities) if capacities else None
            })

        return sorted(merged_facilities, key=lambda item: item["name"] or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/map/heatmap")
async def get_heatmap_data(
    heatmap_type: str = Query("physician_density", description="Type of heatmap: physician_density, hospital_density, medical_desert"),
    db: Session = Depends(get_db)
):
    """Get heatmap data for visualization"""
    try:
        if heatmap_type == "physician_density":
            # Group by city and calculate physician density
            from sqlalchemy import func
            data = db.query(
                Facility.address_city,
                Facility.latitude,
                Facility.longitude,
                func.sum(Facility.number_doctors).label('total_doctors'),
                func.count(Facility.id).label('facility_count')
            ).group_by(
                Facility.address_city,
                Facility.latitude,
                Facility.longitude
            ).all()
            
            return [
                {
                    "lat": row[1],
                    "lon": row[2],
                    "intensity": min((row[3] or 0) / max(row[4], 1) / 20, 1.0),
                    "city": row[0],
                    "value": row[3] or 0
                }
                for row in data
                if is_valid_ghana_coordinate(row[1], row[2])
            ]
        
        elif heatmap_type == "hospital_density":
            from sqlalchemy import func
            data = db.query(
                Facility.address_city,
                Facility.latitude,
                Facility.longitude,
                func.count(Facility.id).label('facility_count')
            ).filter(
                Facility.facility_type == "hospital"
            ).group_by(
                Facility.address_city,
                Facility.latitude,
                Facility.longitude
            ).all()
            
            return [
                {
                    "lat": row[1],
                    "lon": row[2],
                    "intensity": min(row[3] / 10, 1.0),
                    "city": row[0],
                    "value": row[3]
                }
                for row in data
                if is_valid_ghana_coordinate(row[1], row[2])
            ]
        
        elif heatmap_type == "medical_desert":
            underserved = detect_underserved_regions(db, 0.5)
            
            return [
                {
                    "lat": region.get("center_latitude", 0),
                    "lon": region.get("center_longitude", 0),
                    "intensity": region["medical_desert_score"],
                    "city": region["region_name"],
                    "value": region["medical_desert_score"]
                }
                for region in underserved
                if is_valid_ghana_coordinate(region.get("center_latitude"), region.get("center_longitude"))
            ]
        
        else:
            raise HTTPException(status_code=400, detail="Invalid heatmap type")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
