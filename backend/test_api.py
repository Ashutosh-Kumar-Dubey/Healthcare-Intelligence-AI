"""
Test script to verify API endpoints are working
Run this after starting the backend server
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))

def test_health_check():
    response = requests.get(f"{BASE_URL}/")
    print_response("Health Check", response)

def test_overview_stats():
    response = requests.get(f"{BASE_URL}/api/stats/overview")
    print_response("Overview Statistics", response)

def test_facilities():
    response = requests.get(f"{BASE_URL}/api/facilities?limit=5")
    print_response("List Facilities (limit 5)", response)

def test_map_facilities():
    response = requests.get(f"{BASE_URL}/api/map/facilities")
    print_response("Map Facilities", response)

def test_query_count():
    response = requests.post(
        f"{BASE_URL}/api/query",
        json={"query": "How many hospitals are there?"}
    )
    print_response("Query: Count Hospitals", response)

def test_query_semantic():
    response = requests.post(
        f"{BASE_URL}/api/query",
        json={"query": "Find facilities with cardiology"}
    )
    print_response("Query: Semantic Search (Cardiology)", response)

def test_geospatial_nearby():
    response = requests.post(
        f"{BASE_URL}/api/geospatial/nearby",
        json={
            "latitude": 7.9465,
            "longitude": -1.0232,
            "radius_km": 50
        }
    )
    print_response("Geospatial: Nearby Facilities", response)

def test_underserved_regions():
    response = requests.get(f"{BASE_URL}/api/geospatial/underserved?threshold=0.7")
    print_response("Underserved Regions", response)

def test_heatmap():
    response = requests.get(f"{BASE_URL}/api/map/heatmap?heatmap_type=physician_density")
    print_response("Heatmap: Physician Density", response)

def test_anomalies():
    response = requests.get(f"{BASE_URL}/api/anomalies?limit=5")
    print_response("Anomalies", response)

def main():
    print("Testing Healthcare Intelligence AI API")
    print(f"Base URL: {BASE_URL}")
    
    try:
        test_health_check()
        test_overview_stats()
        test_facilities()
        test_map_facilities()
        test_query_count()
        test_query_semantic()
        test_geospatial_nearby()
        test_underserved_regions()
        test_heatmap()
        test_anomalies()
        
        print(f"\n{'='*60}")
        print("All tests completed!")
        print(f"{'='*60}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API.")
        print("Make sure the backend server is running on http://localhost:8000")
        print("Run: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
