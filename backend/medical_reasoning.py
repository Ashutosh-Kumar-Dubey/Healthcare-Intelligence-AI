from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import Facility, Anomaly


class MedicalReasoningAgent:
    """Agent for medical reasoning and anomaly detection"""
    
    def __init__(self):
        self.medical_knowledge_base = {
            # Required equipment for procedures
            "imaging": ["x-ray", "ultrasound", "ct scanner", "mri machine"],
            "surgery": ["operating theatre", "surgical equipment", "anesthesia machine"],
            "laboratory": ["laboratory equipment", "microscope", "centrifuge"],
            "dialysis": ["dialysis machine", "hemodialysis equipment"],
            "cardiology": ["ecg machine", "echocardiogram", "cardiac monitor"],
            "ophthalmology": ["oct machine", "slit lamp", "fundus camera"],
            
            # Expected maximum inpatient beds per doctor for coarse validation.
            "doctor_capacity_ratio": {
                "clinic": 50,
                "hospital": 100,
                "specialist": 150
            }
        }
    
    def detect_capability_equipment_mismatch(
        self, 
        facility: Facility
    ) -> List[Dict[str, Any]]:
        """Detect mismatches between claimed capabilities and listed equipment"""
        mismatches = []
        
        if not facility.capabilities or not facility.equipment:
            return mismatches
        
        equipment_str = " ".join([str(e).lower() for e in facility.equipment])
        
        for capability in facility.capabilities:
            if not isinstance(capability, str):
                continue
            
            capability_lower = capability.lower()
            
            # Check if capability requires specific equipment
            for proc, required_equipment in self.medical_knowledge_base.items():
                if proc in capability_lower:
                    has_equipment = any(
                        eq in equipment_str 
                        for eq in required_equipment
                    )
                    
                    if not has_equipment:
                        mismatches.append({
                            "type": "capability_equipment_mismatch",
                            "capability": capability,
                            "missing_equipment": required_equipment,
                            "severity": "high" if proc in ["surgery", "dialysis"] else "medium",
                            "confidence": 0.75
                        })
        
        return mismatches
    
    def detect_unrealistic_claims(
        self, 
        facility: Facility
    ) -> List[Dict[str, Any]]:
        """Detect unrealistic or inconsistent claims"""
        unrealistic = []
        
        # Check doctor-to-capacity ratio
        if facility.number_doctors and facility.capacity:
            ratio = facility.capacity / max(facility.number_doctors, 1)
            expected_max_beds_per_doctor = self.medical_knowledge_base["doctor_capacity_ratio"].get(
                facility.facility_type, 100
            )
            
            # If ratio is way off (more than 3x expected)
            if ratio > expected_max_beds_per_doctor * 3:
                unrealistic.append({
                    "type": "unrealistic_capacity",
                    "field": "capacity",
                    "value": facility.capacity,
                    "expected_max": facility.number_doctors * expected_max_beds_per_doctor * 3,
                    "severity": "high",
                    "confidence": 0.8
                })
        
        # Check for impossible specialties combinations
        if facility.specialties and len(facility.specialties) > 20:
            unrealistic.append({
                "type": "unrealistic_specialties",
                "field": "specialties",
                "value": len(facility.specialties),
                "expected_max": 20,
                "severity": "medium",
                "confidence": 0.7
            })
        
        return unrealistic
    
    def detect_missing_infrastructure(
        self, 
        facility: Facility
    ) -> List[Dict[str, Any]]:
        """Detect missing infrastructure based on facility type"""
        missing = []
        
        if facility.facility_type == "hospital":
            # Hospitals should have certain basic infrastructure
            if not facility.equipment:
                missing.append({
                    "type": "missing_infrastructure",
                    "field": "equipment",
                    "severity": "high",
                    "confidence": 0.9
                })
            
            if not facility.number_doctors:
                missing.append({
                    "type": "missing_infrastructure",
                    "field": "number_doctors",
                    "severity": "high",
                    "confidence": 0.85
                })
        
        elif facility.facility_type == "clinic":
            if not facility.specialties:
                missing.append({
                    "type": "missing_infrastructure",
                    "field": "specialties",
                    "severity": "medium",
                    "confidence": 0.7
                })
        
        return missing
    
    def compute_overall_reliability_score(
        self, 
        facility: Facility,
        anomalies: List[Anomaly]
    ) -> float:
        """Compute overall reliability score based on data quality and anomalies"""
        base_score = 1.0
        
        # Deduct for data completeness
        if not facility.name:
            base_score -= 0.2
        if not facility.address_city:
            base_score -= 0.1
        if not facility.specialties:
            base_score -= 0.15
        if not facility.capabilities:
            base_score -= 0.1
        
        # Deduct for anomalies
        for anomaly in anomalies:
            if anomaly.severity == "high":
                base_score -= 0.15 * anomaly.confidence_score
            elif anomaly.severity == "medium":
                base_score -= 0.1 * anomaly.confidence_score
            else:
                base_score -= 0.05 * anomaly.confidence_score
        
        return max(0.0, min(1.0, base_score))
    
    def analyze_facility(
        self, 
        facility: Facility
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of a facility"""
        analysis = {
            "facility_id": facility.id,
            "facility_name": facility.name,
            "reliability_score": facility.facility_reliability_score,
            "anomalies": [],
            "recommendations": []
        }
        
        # Detect various types of anomalies
        capability_mismatches = self.detect_capability_equipment_mismatch(facility)
        unrealistic_claims = self.detect_unrealistic_claims(facility)
        missing_infra = self.detect_missing_infrastructure(facility)
        
        analysis["anomalies"].extend(capability_mismatches)
        analysis["anomalies"].extend(unrealistic_claims)
        analysis["anomalies"].extend(missing_infra)
        
        # Generate recommendations
        if capability_mismatches:
            analysis["recommendations"].append(
                "Verify equipment inventory against claimed capabilities"
            )
        
        if unrealistic_claims:
            analysis["recommendations"].append(
                "Review and validate capacity and staffing numbers"
            )
        
        if missing_infra:
            analysis["recommendations"].append(
                "Complete missing infrastructure information"
            )
        
        if not analysis["anomalies"]:
            analysis["recommendations"].append(
                "Facility data appears consistent and complete"
            )
        
        return analysis


medical_reasoning_agent = MedicalReasoningAgent()
