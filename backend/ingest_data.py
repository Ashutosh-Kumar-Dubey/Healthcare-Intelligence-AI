"""
Script to ingest healthcare data from CSV
Usage: python ingest_data.py <path_to_csv>
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_ingestion import ingest_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_data.py <path_to_csv>")
        print("Example: python ingest_data.py '../Virtue Foundation Ghana v0.3 - Sheet1.csv'")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    print(f"Starting data ingestion from {csv_path}...")
    ingest_data(csv_path)
