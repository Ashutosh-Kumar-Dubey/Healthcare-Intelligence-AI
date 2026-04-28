import React from 'react';
import { motion } from 'framer-motion';
import { Brain, MapPin, AlertTriangle, CheckCircle, ListChecks, Route } from 'lucide-react';
import './components.css';

const renderList = (items, className = 'insight-list') => {
  if (!items || items.length === 0) return null;
  return (
    <ul className={className}>
      {items.map((item, index) => (
        <li key={index}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
      ))}
    </ul>
  );
};

const citationLabel = (citation) => {
  if (typeof citation === 'string') return citation;
  const row = citation.row_id ? `Row ${citation.row_id}` : `Facility ${citation.facility_id}`;
  const field = citation.field ? ` - ${citation.field}` : '';
  return `${row}${field}`;
};

const renderTags = (title, values, limit = 8) => {
  if (!values || values.length === 0) return null;
  return (
    <div className="specialties-list">
      <h5>{title}</h5>
      <div className="tags">
        {values.slice(0, limit).map((value, index) => (
          <span key={index} className="tag">{value}</span>
        ))}
        {values.length > limit && (
          <span className="tag">+{values.length - limit} more</span>
        )}
      </div>
    </div>
  );
};

const getMatchedFacilities = (queryResult) => {
  const data = queryResult?.data || {};
  if (Array.isArray(data.facilities)) return data.facilities;
  if (Array.isArray(data.anomalies)) {
    return data.anomalies.map((item) => ({
      id: item.facility_id,
      name: item.facility_name,
      city: item.city,
      reliability_score: item.reliability_score,
      type: 'facility'
    }));
  }
  return [];
};

function InsightsPanel({ queryResult, selectedFacility, onFacilityFocus }) {
  if (!queryResult && !selectedFacility) {
    return (
      <div className="insights-panel-content">
        <div className="panel-header">
          <Brain className="panel-icon" />
          <h2>Insights</h2>
        </div>
        <p className="panel-description">
          Run a query or select a facility to see AI-generated insights
        </p>
        <div className="empty-state">
          <Brain size={48} className="empty-icon" />
          <p>No insights to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className="insights-panel-content">
      <div className="panel-header">
        <Brain className="panel-icon" />
        <h2>AI Insights</h2>
      </div>

      {queryResult && (
        <motion.div
          className="insight-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>Query Result</h3>
          <div className="query-answer">
            <p>{queryResult.answer}</p>
          </div>

          {renderList(queryResult.summary)}

          {queryResult.findings && queryResult.findings.length > 0 && (
            <div className="agent-output-block">
              <div className="mini-header">
                <CheckCircle size={16} />
                <h4>Findings</h4>
              </div>
              {renderList(queryResult.findings)}
            </div>
          )}

          {queryResult.recommended_actions && queryResult.recommended_actions.length > 0 && (
            <div className="agent-output-block action-block">
              <div className="mini-header">
                <Route size={16} />
                <h4>Planner Actions</h4>
              </div>
              {renderList(queryResult.recommended_actions, 'action-list')}
            </div>
          )}

          {getMatchedFacilities(queryResult).length > 0 && (
            <div className="agent-output-block match-block">
              <div className="mini-header">
                <MapPin size={16} />
                <h4>Map Matches</h4>
              </div>
              <div className="match-list">
                {getMatchedFacilities(queryResult).slice(0, 12).map((facility, index) => (
                  <button
                    key={`${facility.id || facility.name}-${index}`}
                    className="match-item"
                    type="button"
                    onClick={() => onFacilityFocus?.({
                      facility_id: facility.id,
                      facility_name: facility.name
                    })}
                  >
                    <span>
                      <strong>{facility.name}</strong>
                      <small>{facility.city || facility.region || 'Location needs verification'}</small>
                    </span>
                    <MapPin size={15} />
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <div className="confidence-meter">
            <span>Confidence:</span>
            <div className="confidence-bar">
              <motion.div
                className="confidence-fill"
                initial={{ width: 0 }}
                animate={{ width: `${queryResult.confidence * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="confidence-value">{(queryResult.confidence * 100).toFixed(0)}%</span>
          </div>

          {queryResult.citations && queryResult.citations.length > 0 && (
            <div className="citations">
              <h4>Row-Level Citations:</h4>
              <div className="citation-tags">
                {queryResult.citations.map((citation, index) => (
                  <button
                    key={index}
                    className="citation-card citation-card-button"
                    type="button"
                    onClick={() => onFacilityFocus?.(citation)}
                  >
                    <span className="citation-tag">{citationLabel(citation)}</span>
                    {citation.facility_name && <span className="citation-facility">{citation.facility_name}</span>}
                    {citation.evidence && <p>{citation.evidence}</p>}
                    <span className="citation-action">Focus on map</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {queryResult.agent_trace && queryResult.agent_trace.length > 0 && (
            <div className="agent-output-block">
              <div className="mini-header">
                <ListChecks size={16} />
                <h4>Agent Trace</h4>
              </div>
              <div className="trace-list">
                {queryResult.agent_trace.map((step, index) => (
                  <div key={index} className="trace-item">
                    <span>{step.step}</span>
                    <p>{typeof step.output === 'string' ? step.output : JSON.stringify(step.output)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {queryResult.data && Object.keys(queryResult.data).length > 0 && (
            <div className="data-preview">
              <h4>Structured Data</h4>
              <pre className="data-json">
                {JSON.stringify(queryResult.data, null, 2)}
              </pre>
            </div>
          )}
        </motion.div>
      )}

      {selectedFacility && (
        <motion.div
          className="insight-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>Facility Details</h3>
          <div className="facility-card">
            <div className="facility-header">
              <MapPin size={20} />
              <h4>{selectedFacility.name}</h4>
            </div>
            
            <div className="facility-info">
              <div className="info-row">
                <span className="info-label">Type:</span>
                <span className="info-value">{selectedFacility.type}</span>
              </div>
              <div className="info-row">
                <span className="info-label">City:</span>
                <span className="info-value">{selectedFacility.city}</span>
              </div>
              {selectedFacility.doctors && (
                <div className="info-row">
                  <span className="info-label">Doctors:</span>
                  <span className="info-value">{selectedFacility.doctors}</span>
                </div>
              )}
              {selectedFacility.capacity && (
                <div className="info-row">
                  <span className="info-label">Capacity:</span>
                  <span className="info-value">{selectedFacility.capacity}</span>
                </div>
              )}
              <div className="info-row">
                <span className="info-label">Data confidence:</span>
                <span className="info-value">
                  {(selectedFacility.reliability_score * 100).toFixed(1)}%
                </span>
              </div>
              {selectedFacility.best_row_reliability && (
                <div className="info-row">
                  <span className="info-label">Best evidence row:</span>
                  <span className="info-value">
                    {(selectedFacility.best_row_reliability * 100).toFixed(1)}%
                  </span>
                </div>
              )}
              {selectedFacility.evidence_rows && (
                <div className="info-row">
                  <span className="info-label">Merged rows:</span>
                  <span className="info-value">{selectedFacility.evidence_rows}</span>
                </div>
              )}
            </div>

            {renderTags('Specialties', selectedFacility.specialties, 10)}
            {renderTags('Procedures', selectedFacility.procedures, 6)}
            {renderTags('Equipment', selectedFacility.equipment, 6)}
            {renderTags('Capabilities', selectedFacility.capabilities, 6)}
          </div>
        </motion.div>
      )}

      {queryResult && queryResult.query_type === 'gap_analysis' && (
        <motion.div
          className="insight-section alert-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="alert-header">
            <AlertTriangle size={20} className="alert-icon" />
            <h3>Gap Analysis</h3>
          </div>
          <p className="alert-description">
            These regions have limited healthcare infrastructure and may be considered medical deserts.
          </p>
        </motion.div>
      )}

      {queryResult && queryResult.query_type === 'anomaly_detection' && (
        <motion.div
          className="insight-section warning-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="warning-header">
            <AlertTriangle size={20} className="warning-icon" />
            <h3>Anomaly Detection</h3>
          </div>
          <p className="warning-description">
            These facilities may have data inconsistencies or unrealistic claims.
          </p>
        </motion.div>
      )}
    </div>
  );
}

export default InsightsPanel;
