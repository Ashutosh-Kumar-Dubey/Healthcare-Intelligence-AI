from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple
import re

from sqlalchemy.orm import Session

from database import Facility, Anomaly
from geospatial import calculate_medical_desert_score, detect_underserved_regions
from medical_reasoning import medical_reasoning_agent


CRITICAL_SERVICE_KEYWORDS = {
    "emergency": ["emergency", "trauma", "urgent care", "casualty"],
    "surgery": ["surgery", "surgical", "operating theatre", "operating theater", "operation"],
    "obstetrics": ["obstetric", "maternity", "maternal", "delivery", "cesarean", "antenatal"],
    "imaging": ["x-ray", "xray", "ultrasound", "ct", "mri", "imaging", "radiology"],
    "laboratory": ["laboratory", "lab", "diagnostic", "microscope", "testing"],
    "dialysis": ["dialysis", "hemodialysis"],
    "cardiology": ["cardiology", "cardiac", "ecg", "echo"],
    "pediatrics": ["pediatric", "paediatric", "children", "child health"],
    "ophthalmology": ["ophthalmology", "eye", "cataract", "vision"],
}


FACILITY_TYPES = {"hospital", "clinic", "pharmacy", "doctor", "dentist"}


def _as_list(value: Any) -> List[Any]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _clean_terms(text: str) -> List[str]:
    stopwords = {
        "show", "find", "which", "what", "where", "with", "have", "has", "near",
        "facilities", "facility", "hospitals", "hospital", "clinics", "clinic",
        "regions", "region", "medical", "healthcare", "care", "the", "and", "for",
        "that", "are", "is", "in", "of", "to", "me", "all", "available",
    }
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())
        if token not in stopwords and len(token) > 2
    ]


class HealthcareIntelligenceAgent:
    """Rule-based IDP and planning agent for Virtue Foundation facility data."""

    def answer_query(
        self,
        query: str,
        db: Session,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        parameters = parameters or {}
        query_type = self.classify(query)

        trace = [
            {
                "step": "classify_request",
                "input": query,
                "output": query_type,
                "citations": [],
            }
        ]

        if query_type == "anomaly_detection":
            result = self._anomaly_report(db)
        elif query_type == "gap_analysis":
            result = self._gap_report(query, db, parameters)
        elif query_type == "planning":
            result = self._planning_report(query, db, parameters)
        elif query_type == "count":
            result = self._count_report(query, db)
        elif query_type == "geospatial":
            result = self._geospatial_report(query, db, parameters)
        else:
            result = self._capability_search(query, db)

        trace.append(
            {
                "step": "synthesize_answer",
                "input": {
                    "query_type": query_type,
                    "evidence_count": len(result.get("citations", [])),
                },
                "output": result["answer"],
                "citations": result.get("citations", [])[:8],
            }
        )

        return {
            "query": query,
            "query_type": query_type,
            "answer": result["answer"],
            "summary": result.get("summary", []),
            "findings": result.get("findings", []),
            "recommended_actions": result.get("recommended_actions", []),
            "data": result.get("data", {}),
            "confidence": result.get("confidence", 0.78),
            "citations": result.get("citations", [])[:20],
            "agent_trace": trace,
        }

    def classify(self, query: str) -> str:
        query_lower = query.lower()
        if any(word in query_lower for word in ["plan", "route", "prioritize", "deploy", "investment", "action"]):
            return "planning"
        if any(word in query_lower for word in ["anomaly", "inconsistent", "unreliable", "suspicious", "verify", "mismatch"]):
            return "anomaly_detection"
        if any(word in query_lower for word in ["gap", "shortage", "lack", "missing", "desert", "underserved", "risk"]):
            return "gap_analysis"
        if any(word in query_lower for word in ["within", "near", "radius", "km", "distance", "around"]):
            return "geospatial"
        if any(word in query_lower for word in ["count", "how many", "number of", "total"]):
            return "count"
        return "capability_search"

    def _count_report(self, query: str, db: Session) -> Dict[str, Any]:
        facilities = self._matching_facilities(query, db)
        citations = [self._citation(f, "row", "Facility matched count query") for f in facilities[:10]]
        facility_type = self._facility_type_from_query(query)
        label = facility_type or "facilities"
        return {
            "answer": f"Found {len(facilities)} {label} matching the request.",
            "summary": [f"{len(facilities)} matching rows", f"{len(citations)} row-level citations returned"],
            "findings": self._facility_findings(facilities[:8]),
            "recommended_actions": ["Open cited rows before operational use", "Run anomaly detection for facilities used in routing decisions"],
            "data": {"count": len(facilities), "facilities": self._facility_cards(facilities[:25])},
            "confidence": 0.86,
            "citations": citations,
        }

    def _capability_search(self, query: str, db: Session) -> Dict[str, Any]:
        facilities = self._matching_facilities(query, db)
        if not facilities:
            facilities = db.query(Facility).limit(10).all()

        service_counter = Counter()
        for facility in facilities:
            service_counter.update(self._facility_services(facility))

        top_services = ", ".join([name for name, _ in service_counter.most_common(5)]) or "limited structured service evidence"
        citations = [self._best_citation(f, query) for f in facilities[:12]]
        answer = (
            f"I found {len(facilities)} relevant facilities. The strongest capability signals are: {top_services}. "
            "Use the cited rows to verify each claim before patient or volunteer routing."
        )

        return {
            "answer": answer,
            "summary": [f"{len(facilities)} facilities matched", f"Top services: {top_services}"],
            "findings": self._facility_findings(facilities[:10]),
            "recommended_actions": [
                "Confirm capability claims with facilities that have weak equipment evidence",
                "Prioritize facilities with named specialties plus matching procedure or equipment evidence",
            ],
            "data": {
                "facilities": self._facility_cards(facilities[:25]),
                "service_distribution": dict(service_counter.most_common()),
            },
            "confidence": 0.8 if citations else 0.62,
            "citations": citations,
        }

    def _gap_report(self, query: str, db: Session, parameters: Dict[str, Any]) -> Dict[str, Any]:
        threshold = float(parameters.get("threshold", 0.65))
        regions = detect_underserved_regions(db, threshold)
        if not regions:
            city_names = [row[0] for row in db.query(Facility.address_city).distinct().all() if row[0]]
            regions = [
                {"region_name": city, **calculate_medical_desert_score(db, city)}
                for city in city_names
            ]
            regions.sort(key=lambda item: item["medical_desert_score"], reverse=True)

        enriched = []
        citations = []
        for region in regions[:12]:
            facilities = db.query(Facility).filter(Facility.address_city == region["region_name"]).all()
            missing = self._missing_critical_services(facilities)
            sample = facilities[:3]
            citations.extend([self._citation(f, "city", f"Facility evidence for {region['region_name']}") for f in sample])
            enriched.append({
                **region,
                "missing_critical_services": missing,
                "facilities": self._facility_cards(sample),
            })

        top_names = ", ".join([r["region_name"] for r in enriched[:5]]) or "no populated regions"
        answer = (
            f"Highest-risk medical desert candidates are {top_names}. "
            "The score combines low doctor counts, low hospital density, and missing critical capability evidence."
        )
        return {
            "answer": answer,
            "summary": [
                f"{len(enriched)} regions evaluated",
                f"Threshold: {threshold}",
                "Medical desert score closer to 1 means higher access risk",
            ],
            "findings": [
                f"{r['region_name']}: desert score {r['medical_desert_score']:.2f}, "
                f"{r['total_facilities']} facilities, {r['total_doctors']} doctors, missing {', '.join(r['missing_critical_services'][:4]) or 'no critical gaps detected'}"
                for r in enriched[:8]
            ],
            "recommended_actions": [
                "Validate the top-risk regions with local population and travel-time data",
                "Route clinical volunteers toward regions missing emergency, surgery, obstetrics, or imaging evidence",
                "Collect missing doctor, bed, equipment, and service fields for high-risk rows",
            ],
            "data": {"underserved_regions": enriched},
            "confidence": 0.78,
            "citations": citations[:20],
        }

    def _planning_report(self, query: str, db: Session, parameters: Dict[str, Any]) -> Dict[str, Any]:
        gap = self._gap_report(query, db, parameters)
        anomalies = self._anomaly_report(db, limit=12)
        top_regions = gap["data"].get("underserved_regions", [])[:5]

        actions = [
            "Triage: focus on highest desert-score regions first, then facilities with emergency or referral capability",
            "Verify: call or email cited facilities where capability claims lack matching equipment or staffing evidence",
            "Deploy: match volunteer specialties to missing services, especially surgery, obstetrics, imaging, pediatrics, and emergency care",
            "Invest: fund basic equipment and data-completion work before expanding advanced procedures",
            "Monitor: rerun anomaly and desert scoring after each field update so planners see impact immediately",
        ]

        findings = [
            f"Priority region {idx + 1}: {region['region_name']} with desert score {region['medical_desert_score']:.2f}"
            for idx, region in enumerate(top_regions)
        ]
        findings.extend(anomalies.get("findings", [])[:4])

        return {
            "answer": "Built an adoption-friendly planner: prioritize high-risk regions, verify questionable claims, then route volunteers and investments by missing service.",
            "summary": ["Planner uses desert score, extracted capabilities, staffing, capacity, and anomaly checks"],
            "findings": findings,
            "recommended_actions": actions,
            "data": {
                "priority_regions": top_regions,
                "anomaly_watchlist": anomalies.get("data", {}).get("anomalies", [])[:8],
            },
            "confidence": 0.82,
            "citations": (gap.get("citations", []) + anomalies.get("citations", []))[:20],
        }

    def _anomaly_report(self, db: Session, limit: int = 50) -> Dict[str, Any]:
        facilities = db.query(Facility).limit(limit).all()
        records = []
        citations = []

        for facility in facilities:
            analysis = medical_reasoning_agent.analyze_facility(facility)
            if analysis["anomalies"]:
                records.append({
                    "facility_id": facility.id,
                    "facility_name": facility.name,
                    "city": facility.address_city,
                    "reliability_score": facility.facility_reliability_score,
                    "anomalies": analysis["anomalies"],
                    "recommendations": analysis["recommendations"],
                })
                citations.append(self._citation(facility, "capability/equipment/staffing", "Anomaly check used this facility row"))

        stored = db.query(Anomaly).limit(limit).all()
        for anomaly in stored:
            if anomaly.facility:
                citations.append(self._citation(anomaly.facility, anomaly.detected_field or "stored_anomaly", anomaly.description))

        high = sum(
            1
            for record in records
            for anomaly in record["anomalies"]
            if anomaly.get("severity") == "high"
        )
        answer = f"Detected {len(records)} facilities with suspicious or incomplete claims; {high} high-severity issues need manual verification."
        return {
            "answer": answer,
            "summary": [f"{len(records)} facilities flagged", f"{high} high-severity issues"],
            "findings": [
                f"{record['facility_name']}: {len(record['anomalies'])} issue(s), reliability {(record['reliability_score'] or 0) * 100:.0f}%"
                for record in records[:10]
            ],
            "recommended_actions": [
                "Verify high-severity capability-equipment mismatches first",
                "Request missing equipment, doctor, and capacity fields from hospitals",
                "Do not route advanced procedures to rows with unresolved high-severity anomalies",
            ],
            "data": {"anomalies": records},
            "confidence": 0.76,
            "citations": citations[:20],
        }

    def _geospatial_report(self, query: str, db: Session, parameters: Dict[str, Any]) -> Dict[str, Any]:
        from geospatial import find_facilities_within_radius

        lat = parameters.get("latitude")
        lon = parameters.get("longitude")
        radius = float(parameters.get("radius_km", 25))
        facility_type = parameters.get("facility_type") or self._facility_type_from_query(query)

        if lat is None or lon is None:
            return {
                "answer": "Please provide latitude and longitude parameters for a distance search.",
                "summary": ["Missing coordinates"],
                "findings": [],
                "recommended_actions": ["Use the map or include coordinates for nearby-facility routing"],
                "data": {},
                "confidence": 0.3,
                "citations": [],
            }

        facilities = find_facilities_within_radius(db, float(lat), float(lon), radius, facility_type)
        return {
            "answer": f"Found {len(facilities)} facilities within {radius:g} km of the selected point.",
            "summary": [f"Center: {lat}, {lon}", f"Radius: {radius:g} km"],
            "findings": self._facility_findings(facilities[:10]),
            "recommended_actions": ["Check reliability and service evidence before routing a patient"],
            "data": {"facilities": self._facility_cards(facilities[:25])},
            "confidence": 0.84,
            "citations": [self._citation(f, "coordinates", "Distance search matched this facility") for f in facilities[:15]],
        }

    def _matching_facilities(self, query: str, db: Session) -> List[Facility]:
        facilities = db.query(Facility).all()
        query_lower = query.lower()
        city = self._city_from_query(query, facilities)
        facility_type = self._facility_type_from_query(query)
        terms = _clean_terms(query)

        matches: List[Tuple[int, Facility]] = []
        for facility in facilities:
            if city and (facility.address_city or "").lower() != city.lower():
                continue
            if facility_type and facility.facility_type != facility_type:
                continue

            haystack = self._facility_text(facility)
            score = 0
            for term in terms:
                if term in haystack:
                    score += 2
            for service, keywords in CRITICAL_SERVICE_KEYWORDS.items():
                if service in query_lower and any(keyword in haystack for keyword in keywords):
                    score += 4
            if not terms and (city or facility_type):
                score = 1
            if score > 0:
                matches.append((score, facility))

        matches.sort(key=lambda item: (item[0], item[1].facility_reliability_score or 0), reverse=True)
        return [facility for _, facility in matches]

    def _city_from_query(self, query: str, facilities: List[Facility]) -> Optional[str]:
        query_lower = query.lower()
        cities = sorted({f.address_city for f in facilities if f.address_city}, key=len, reverse=True)
        for city in cities:
            if city.lower() in query_lower:
                return city
        return None

    def _facility_type_from_query(self, query: str) -> Optional[str]:
        query_lower = query.lower()
        for facility_type in FACILITY_TYPES:
            if facility_type in query_lower or f"{facility_type}s" in query_lower:
                return facility_type
        return None

    def _facility_text(self, facility: Facility) -> str:
        values = [
            facility.name,
            facility.facility_type,
            facility.address_city,
            facility.address_state_or_region,
            facility.description,
            facility.mission_statement,
            *_as_list(facility.specialties),
            *_as_list(facility.procedures),
            *_as_list(facility.equipment),
            *_as_list(facility.capabilities),
        ]
        return " ".join(str(value).lower() for value in values if value)

    def _facility_services(self, facility: Facility) -> List[str]:
        haystack = self._facility_text(facility)
        return [
            service
            for service, keywords in CRITICAL_SERVICE_KEYWORDS.items()
            if any(keyword in haystack for keyword in keywords)
        ]

    def _missing_critical_services(self, facilities: List[Facility]) -> List[str]:
        present = set()
        for facility in facilities:
            present.update(self._facility_services(facility))
        return [service for service in CRITICAL_SERVICE_KEYWORDS if service not in present]

    def _facility_cards(self, facilities: List[Facility]) -> List[Dict[str, Any]]:
        return [
            {
                "id": f.id,
                "name": f.name,
                "type": f.facility_type,
                "city": f.address_city,
                "region": f.address_state_or_region,
                "specialties": f.specialties or [],
                "procedures": f.procedures or [],
                "equipment": f.equipment or [],
                "capabilities": f.capabilities or [],
                "doctors": f.number_doctors,
                "capacity": f.capacity,
                "reliability_score": f.facility_reliability_score,
                "medical_desert_score": f.medical_desert_score,
            }
            for f in facilities
        ]

    def _facility_findings(self, facilities: List[Facility]) -> List[str]:
        findings = []
        for facility in facilities:
            services = self._facility_services(facility)
            service_text = ", ".join(services[:4]) if services else "limited explicit capability evidence"
            findings.append(
                f"{facility.name} ({facility.address_city or 'unknown city'}): {service_text}; "
                f"reliability {(facility.facility_reliability_score or 0) * 100:.0f}%"
            )
        return findings

    def _citation(self, facility: Facility, field: str, evidence: str) -> Dict[str, Any]:
        raw = facility.raw_data or {}
        return {
            "facility_id": facility.id,
            "row_id": raw.get("pk_unique_id") or raw.get("content_table_id") or facility.unique_id,
            "facility_name": facility.name,
            "field": field,
            "evidence": evidence,
            "source_url": facility.source_url,
        }

    def _best_citation(self, facility: Facility, query: str) -> Dict[str, Any]:
        query_terms = _clean_terms(query)
        fields = {
            "procedure": facility.procedures or [],
            "equipment": facility.equipment or [],
            "capability": facility.capabilities or [],
            "specialties": facility.specialties or [],
            "description": [facility.description or ""],
        }
        for field, values in fields.items():
            for value in values:
                value_text = str(value)
                lower = value_text.lower()
                if any(term in lower for term in query_terms):
                    return self._citation(facility, field, value_text[:220])
        return self._citation(facility, "row", "Facility row matched the query context")


healthcare_intelligence_agent = HealthcareIntelligenceAgent()
