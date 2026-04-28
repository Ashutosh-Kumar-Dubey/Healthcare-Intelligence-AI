import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Activity, Layers, BarChart3, X, Building2 } from 'lucide-react';
import MapView from './components/MapView';
import QueryPanel from './components/QueryPanel';
import InsightsPanel from './components/InsightsPanel';
import LayerControl from './components/LayerControl';
import StatsOverview from './components/StatsOverview';
import { apiUrl } from './api';
import './App.css';

const workflowTabs = [
  { id: 'query', label: 'Ask Agent', icon: Search },
  { id: 'layers', label: 'Map Modes', icon: Layers },
  { id: 'stats', label: 'Snapshot', icon: BarChart3 },
];

function App() {
  const [showQueryPanel, setShowQueryPanel] = useState(true);
  const [showInsights, setShowInsights] = useState(false);
  const [showLayers, setShowLayers] = useState(false);
  const [showStats, setShowStats] = useState(true);
  const [showFacilityPanel, setShowFacilityPanel] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [mapFocusTarget, setMapFocusTarget] = useState(null);
  const [activeLayers, setActiveLayers] = useState({
    facilities: true,
    physicianDensity: false,
    hospitalDensity: false,
    medicalDesert: false
  });

  const handleQuery = async (query, parameters = {}) => {
    try {
      const response = await fetch(apiUrl('/api/query'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, parameters }),
      });
      const data = await response.json();
      setQueryResult(data);
      setShowInsights(true);
      
      // Update map based on query type
      if (data.query_type === 'geospatial' && data.data.facilities) {
        // Map will handle this through props
      }
    } catch (error) {
      console.error('Query error:', error);
    }
  };

  const handleFacilitySelect = (facility) => {
    setSelectedFacility(facility);
    setShowFacilityPanel(true);
  };

  const handleResultFocus = (target) => {
    setMapFocusTarget({
      ...target,
      requestedAt: Date.now()
    });
  };

  const toggleLayer = (layer) => {
    setActiveLayers(prev => ({
      ...prev,
      ...(layer !== 'facilities' ? {
        physicianDensity: false,
        hospitalDensity: false,
        medicalDesert: false
      } : {}),
      [layer]: !prev[layer]
    }));
  };

  const toggleWorkflow = (id) => {
    if (id === 'query') {
      setShowQueryPanel((value) => !value);
    }
    if (id === 'layers') {
      setShowLayers((value) => !value);
    }
    if (id === 'stats') {
      setShowStats((value) => !value);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <motion.header 
        className="header"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="header-content">
          <div className="logo">
            <Activity className="logo-icon" />
            <div>
              <h1>Healthcare Intelligence AI</h1>
              <p>Virtue Foundation medical desert command layer</p>
            </div>
          </div>
          <div className="header-actions">
            <span className="live-pill">Live Ghana dataset</span>
            {workflowTabs.map((tab) => {
              const Icon = tab.icon;
              const active = (
                (tab.id === 'query' && showQueryPanel) ||
                (tab.id === 'layers' && showLayers) ||
                (tab.id === 'stats' && showStats)
              );

              return (
                <motion.button
                  key={tab.id}
                  className={`workflow-button ${active ? 'active' : ''}`}
                  onClick={() => toggleWorkflow(tab.id)}
                  whileHover={{ y: -1 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Icon size={17} />
                  <span>{tab.label}</span>
                </motion.button>
              );
            })}
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="main-content">
        <div className="map-context-strip">
          <span className={activeLayers.facilities ? 'active' : ''}>Facilities</span>
          <span className={activeLayers.physicianDensity ? 'active' : ''}>Physician Density</span>
          <span className={activeLayers.hospitalDensity ? 'active' : ''}>Hospital Density</span>
          <span className={activeLayers.medicalDesert ? 'active' : ''}>Medical Desert</span>
        </div>

        {/* Map View */}
        <div className="map-container">
          <MapView
            activeLayers={activeLayers}
            onFacilitySelect={handleFacilitySelect}
            focusTarget={mapFocusTarget}
          />
        </div>

        {/* Query Panel */}
        <AnimatePresence>
          {showQueryPanel && (
            <motion.div
              className="panel query-panel"
              initial={{ x: -400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -400, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <button
                className="close-button"
                onClick={() => setShowQueryPanel(false)}
              >
                <X size={20} />
              </button>
              <QueryPanel onQuery={handleQuery} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Insights Panel */}
        <AnimatePresence>
          {showInsights && queryResult && (
            <motion.div
              className="panel insights-panel"
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <button
                className="close-button"
                onClick={() => setShowInsights(false)}
              >
                <X size={20} />
              </button>
              <InsightsPanel
                queryResult={queryResult}
                selectedFacility={null}
                onFacilityFocus={handleResultFocus}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Facility Details Panel */}
        <AnimatePresence>
          {showFacilityPanel && selectedFacility && (
            <motion.div
              className="panel facility-panel"
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <button
                className="close-button"
                onClick={() => setShowFacilityPanel(false)}
              >
                <X size={20} />
              </button>
              <div className="facility-panel-kicker">
                <Building2 size={16} />
                Facility Profile
              </div>
              <InsightsPanel
                queryResult={null}
                selectedFacility={selectedFacility}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Layer Control */}
        <AnimatePresence>
          {showLayers && (
            <motion.div
              className="panel layer-panel"
              initial={{ y: -300, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -300, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <LayerControl
                activeLayers={activeLayers}
                onToggleLayer={toggleLayer}
                onClose={() => setShowLayers(false)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Stats Overview */}
        <AnimatePresence>
          {showStats && (
            <motion.div
              className={`stats-container ${showQueryPanel ? 'with-query' : ''} ${(showInsights || showFacilityPanel) ? 'with-insights' : ''}`}
              initial={{ y: -100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -100, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <StatsOverview />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
