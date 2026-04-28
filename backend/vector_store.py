from config import settings
from typing import List, Dict, Any
import json
from difflib import SequenceMatcher


class VectorStore:
    """Simple in-memory vector store using text similarity"""
    
    def __init__(self):
        self.facilities = {}  # id -> {text, metadata}
        self.procedures = {}  # id -> {text, metadata}
    
    def add_facility(self, facility_id: str, text: str, metadata: Dict[str, Any]):
        """Add a facility to the vector store"""
        self.facilities[facility_id] = {
            "text": text,
            "metadata": metadata
        }
    
    def add_procedure(self, procedure_id: str, text: str, metadata: Dict[str, Any]):
        """Add a procedure to the vector store"""
        self.procedures[procedure_id] = {
            "text": text,
            "metadata": metadata
        }
    
    def _similarity(self, query: str, text: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        return SequenceMatcher(None, query.lower(), text.lower()).ratio()
    
    def search_facilities(self, query: str, n_results: int = 10) -> Dict:
        """Search facilities by text similarity"""
        query_lower = query.lower()
        results = []
        
        for fid, data in self.facilities.items():
            similarity = self._similarity(query, data["text"])
            if similarity > 0.1:  # Threshold for relevance
                results.append({
                    "text": data["text"],
                    "metadata": data["metadata"],
                    "similarity": similarity
                })
        
        # Sort by similarity and return top n
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:n_results]
        
        return {
            "results": results,
            "count": len(results)
        }
    
    def search_procedures(self, query: str, n_results: int = 10) -> Dict:
        """Search procedures by text similarity"""
        query_lower = query.lower()
        results = []
        
        for pid, data in self.procedures.items():
            similarity = self._similarity(query, data["text"])
            if similarity > 0.1:
                results.append({
                    "text": data["text"],
                    "metadata": data["metadata"],
                    "similarity": similarity
                })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:n_results]
        
        return {
            "results": results,
            "count": len(results)
        }
    
    def hybrid_search(self, query: str, facility_ids: List[str], n_results: int = 5) -> Dict:
        """Hybrid search combining similarity and filtered results"""
        if facility_ids:
            # Search only within specified IDs
            results = []
            for fid in facility_ids:
                if fid in self.facilities:
                    similarity = self._similarity(query, self.facilities[fid]["text"])
                    if similarity > 0.1:
                        results.append({
                            "text": self.facilities[fid]["text"],
                            "metadata": self.facilities[fid]["metadata"],
                            "similarity": similarity
                        })
        else:
            # Search all
            return self.search_facilities(query, n_results)
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:n_results]
        
        return {
            "results": results,
            "count": len(results)
        }
    
    def delete_facility(self, facility_id: str):
        """Delete a facility from the vector store"""
        if facility_id in self.facilities:
            del self.facilities[facility_id]
    
    def get_facility_count(self) -> int:
        """Get total number of facilities in vector store"""
        return len(self.facilities)


vector_store = VectorStore()
