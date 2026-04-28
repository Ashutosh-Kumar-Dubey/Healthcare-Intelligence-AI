# System Architecture

## Overview

The Healthcare Intelligence AI system is a multi-agent architecture that combines structured database queries with semantic vector search to provide intelligent healthcare infrastructure analysis.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Query Panel  │  │  Map View    │  │ Insights     │          │
│  │              │  │              │  │ Panel        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API LAYER                               │  │
│  │  /api/query, /api/facilities, /api/geospatial, etc.     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │              MULTI-AGENT ORCHESTRATION                    │  │
│  │                                                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐      │  │
│  │  │ Supervisor │──│Text-to-SQL │──│Vector Search │      │  │
│  │  │  Agent     │  │  Agent     │  │   Agent      │      │  │
│  │  └────────────┘  └────────────┘  └──────────────┘      │  │
│  │         │                │                │              │  │
│  │         └────────────────┼────────────────┘              │  │
│  │                          │                               │  │
│  │  ┌────────────┐  ┌────────────┐                        │  │
│  │  │ Medical    │  │ Geospatial │                        │  │
│  │  │ Reasoning  │  │   Agent    │                        │  │
│  │  └────────────┘  └────────────┘                        │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   PostgreSQL   │  │    ChromaDB     │  │     SQLite      │
│   (Structured) │  │   (Vector)      │  │   (Fallback)    │
│                │  │                 │  │                 │
│ • Facilities   │  │ • Facility      │  │ • Same as       │
│ • Anomalies    │  │   embeddings   │  │   PostgreSQL    │
│ • Medical      │  │ • Procedure     │  │                 │
│   Deserts      │  │   embeddings   │  │                 │
└────────────────┘  └─────────────────┘  └─────────────────┘
```

## Agent Details

### 1. Supervisor Agent

**Purpose:** Query classification and routing

**Input:** Natural language query string

**Process:**
1. Analyze query for keywords
2. Determine query type:
   - Count queries: "how many", "count"
   - Geospatial: "within", "near", "radius"
   - Gap analysis: "gap", "shortage", "desert"
   - Anomaly detection: "anomaly", "inconsistent"
   - Default: semantic search

**Output:** Query type label

**File:** `backend/agents.py` - `SupervisorAgent`

### 2. Text-to-SQL Agent

**Purpose:** Convert natural language to SQL queries

**Input:** Query string, database session

**Process:**
1. Extract entities (specialty, facility type, location)
2. Generate appropriate SQL query
3. Execute query
4. Return results

**Example:**
```
Input: "How many hospitals in Accra?"
SQL: SELECT COUNT(*) FROM facilities 
     WHERE facility_type='hospital' AND address_city='Accra'
```

**File:** `backend/agents.py` - `TextToSQLAgent`

### 3. Vector Search Agent

**Purpose:** Semantic search using vector embeddings

**Input:** Query string, number of results

**Process:**
1. Use ChromaDB to search facility embeddings
2. Return top-k similar facilities
3. Include similarity scores

**Use Cases:**
- Find facilities by capability description
- Semantic matching of specialties
- Unstructured text queries

**File:** `backend/agents.py` - `VectorSearchAgent`

### 4. Medical Reasoning Agent

**Purpose:** Detect anomalies and assess data quality

**Input:** Facility object

**Process:**
1. Check capability vs equipment mismatch
2. Detect unrealistic claims (capacity vs doctors)
3. Identify missing infrastructure
4. Compute reliability score (0-1)

**Scoring Formula:**
```
Base Score = 1.0
- Missing name: -0.2
- Missing location: -0.1
- Missing specialties: -0.15
- Missing capabilities: -0.1
- Missing capacity info: -0.15
- Missing contact: -0.1
- Missing geolocation: -0.1
- Anomaly deductions: severity * confidence

Reliability Score = max(0, Base Score - deductions)
```

**File:** `backend/medical_reasoning.py`

### 5. Geospatial Agent

**Purpose:** Spatial analysis and medical desert detection

**Input:** Coordinates, radius, region name

**Process:**
1. Use Haversine formula for distance calculations
2. Find facilities within radius
3. Calculate density scores
4. Compute medical desert score

**Medical Desert Score Formula:**
```
Physician Density Score = min(doctors_per_100k / 230, 1.0)
Hospital Density Score = min(hospitals_per_100k / 5, 1.0)
Service Level = (Physician Density + Hospital Density) / 2
Medical Desert Score = 1.0 - Service Level
```

**File:** `backend/geospatial.py`, `backend/agents.py` - `GeospatialAgent`

## Data Flow

### Query Processing Flow

```
User Query
    ↓
Supervisor Agent (classify)
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│         │         │         │         │
Count   Geospatial  Gap    Anomaly  Semantic
    ↓         ↓         ↓        ↓        ↓
Text-to-  Geospatial  Gap    Medical  Vector
SQL       Agent      Analysis Reasoning Search
    ↓         ↓         ↓        ↓        ↓
PostgreSQL PostgreSQL Postgres Postgres ChromaDB
    ↓         ↓         ↓        ↓        ↓
Aggregate Results
    ↓
Format Response (with confidence, citations)
    ↓
Return to Frontend
```

### Data Ingestion Flow

```
CSV File
    ↓
Parse Rows
    ↓
Extract JSON Fields (specialties, procedures, etc.)
    ↓
Geocode Addresses (Nominatim API)
    ↓
Extract Procedures/Equipment from Capabilities
    ↓
Create Facility Record
    ↓
Compute Reliability Score
    ↓
Store in PostgreSQL
    ↓
Create Vector Embedding
    ↓
Store in ChromaDB
    ↓
Detect Anomalies
    ↓
Store Anomalies in PostgreSQL
```

## Database Schema

### Facilities Table

```sql
CREATE TABLE facilities (
    id INTEGER PRIMARY KEY,
    unique_id VARCHAR UNIQUE,
    name VARCHAR,
    source_url VARCHAR,
    facility_type VARCHAR,  -- hospital, clinic, etc.
    organization_type VARCHAR,
    
    -- Location
    address_line1 VARCHAR,
    address_line2 VARCHAR,
    address_city VARCHAR,
    address_state_or_region VARCHAR,
    address_country VARCHAR,
    latitude FLOAT,
    longitude FLOAT,
    
    -- Healthcare data
    specialties JSON,  -- List of specialties
    procedures JSON,   -- List of procedures
    equipment JSON,    -- List of equipment
    capabilities JSON, -- List of capabilities
    
    -- Capacity
    number_doctors INTEGER,
    capacity INTEGER,
    
    -- Contact
    phone_numbers JSON,
    email VARCHAR,
    websites JSON,
    
    -- Additional
    year_established INTEGER,
    description TEXT,
    mission_statement TEXT,
    
    -- Scoring
    facility_reliability_score FLOAT DEFAULT 1.0,
    medical_desert_score FLOAT DEFAULT 0.0,
    
    -- Raw data
    raw_data JSON
);
```

### Anomalies Table

```sql
CREATE TABLE anomalies (
    id INTEGER PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    anomaly_type VARCHAR,  -- capability_equipment_mismatch, etc.
    severity VARCHAR,      -- low, medium, high
    description TEXT,
    confidence_score FLOAT,
    detected_field VARCHAR,
    expected_value VARCHAR,
    actual_value VARCHAR
);
```

### Medical Deserts Table

```sql
CREATE TABLE medical_deserts (
    id INTEGER PRIMARY KEY,
    region_name VARCHAR,
    region_type VARCHAR,  -- city, state
    
    -- Scores
    physician_density_score FLOAT,
    hospital_density_score FLOAT,
    medical_desert_score FLOAT,
    
    -- Counts
    total_facilities INTEGER,
    total_doctors INTEGER,
    total_capacity INTEGER,
    
    -- Gap analysis
    population_estimate INTEGER,
    facilities_per_100k FLOAT,
    doctors_per_100k FLOAT,
    
    -- Coordinates
    center_latitude FLOAT,
    center_longitude FLOAT,
    radius_km FLOAT
);
```

## Vector Database Schema

### Facilities Collection

```
Document: Combined text of name, specialties, procedures, equipment, capabilities, description
Metadata:
  - id: facility unique_id
  - name: facility name
  - facility_type: hospital/clinic
  - city: address city
  - specialties: JSON string
  - latitude: float
  - longitude: float
```

### Procedures Collection

```
Document: Procedure description
Metadata:
  - id: procedure unique_id
  - facility_id: related facility
  - type: procedure type
```

## API Endpoints

### Query & Analysis
- `POST /api/query` - Main AI query endpoint
- `POST /api/geospatial/nearby` - Find facilities within radius
- `POST /api/geospatial/medical-desert` - Calculate desert score
- `GET /api/geospatial/underserved` - List underserved regions

### Facilities
- `GET /api/facilities` - List with filters (type, city, pagination)
- `GET /api/facilities/{id}` - Get single facility
- `GET /api/facilities/{id}/analysis` - Get anomaly analysis

### Anomalies
- `GET /api/anomalies` - List with filters (severity, pagination)

### Statistics
- `GET /api/stats/overview` - Global statistics
- `GET /api/stats/by-region` - Regional statistics

### Map Visualization
- `GET /api/map/facilities` - Facilities with coordinates
- `GET /api/map/heatmap` - Heatmap data (physician/hospital/desert)

### Data Ingestion
- `POST /api/ingest` - Trigger data ingestion from CSV

## Frontend Architecture

### Component Structure

```
App.js
├── Header (logo, controls)
├── MapView (Leaflet map)
│   ├── Markers (facilities)
│   └── HeatmapLayer (density/desert)
├── QueryPanel (AI query input)
├── InsightsPanel (results display)
├── LayerControl (map layer toggles)
└── StatsOverview (statistics cards)
```

### State Management

- Local component state for UI panels
- API calls for data fetching
- No global state management (Redux) for simplicity

### Styling

- TailwindCSS for utility classes
- Custom CSS for glassmorphism effects
- Framer Motion for animations

## Technology Choices

### Backend

**FastAPI:** Modern, fast Python web framework with automatic API docs

**SQLAlchemy:** Powerful ORM with support for multiple databases

**ChromaDB:** Open-source vector database, easy to set up, no API keys needed

**LangChain:** AI framework for building agent systems

**GeoPy:** Geocoding library using Nominatim (free, no API key)

### Frontend

**React:** Component-based UI library

**Leaflet:** Open-source mapping library (free, no API key)

**Framer Motion:** Smooth animations

**TailwindCSS:** Utility-first CSS framework

**Lucide React:** Beautiful icon library

## Scalability Considerations

### Current Design
- SQLite for simplicity (can switch to PostgreSQL)
- ChromaDB with local persistence
- Single-server deployment

### Scaling Up
- Switch to PostgreSQL for production
- Use cloud vector database (Pinecone, Weaviate)
- Add Redis caching
- Deploy with Docker/Kubernetes
- Add load balancer
- Implement rate limiting
- Add authentication/authorization

## Security Considerations

### Current
- CORS enabled for all origins (development)
- No authentication (development mode)
- Input validation via Pydantic

### Production Additions
- Restrict CORS origins
- Add API key authentication
- Rate limiting
- Input sanitization
- SQL injection prevention (SQLAlchemy handles this)
- HTTPS only
- Environment variable management
