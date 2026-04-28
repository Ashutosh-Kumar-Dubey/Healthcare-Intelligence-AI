# Setup Instructions

## Step-by-Step Installation Guide

### 1. Clone/Download the Project

Navigate to the project directory:
```bash
cd "c:\Users\Yuvraj Goyal\OneDrive\Desktop\New folder (9)\healthcare-intelligence-ai"
```

### 2. Backend Setup

#### 2.1 Create Python Virtual Environment (Recommended)

```bash
cd backend
python -m venv venv
```

#### 2.2 Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

#### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.4 Configure Environment

```bash
# Copy the example environment file
copy .env.example .env
```

Edit `.env` if needed. By default, it uses SQLite (no setup required). For PostgreSQL:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/healthcare_intelligence
```

#### 2.5 Ingest Data (Optional)

The system can work without data ingestion for testing, but for full functionality:

```bash
python ingest_data.py "..\Virtue Foundation Ghana v0.3 - Sheet1.csv"
```

**Note:** This will:
- Parse the CSV file
- Geocode addresses (requires internet, may take time)
- Store data in database
- Build vector embeddings
- Detect anomalies

**For faster testing without geocoding**, the system will work with sample data once you run it.

#### 2.6 Start Backend Server

```bash
python main.py
```

The backend will start on `http://localhost:8000`

You can verify it's working by visiting:
- `http://localhost:8000` - API root
- `http://localhost:8000/docs` - Interactive API documentation (Swagger)

### 3. Frontend Setup

#### 3.1 Install Node.js Dependencies

Open a new terminal (keep backend running):

```bash
cd frontend
npm install
```

#### 3.2 Start Frontend Development Server

```bash
npm start
```

The frontend will open at `http://localhost:3000`

### 4. Using the Application

1. Open your browser to `http://localhost:3000`
2. You'll see an interactive map of Ghana
3. Use the **Query Panel** (left) to ask questions:
   - "How many hospitals are in Accra?"
   - "Show me underserved regions"
   - "Find facilities with cardiology"
4. Use the **Layers Control** (top) to toggle map layers:
   - Facilities
   - Physician Density (heatmap)
   - Hospital Density (heatmap)
   - Medical Desert (heatmap)
5. Click on facility markers to see details
6. View **AI Insights** (right panel) for analysis results

### 5. Testing API Endpoints

Use the interactive Swagger UI at `http://localhost:8000/docs` or curl:

```bash
# Get overview statistics
curl http://localhost:8000/api/stats/overview

# Get facilities for map
curl http://localhost:8000/api/map/facilities

# Process a query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How many hospitals are there?"}'
```

### 6. Troubleshooting

#### Backend Issues

**Port 8000 already in use:**
```bash
# Edit main.py and change the port:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Import errors:**
```bash
# Ensure you're in the backend directory
cd backend
pip install -r requirements.txt
```

**Database errors:**
- Delete `healthcare.db` and `chroma_db` folder to start fresh
- The system will recreate them on next run

#### Frontend Issues

**Port 3000 already in use:**
```bash
# The terminal will show an alternative port (usually 3001)
# Or kill the process using port 3000
```

**Map not loading:**
- Check that backend is running on port 8000
- Check browser console for errors (F12)
- Ensure internet connection for map tiles

**CORS errors:**
- The backend has CORS enabled for all origins
- If issues persist, check backend console

#### Data Ingestion Issues

**Geocoding timeouts:**
- The script uses Nominatim (OpenStreetMap) which has rate limits
- If it fails, the system will still work with lat/lon = None
- You can add coordinates manually later

**Memory issues:**
- Process the CSV in chunks if it's very large
- Edit `data_ingestion.py` to batch process

### 7. Production Deployment

For production deployment:

#### Backend
- Use PostgreSQL instead of SQLite
- Set up environment variables properly
- Use a production WSGI server (Gunicorn)
- Enable HTTPS
- Set up proper CORS origins

#### Frontend
- Build the production bundle: `npm run build`
- Serve with nginx or similar
- Configure API proxy

### 8. Optional: Using PostgreSQL

If you want to use PostgreSQL instead of SQLite:

1. Install PostgreSQL
2. Create a database:
```sql
CREATE DATABASE healthcare_intelligence;
```

3. Update `.env`:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/healthcare_intelligence
```

4. Install psycopg2-binary (already in requirements.txt)

The system will automatically use PostgreSQL when configured.

### 9. Data Sources

The system is designed to work with the Virtue Foundation Ghana healthcare dataset. The CSV should contain:
- Facility names and addresses
- Specialties, procedures, equipment
- Capabilities and descriptions
- Contact information

You can adapt the ingestion pipeline for other datasets by modifying `data_ingestion.py`.

### 10. Support

For issues or questions:
1. Check the API docs at `http://localhost:8000/docs`
2. Review the code comments
3. Check the main README.md for architecture details
