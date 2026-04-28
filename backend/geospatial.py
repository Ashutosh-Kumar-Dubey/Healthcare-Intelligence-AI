import math
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from database import Facility, MedicalDesert


GHANA_BOUNDS = {
    "min_lat": 4.0,
    "max_lat": 12.5,
    "min_lon": -3.5,
    "max_lon": 1.5,
}


def is_valid_ghana_coordinate(lat: float, lon: float) -> bool:
    """Return True for usable Ghana map coordinates."""
    if lat is None or lon is None:
        return False
    return (
        GHANA_BOUNDS["min_lat"] <= lat <= GHANA_BOUNDS["max_lat"]
        and GHANA_BOUNDS["min_lon"] <= lon <= GHANA_BOUNDS["max_lon"]
    )


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r


def find_facilities_within_radius(
    db: Session, 
    lat: float, 
    lon: float, 
    radius_km: float,
    facility_type: str = None
) -> List[Facility]:
    """Find all facilities within a given radius of a point"""
    facilities = db.query(Facility).filter(
        Facility.latitude.isnot(None),
        Facility.longitude.isnot(None)
    )
    
    if facility_type:
        facilities = facilities.filter(Facility.facility_type == facility_type)
    
    facilities = facilities.all()
    
    result = []
    for facility in facilities:
        distance = haversine_distance(lat, lon, facility.latitude, facility.longitude)
        if distance <= radius_km:
            result.append(facility)
    
    return result


def calculate_medical_desert_score(
    db: Session,
    region_name: str,
    region_type: str = "city",
    radius_km: float = 50
) -> Dict:
    """
    Calculate medical desert score for a region
    Score ranges from 0 (well-served) to 1 (medical desert)
    """
    # Get facilities in the region
    if region_type == "city":
        facilities = db.query(Facility).filter(
            Facility.address_city == region_name
        ).all()
    else:
        facilities = db.query(Facility).filter(
            Facility.address_state_or_region == region_name
        ).all()
    
    if not facilities:
        return {
            "medical_desert_score": 1.0,
            "physician_density_score": 0.0,
            "hospital_density_score": 0.0,
            "total_facilities": 0,
            "total_doctors": 0,
            "total_capacity": 0
        }
    
    # Calculate center point
    lats = [f.latitude for f in facilities if f.latitude]
    lons = [f.longitude for f in facilities if f.longitude]
    
    if lats and lons:
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
    else:
        center_lat = 0.0
        center_lon = 0.0
    
    # Count metrics
    total_facilities = len(facilities)
    total_doctors = sum([f.number_doctors or 0 for f in facilities])
    total_capacity = sum([f.capacity or 0 for f in facilities])
    
    hospitals = [f for f in facilities if f.facility_type == "hospital"]
    hospital_count = len(hospitals)
    
    # Calculate density scores (normalized)
    # Assuming baseline: 10 facilities per 100k people is adequate
    # Using 100k as baseline population estimate
    baseline_population = 100000
    facilities_per_100k = (total_facilities / baseline_population) * 100000
    doctors_per_100k = (total_doctors / baseline_population) * 100000
    
    # Physician density score (0 = low, 1 = high)
    # WHO recommends 23 doctors per 10,000 people (230 per 100k)
    physician_density_score = min(doctors_per_100k / 230, 1.0)
    
    # Hospital density score
    # Assuming 5 hospitals per 100k is adequate
    hospital_density_score = min((hospital_count / baseline_population) * 100000 / 5, 1.0)
    
    # Medical desert score (inverse of service level)
    # Combines physician and hospital density
    service_level = (physician_density_score + hospital_density_score) / 2
    medical_desert_score = 1.0 - service_level
    
    return {
        "medical_desert_score": medical_desert_score,
        "physician_density_score": physician_density_score,
        "hospital_density_score": hospital_density_score,
        "total_facilities": total_facilities,
        "total_doctors": total_doctors,
        "total_capacity": total_capacity,
        "center_latitude": center_lat,
        "center_longitude": center_lon,
        "radius_km": radius_km
    }


def detect_underserved_regions(db: Session, threshold: float = 0.7) -> List[Dict]:
    """Detect regions with high medical desert scores"""
    regions = db.query(Facility.address_city).distinct().all()
    
    underserved = []
    for (region_name,) in regions:
        if not region_name:
            continue
        
        score_data = calculate_medical_desert_score(db, region_name)
        
        if score_data["medical_desert_score"] >= threshold:
            underserved.append({
                "region_name": region_name,
                **score_data
            })
    
    # Sort by desert score (highest first)
    underserved.sort(key=lambda x: x["medical_desert_score"], reverse=True)
    
    return underserved


def compute_facility_reliability_score(facility: Facility) -> float:
    """
    Compute facility reliability score based on data completeness and consistency
    Score ranges from 0 (unreliable) to 1 (highly reliable)
    """
    score = 1.0
    
    # Check for basic information
    if not facility.name:
        score -= 0.2
    if not facility.address_city:
        score -= 0.1
    if not facility.facility_type:
        score -= 0.1
    
    # Check for healthcare data
    if not facility.specialties:
        score -= 0.15
    if not facility.capabilities:
        score -= 0.1
    
    # Check for capacity information
    if not facility.number_doctors and not facility.capacity:
        score -= 0.15
    
    # Check for contact information
    if not facility.phone_numbers and not facility.email:
        score -= 0.1
    
    # Check for geolocation
    if not facility.latitude or not facility.longitude:
        score -= 0.1
    
    return max(0.0, score)
