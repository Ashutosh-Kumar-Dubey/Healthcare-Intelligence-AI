# Healthcare Intelligence AI

A complete agentic AI system for global healthcare intelligence that identifies "medical deserts" and connects healthcare demand with actual infrastructure.

## 🎯 Core Features

- **Multi-Agent System**: Supervisor, Text-to-SQL, Vector Search, Medical Reasoning, and Geospatial agents
- **Hybrid Retrieval**: SQL + semantic search using Chroma vector database
- **Medical Desert Detection**: AI-powered identification of underserved regions
- **Anomaly Detection**: Identifies data inconsistencies and unrealistic claims
- **Interactive Map**: Leaflet.js with heatmaps for physician density, hospital density, and medical desert scores
- **Premium UI**: Dark theme with glassmorphism, Framer Motion animations

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│  (Leaflet Map, Query Panel, Insights, Layer Control)        │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Multi-Agent System                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │  │
│  │  │Supervisor│  │Text-to-SQL│  │  Vector Search   │    │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘    │  │
│  │  ┌──────────┐  ┌──────────┐                           │  │
│  │  │Medical   │  │Geospatial│                           │  │
│  │  │Reasoning │  │Agent     │                           │  │
│  │  └──────────┘  └──────────┘                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
│  PostgreSQL  │  │   Chroma   │  │   SQLite   │
│   Database   │  │ Vector DB  │  │  (fallback)│
└──────────────┘  └────────────┘  └────────────┘
```

## 📊 Database Schema

### Facilities Table
- Basic info: name, type, organization
- Location: address, lat/lon
- Healthcare data: specialties, procedures, equipment, capabilities
- Capacity: doctors, capacity
- Scoring: reliability_score, medical_desert_score

### Anomalies Table
- Type: capability_equipment_mismatch, unrealistic_claim, missing_infrastructure
- Severity: low, medium, high
- Confidence score

### Medical Deserts Table
- Region scores: physician_density, hospital_density, medical_desert_score
- Gap analysis metrics

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- (Optional) PostgreSQL for production

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env if needed (uses SQLite by default)

# Run data ingestion (optional - uses sample data)
python data_ingestion.py "../Virtue Foundation Ghana v0.3 - Sheet1.csv"

# Start the backend server
python main.py
```

Backend will run on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

Frontend will run on `http://localhost:3000`

## 📡 API Endpoints

### Query & Analysis
- `POST /api/query` - Process natural language queries
- `POST /api/geospatial/nearby` - Find facilities within radius
- `POST /api/geospatial/medical-desert` - Calculate desert score
- `GET /api/geospatial/underserved` - Get underserved regions

### Facilities
- `GET /api/facilities` - List facilities with filters
- `GET /api/facilities/{id}` - Get specific facility
- `GET /api/facilities/{id}/analysis` - Get facility analysis

### Anomalies
- `GET /api/anomalies` - List anomalies with filters

### Statistics
- `GET /api/stats/overview` - Overview statistics
- `GET /api/stats/by-region` - Statistics by region

### Map Data
- `GET /api/map/facilities` - Facilities for map
- `GET /api/map/heatmap` - Heatmap data

## 🧠 Agent Capabilities

### Supervisor Agent
Routes queries to appropriate agents based on intent:
- Count queries → Text-to-SQL
- Geospatial queries → Geospatial Agent
- Gap/shortage queries → Gap Analysis
- Anomaly queries → Medical Reasoning
- Semantic queries → Vector Search

### Text-to-SQL Agent
Converts natural language to SQL queries:
- "How many hospitals in Accra?" → `SELECT COUNT(*) FROM facilities WHERE facility_type='hospital' AND address_city='Accra'`

### Vector Search Agent
Semantic search using Chroma:
- Finds facilities by capability, specialty, or description
- Handles unstructured text queries

### Medical Reasoning Agent
Detects anomalies:
- Capability vs equipment mismatch
- Unrealistic capacity claims
- Missing infrastructure
- Computes reliability scores

### Geospatial Agent
Spatial analysis:
- Find facilities within X km
- Calculate medical desert scores
- Detect underserved regions
- Uses Haversine formula for distances

## 🗺️ Map Features

### Layers
- **Facilities**: All healthcare facilities with custom markers
- **Physician Density**: Heatmap showing doctors per facility
- **Hospital Density**: Heatmap showing hospital concentration
- **Medical Desert**: Heatmap highlighting underserved regions

### Interactions
- Click markers for facility details
- Toggle layers dynamically
- Map updates based on query results
- Dark mode map tiles

## 📝 Example Queries

1. **Count Query**: "How many hospitals are in Accra?"
2. **Geospatial**: "Find facilities within 10km of 7.9465, -1.0232"
3. **Gap Analysis**: "Show me underserved regions"
4. **Anomaly Detection**: "Detect facilities with data anomalies"
5. **Semantic**: "Find facilities offering cardiology services"

## 🏆 Bonus Features

- **Citation Tracing**: Shows which data sources were used
- **Confidence Scores**: AI confidence for each answer
- **Facility Anomaly Scoring**: Data quality assessment
- **Medical Desert Score Formula**: 
  ```
  Service Level = (Physician Density Score + Hospital Density Score) / 2
  Medical Desert Score = 1.0 - Service Level
  ```

## 🔧 Configuration

### Backend (backend/.env)
```
DATABASE_URL=sqlite:///./healthcare.db
OPENAI_API_KEY=your_key_here  # Optional, for enhanced NLP
CHROMA_PERSIST_DIR=./chroma_db
```

### Frontend
Uses proxy to backend (configured in package.json)

## 📦 Tech Stack

**Backend:**
- FastAPI - Web framework
- SQLAlchemy - ORM
- ChromaDB - Vector database
- LangChain - AI framework
- GeoPy - Geocoding

**Frontend:**
- React - UI framework
- TailwindCSS - Styling
- Framer Motion - Animations
- Leaflet - Maps
- Lucide React - Icons

## 🧪 Testing

Test the system with the built-in example queries in the Query Panel, or use curl:

```bash
# Count facilities
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How many hospitals are there?"}'

# Find nearby facilities
curl -X POST http://localhost:8000/api/geospatial/nearby \
  -H "Content-Type: application/json" \
  -d '{"latitude": 7.9465, "longitude": -1.0232, "radius_km": 10}'

# Get underserved regions
curl http://localhost:8000/api/geospatial/underserved?threshold=0.7
```

## 📄 License

This project is built for the Virtue Foundation + Accenture Databricks Hackathon Challenge.

## 🙏 Acknowledgments

- Virtue Foundation for healthcare data
- Accenture & Databricks for the challenge
- OpenStreetMap for map tiles
- All open-source libraries used
