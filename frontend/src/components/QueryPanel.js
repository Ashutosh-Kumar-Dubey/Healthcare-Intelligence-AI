import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Map, Route, SearchCheck, Send, Sparkles } from 'lucide-react';
import './components.css';

const exampleQueries = [
  {
    icon: AlertTriangle,
    label: 'Find care gaps',
    query: 'Which regions are medical deserts and what critical services are missing?'
  },
  {
    icon: Route,
    label: 'Build deployment plan',
    query: 'Create a volunteer deployment plan for the highest-risk regions'
  },
  {
    icon: SearchCheck,
    label: 'Match capabilities',
    query: 'Find facilities with maternity, surgery, or emergency capability'
  },
  {
    icon: Map,
    label: 'Verify claims',
    query: 'Detect suspicious facility capability claims'
  }
];

function QueryPanel({ onQuery }) {
  const [query, setQuery] = useState('');
  const [parameters, setParameters] = useState({});
  const [showExamples, setShowExamples] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onQuery(query, parameters);
      setQuery('');
      setParameters({});
      setShowExamples(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery.query);
    setShowExamples(false);
    
    // Set parameters for geospatial queries
    if (exampleQuery.query.includes('within') || exampleQuery.query.includes('km')) {
      setParameters({
        latitude: 7.9465,
        longitude: -1.0232,
        radius_km: 10
      });
    }
  };

  return (
    <div className="query-panel-content">
      <div className="panel-header">
        <Sparkles className="panel-icon" />
        <h2>Mission Planner</h2>
      </div>
      
      <p className="panel-description">
        Ask in plain language. The agent turns messy facility rows into evidence-backed routing, verification, and investment actions.
      </p>

      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-group">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Example: where should we send surgical volunteers first?"
            className="query-input"
            rows={3}
          />
        </div>
        
        <motion.button
          type="submit"
          className="submit-button"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          disabled={!query.trim()}
        >
          <Send size={18} />
          <span>Analyze</span>
        </motion.button>
      </form>

      {showExamples && (
        <div className="examples-section">
          <h3>Fast Starts</h3>
          <div className="examples-list">
            {exampleQueries.map((example, index) => {
              const ExampleIcon = example.icon;
              return (
                <motion.button
                  key={index}
                  className="example-button"
                  onClick={() => handleExampleClick(example)}
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <ExampleIcon size={16} />
                  <span>
                    <strong>{example.label}</strong>
                    <small>{example.query}</small>
                  </span>
                </motion.button>
              );
            })}
          </div>
        </div>
      )}

      <div className="query-tips">
        <h4>Good demo questions</h4>
        <button type="button" onClick={() => setQuery('Which hospitals have emergency, imaging, and surgery evidence?')}>
          Which hospitals are ready for urgent referral?
        </button>
        <button type="button" onClick={() => setQuery('Which facilities need manual verification before patient routing?')}>
          What data should we verify first?
        </button>
      </div>
    </div>
  );
}

export default QueryPanel;
