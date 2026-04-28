import React from 'react';
import { motion } from 'framer-motion';
import { Layers, MapPin, Activity, AlertCircle, Users } from 'lucide-react';
import './components.css';

function LayerControl({ activeLayers, onToggleLayer, onClose }) {
  const layers = [
    {
      id: 'facilities',
      name: 'Facilities',
      icon: MapPin,
      color: '#6366f1',
      description: 'All healthcare facilities'
    },
    {
      id: 'physicianDensity',
      name: 'Physician Density',
      icon: Users,
      color: '#10b981',
      description: 'Doctors per facility'
    },
    {
      id: 'hospitalDensity',
      name: 'Hospital Density',
      icon: Activity,
      color: '#ef4444',
      description: 'Hospital concentration'
    },
    {
      id: 'medicalDesert',
      name: 'Medical Desert',
      icon: AlertCircle,
      color: '#f59e0b',
      description: 'Underserved regions'
    }
  ];

  return (
    <div className="layer-control-content">
      <div className="layer-header">
        <Layers className="layer-icon" />
        <h2>Map Layers</h2>
      </div>

      <div className="layers-list">
        {layers.map((layer) => {
          const Icon = layer.icon;
          const isActive = activeLayers[layer.id];
          
          return (
            <motion.button
              key={layer.id}
              className={`layer-item ${isActive ? 'active' : ''}`}
              onClick={() => onToggleLayer(layer.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: layers.indexOf(layer) * 0.1 }}
            >
              <div 
                className="layer-indicator"
                style={{ backgroundColor: isActive ? layer.color : 'rgba(255,255,255,0.1)' }}
              >
                <Icon size={18} color={isActive ? '#fff' : layer.color} />
              </div>
              
              <div className="layer-info">
                <span className="layer-name">{layer.name}</span>
                <span className="layer-description">{layer.description}</span>
              </div>
              
              <div className={`layer-toggle ${isActive ? 'on' : 'off'}`}>
                <div className="toggle-knob" />
              </div>
            </motion.button>
          );
        })}
      </div>

      <div className="layer-footer">
        <button className="close-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

export default LayerControl;
