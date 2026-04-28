# Quick Start Guide

## Fastest Way to Run the System

### Option 1: Run with Sample Data (No CSV Required)

The system will work with empty database initially and populate as you use it.

#### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

Backend will run on `http://localhost:8000`

#### Frontend (New Terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm start
```

Frontend will open at `http://localhost:3000`

### Option 2: Ingest Real Data

#### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Ingest data (this will take a few minutes due to geocoding)
python ingest_data.py "..\Virtue Foundation Ghana v0.3 - Sheet1.csv"

# Start the server
python main.py
```

#### Frontend (Same as above)

```bash
cd frontend
npm install
npm start
```

## Verify It's Working

### Check Backend
Open `http://localhost:8000` in your browser - you should see:
```json
{
  "message": "Healthcare Intelligence AI API",
  "version": "1.0.0",
  "status": "running"
}
```

### Check API Docs
Open `http://localhost:8000/docs` - you'll see interactive Swagger UI

### Check Frontend
Open `http://localhost:3000` - you'll see the map interface

### Run API Tests
```bash
cd backend
python test_api.py
```

## Try Example Queries

In the frontend Query Panel, try:

1. **"How many hospitals are there?"**
   - Returns count of hospitals

2. **"Show me underserved regions"**
   - Lists medical deserts

3. **"Find facilities with cardiology"**
   - Semantic search for cardiology

4. **"Detect facilities with anomalies"**
   - Shows data quality issues

## Map Features

Click the **Layers** button (top) to toggle:
- **Facilities** - All healthcare markers
- **Physician Density** - Heatmap of doctors per facility
- **Hospital Density** - Heatmap of hospital concentration
- **Medical Desert** - Heatmap of underserved areas

Click on any marker to see facility details and AI analysis.

## Troubleshooting

**Backend won't start:**
- Check if port 8000 is in use
- Try `python main.py` again

**Frontend won't start:**
- Check if port 3000 is in use
- Try `npm start` again

**Map shows blank:**
- Ensure backend is running
- Check browser console (F12) for errors

**No data showing:**
- Run data ingestion: `python ingest_data.py <path_to_csv>`
- Or use the system without data (some features limited)

## Next Steps

1. Read `SETUP.md` for detailed setup
2. Read `ARCHITECTURE.md` for system design
3. Read `README.md` for full documentation
