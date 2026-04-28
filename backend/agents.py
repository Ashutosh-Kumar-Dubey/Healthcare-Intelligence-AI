from typing import Dict, Any, List, TypedDict, Annotated
from sqlalchemy.orm import Session
from database import Facility, get_db
from vector_store import vector_store
from geospatial import find_facilities_within_radius, calculate_medical_desert_score
from medical_reasoning import medical_reasoning_agent
import re


class AgentState(TypedDict):
    query: str
    query_type: str
    sql_query: str
    sql_results: List[Dict]
    vector_results: List[Dict]
    medical_analysis: Dict
    geospatial_results: Dict
    final_answer: str
    confidence: float
    citations: List[str]


class SupervisorAgent:
    """Routes queries to appropriate agents"""
    
    def analyze_query(self, query: str) -> str:
        """Analyze query and determine type"""
        query_lower = query.lower()
        
        # Check for count queries
        if any(word in query_lower for word in ["count", "how many", "number of"]):
            return "count"
        
        # Check for geospatial queries
        if any(word in query_lower for word in ["within", "near", "radius", "km", "distance", "around"]):
            return "geospatial"
        
        # Check for gap/shortage queries
        if any(word in query_lower for word in ["gap", "shortage", "lack", "missing", "desert", "underserved"]):
            return "gap_analysis"
        
        # Check for anomaly queries
        if any(word in query_lower for word in ["anomaly", "inconsistent", "unreliable", "suspicious"]):
            return "anomaly_detection"
        
        # Default to semantic search
        return "semantic_search"


class TextToSQLAgent:
    """Converts natural language to SQL queries"""
    
    def generate_sql(self, query: str, db: Session) -> tuple:
        """Generate SQL query from natural language"""
        query_lower = query.lower()
        
        # Count queries
        if "count" in query_lower or "how many" in query_lower:
            # Extract specialty
            specialty_match = re.search(r'(?:with|that have|offering|providing)\s+(\w+)', query_lower)
            if specialty_match:
                specialty = specialty_match.group(1)
                sql = f"""
                    SELECT COUNT(*) as count, '{specialty}' as specialty
                    FROM facilities 
                    WHERE specialties LIKE '%{specialty}%'
                """
                return sql, "count"
            
            # Extract facility type
            type_match = re.search(r'(hospitals|clinics|facilities)', query_lower)
            if type_match:
                facility_type = type_match.group(1).rstrip('s')
                sql = f"""
                    SELECT COUNT(*) as count, '{facility_type}' as type
                    FROM facilities 
                    WHERE facility_type = '{facility_type}'
                """
                return sql, "count"
        
        # Default count
        sql = "SELECT COUNT(*) as count FROM facilities"
        return sql, "count"
    
    def execute_sql(self, sql: str, db: Session) -> List[Dict]:
        """Execute SQL query and return results"""
        result = db.execute(sql)
        columns = result.keys()
        rows = result.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]


class VectorSearchAgent:
    """Handles semantic search using vector database"""
    
    def search(self, query: str, n_results: int = 10) -> Dict:
        """Perform semantic search"""
        results = vector_store.search_facilities(query, n_results)
        
        formatted_results = []
        if results and 'documents' in results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results.get('distances') else 0
                })
        
        return {
            "results": formatted_results,
            "count": len(formatted_results)
        }


class MedicalReasoningAgentWrapper:
    """Wrapper for medical reasoning agent"""
    
    def analyze_facility(self, facility_id: int, db: Session) -> Dict:
        """Analyze a specific facility"""
        facility = db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            return {"error": "Facility not found"}
        
        return medical_reasoning_agent.analyze_facility(facility)
    
    def detect_anomalies_batch(self, db: Session, limit: int = 50) -> List[Dict]:
        """Detect anomalies across multiple facilities"""
        facilities = db.query(Facility).limit(limit).all()
        
        anomalies = []
        for facility in facilities:
            analysis = medical_reasoning_agent.analyze_facility(facility)
            if analysis["anomalies"]:
                anomalies.append({
                    "facility_id": facility.id,
                    "facility_name": facility.name,
                    "anomalies": analysis["anomalies"],
                    "reliability_score": analysis["reliability_score"]
                })
        
        return anomalies


class GeospatialAgent:
    """Handles geospatial queries and medical desert detection"""
    
    def find_nearby_facilities(
        self, 
        lat: float, 
        lon: float, 
        radius_km: float,
        db: Session,
        facility_type: str = None
    ) -> List[Dict]:
        """Find facilities within radius"""
        facilities = find_facilities_within_radius(db, lat, lon, radius_km, facility_type)
        
        return [
            {
                "id": f.id,
                "name": f.name,
                "facility_type": f.facility_type,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "specialties": f.specialties,
                "address": f.address_city
            }
            for f in facilities
        ]
    
    def calculate_medical_desert(
        self, 
        region_name: str, 
        db: Session
    ) -> Dict:
        """Calculate medical desert score for a region"""
        return calculate_medical_desert_score(db, region_name)
    
    def detect_underserved_regions(self, db: Session, threshold: float = 0.7) -> List[Dict]:
        """Detect underserved regions"""
        from geospatial import detect_underserved_regions
        return detect_underserved_regions(db, threshold)


# Agent instances
supervisor = SupervisorAgent()
text_to_sql = TextToSQLAgent()
vector_search = VectorSearchAgent()
medical_reasoning = MedicalReasoningAgentWrapper()
geospatial = GeospatialAgent()
