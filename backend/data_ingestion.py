import pandas as pd
import json
import ast
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import Facility, Anomaly, init_db, get_db
from vector_store import vector_store
from geospatial import compute_facility_reliability_score
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time


class DataIngestionPipeline:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="healthcare_intelligence")
        self.city_coordinates = {
            "Accra": (5.6037, -0.1870),
            "Kumasi": (6.6885, -1.6244),
            "Tamale": (9.4075, -0.8533),
            "Takoradi": (4.9016, -1.7831),
            "Cape Coast": (5.1054, -1.2466),
            "Ho": (6.6008, 0.4713),
            "Koforidua": (6.0941, -0.2591),
            "Sunyani": (7.3349, -2.3123),
            "Bolgatanga": (10.7856, -0.8514),
            "Wa": (10.0607, -2.5019),
            "Tema": (5.6698, -0.0166),
            "Obuasi": (6.2023, -1.6679),
            "Techiman": (7.5842, -1.9382),
        }
    
    def parse_json_field(self, field) -> List:
        """Safely parse JSON fields that might be strings or lists"""
        if pd.isna(field):
            return []
        if isinstance(field, list):
            return field
        if isinstance(field, str):
            if field.strip().lower() in {"", "null", "none", "nan"}:
                return []
            try:
                parsed = ast.literal_eval(field)
                if isinstance(parsed, list):
                    return parsed
                if parsed in (None, "null"):
                    return []
                return [parsed]
            except Exception:
                return [field] if field.strip() else []
        return []
    
    def geocode_address(self, address: str, city: str = None, country: str = "Ghana") -> tuple:
        """Geocode an address to get latitude and longitude"""
        if city:
            normalized_city = str(city).strip().lower()
            for known_city, coordinates in self.city_coordinates.items():
                if known_city.lower() == normalized_city:
                    return coordinates
        # Keep ingestion deterministic and offline-friendly for hackathon demos.
        return (None, None)

    def extract_facts_from_text(self, text_values: List, category: str) -> List[str]:
        """Extract IDP facts from messy text using healthcare keyword patterns."""
        if not text_values:
            return []

        keyword_map = {
            "procedure": [
                "surgery", "screening", "testing", "counseling", "treatment", "delivery",
                "operation", "immunization", "vaccination", "diagnosis", "consultation",
                "outreach", "therapy", "endoscopy", "dialysis",
            ],
            "equipment": [
                "x-ray", "xray", "ultrasound", "scanner", "ct", "mri", "laboratory",
                "microscope", "centrifuge", "machine", "oxygen", "theatre", "theater",
                "monitor", "ambulance", "equipment",
            ],
            "capability": [
                "specialties include", "specialty", "icu", "nicu", "emergency", "trauma",
                "inpatient", "outpatient", "capacity", "doctors", "clinic", "hospital",
                "maternity", "public health", "hiv", "tb", "maternal", "pediatric",
            ],
        }
        keywords = keyword_map[category]
        facts = []
        for value in text_values:
            for sentence in re.split(r"(?<=[.!?])\s+|;\s+", str(value)):
                normalized = sentence.strip()
                if normalized and any(keyword in normalized.lower() for keyword in keywords):
                    facts.append(normalized)
        return list(dict.fromkeys(facts))
    
    def extract_procedures_from_capabilities(self, capabilities: List) -> List:
        """Extract procedures from capabilities text"""
        procedures = []
        for cap in capabilities:
            if isinstance(cap, str):
                # Look for action verbs indicating procedures
                action_words = ["provides", "performs", "offers", "conducts", "delivers"]
                for word in action_words:
                    if word.lower() in cap.lower():
                        procedures.append(cap)
                        break
        return procedures
    
    def extract_equipment_from_capabilities(self, capabilities: List) -> List:
        """Extract equipment mentioned in capabilities"""
        equipment = []
        equipment_keywords = [
            "machine", "scanner", "imaging", "x-ray", "ultrasound", "mri", 
            "ct", "laboratory", "theatre", "operating", "equipment", "device"
        ]
        
        for cap in capabilities:
            if isinstance(cap, str):
                for keyword in equipment_keywords:
                    if keyword.lower() in cap.lower():
                        equipment.append(cap)
                        break
        return equipment
    
    def process_csv(self, csv_path: str, db: Session):
        """Process CSV file and ingest data into database"""
        df = pd.read_csv(csv_path)
        
        print(f"Processing {len(df)} facilities...")
        
        for idx, row in df.iterrows():
            try:
                # Parse JSON fields
                specialties = self.parse_json_field(row.get('specialties'))
                procedures_raw = self.parse_json_field(row.get('procedure'))
                equipment_raw = self.parse_json_field(row.get('equipment'))
                capabilities = self.parse_json_field(row.get('capability'))
                phone_numbers = self.parse_json_field(row.get('phone_numbers'))
                websites = self.parse_json_field(row.get('websites'))
                
                # Extract additional procedures and equipment from capabilities
                extracted_procedures = self.extract_procedures_from_capabilities(capabilities)
                extracted_equipment = self.extract_equipment_from_capabilities(capabilities)
                text_pool = capabilities + [row.get('description'), row.get('organizationDescription'), row.get('missionStatement')]
                extracted_procedures += self.extract_facts_from_text(text_pool, "procedure")
                extracted_equipment += self.extract_facts_from_text(text_pool, "equipment")
                extracted_capabilities = self.extract_facts_from_text(text_pool, "capability")
                
                # Combine procedures and equipment
                all_procedures = list(set(procedures_raw + extracted_procedures))
                all_equipment = list(set(equipment_raw + extracted_equipment))
                all_capabilities = list(dict.fromkeys(capabilities + extracted_capabilities))
                
                # Parse numeric fields
                number_doctors = None
                if pd.notna(row.get('numberDoctors')):
                    try:
                        number_doctors = int(row['numberDoctors'])
                    except:
                        pass
                
                capacity = None
                if pd.notna(row.get('capacity')):
                    try:
                        capacity = int(row['capacity'])
                    except:
                        pass
                
                year_established = None
                if pd.notna(row.get('yearEstablished')):
                    try:
                        year_established = int(row['yearEstablished'])
                    except:
                        pass
                
                # Geocode address
                address = row.get('address_line1', '')
                city = row.get('address_city', '')
                lat, lon = self.geocode_address(address, city)
                
                # Create facility
                unique_id = str(row.get('unique_id') or row.get('pk_unique_id') or f"fac_{idx}")
                existing = db.query(Facility).filter(Facility.unique_id == unique_id).first()
                if existing:
                    db.delete(existing)
                    db.flush()

                facility = Facility(
                    unique_id=unique_id,
                    name=row.get('name', ''),
                    source_url=row.get('source_url', ''),
                    facility_type=row.get('facilityTypeId', 'clinic') if pd.notna(row.get('facilityTypeId')) else 'clinic',
                    organization_type=row.get('organization_type', 'facility'),
                    address_line1=row.get('address_line1'),
                    address_line2=row.get('address_line2'),
                    address_city=row.get('address_city'),
                    address_state_or_region=row.get('address_stateOrRegion'),
                    address_country=row.get('address_country', 'Ghana'),
                    latitude=lat,
                    longitude=lon,
                    specialties=specialties,
                    procedures=all_procedures,
                    equipment=all_equipment,
                    capabilities=all_capabilities,
                    number_doctors=number_doctors,
                    capacity=capacity,
                    phone_numbers=phone_numbers,
                    email=row.get('email'),
                    websites=websites,
                    year_established=year_established,
                    description=row.get('description'),
                    mission_statement=row.get('missionStatement'),
                    raw_data=row.to_dict()
                )
                
                # Compute reliability score
                facility.facility_reliability_score = compute_facility_reliability_score(facility)
                
                db.add(facility)
                db.flush()  # Get the ID
                
                # Add to vector store
                try:
                    self._add_to_vector_store(facility)
                except Exception as vector_error:
                    print(f"Vector indexing skipped for row {idx}: {vector_error}")
                
                # Detect anomalies
                self._detect_anomalies(facility, db)
                
                if idx % 50 == 0:
                    print(f"Processed {idx} facilities...")
                    db.commit()
                
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                db.rollback()
                continue
        
        db.commit()
        print(f"Completed processing {len(df)} facilities")
    
    def _add_to_vector_store(self, facility: Facility):
        """Add facility to vector store for semantic search"""
        # Create searchable text
        text_parts = [
            facility.name,
            " ".join(facility.specialties or []),
            " ".join(facility.procedures or []),
            " ".join(facility.equipment or []),
            " ".join(facility.capabilities or []),
            facility.description or ""
        ]
        searchable_text = " ".join([p for p in text_parts if p])
        
        metadata = {
            "id": facility.unique_id,
            "name": facility.name,
            "facility_type": facility.facility_type,
            "city": facility.address_city or "",
            "specialties": json.dumps(facility.specialties or []),
            "latitude": facility.latitude or 0.0,
            "longitude": facility.longitude or 0.0
        }
        
        vector_store.add_facility(facility.unique_id, searchable_text, metadata)
    
    def _detect_anomalies(self, facility: Facility, db: Session):
        """Detect anomalies in facility data"""
        anomalies = []
        
        # Check capability vs equipment mismatch
        if facility.capabilities and facility.equipment:
            # If they claim to do imaging but have no imaging equipment
            has_imaging_capability = any('imaging' in str(c).lower() or 'x-ray' in str(c).lower() or 'ultrasound' in str(c).lower() 
                                        for c in facility.capabilities)
            has_imaging_equipment = any('imaging' in str(e).lower() or 'x-ray' in str(e).lower() or 'ultrasound' in str(e).lower() 
                                      for e in facility.equipment)
            
            if has_imaging_capability and not has_imaging_equipment:
                anomaly = Anomaly(
                    facility_id=facility.id,
                    anomaly_type="capability_equipment_mismatch",
                    severity="medium",
                    description="Facility claims imaging capabilities but no imaging equipment listed",
                    confidence_score=0.7,
                    detected_field="equipment",
                    expected_value="imaging equipment",
                    actual_value="none listed"
                )
                anomalies.append(anomaly)
        
        # Check unrealistic claims
        if facility.number_doctors and facility.capacity:
            # If capacity is very high but doctor count is low
            if facility.capacity > 500 and facility.number_doctors < 10:
                anomaly = Anomaly(
                    facility_id=facility.id,
                    anomaly_type="unrealistic_claim",
                    severity="high",
                    description=f"Capacity ({facility.capacity}) seems unrealistic for doctor count ({facility.number_doctors})",
                    confidence_score=0.8,
                    detected_field="capacity",
                    expected_value=f"< 500 for {facility.number_doctors} doctors",
                    actual_value=str(facility.capacity)
                )
                anomalies.append(anomaly)
        
        # Check missing infrastructure
        if facility.facility_type == "hospital" and not facility.equipment:
            anomaly = Anomaly(
                facility_id=facility.id,
                anomaly_type="missing_infrastructure",
                severity="medium",
                description="Hospital listed with no equipment information",
                confidence_score=0.6,
                detected_field="equipment",
                expected_value="equipment list",
                actual_value="none"
            )
            anomalies.append(anomaly)
        
        # Add anomalies to database
        for anomaly in anomalies:
            db.add(anomaly)


def ingest_data(csv_path: str):
    """Main function to ingest data"""
    init_db()
    db = next(get_db())
    
    pipeline = DataIngestionPipeline()
    pipeline.process_csv(csv_path, db)
    
    db.close()
    print("Data ingestion complete!")


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "../Virtue Foundation Ghana v0.3 - Sheet1.csv"
    ingest_data(csv_path)
