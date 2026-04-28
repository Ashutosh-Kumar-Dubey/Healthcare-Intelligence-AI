import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { apiUrl } from '../api';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (type, isFocused = false) => {
  const colors = {
    hospital: '#38bdf8',
    clinic: '#14b8a6',
    pharmacy: '#f59e0b',
    dentist: '#a78bfa',
    doctor: '#22c55e',
    default: '#94a3b8'
  };
  const color = colors[type] || colors.default;
  const size = isFocused ? 30 : 22;
  const innerSize = isFocused ? 14 : 10;
  
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 2px solid ${isFocused ? '#ffffff' : 'rgba(255,255,255,0.86)'};
      box-shadow: 0 0 0 ${isFocused ? '6px' : '3px'} ${color}2e, 0 0 18px ${color}90;
      background: rgba(8, 13, 18, 0.92);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        width: ${innerSize}px;
        height: ${innerSize}px;
        border-radius: 50%;
        background: ${color};
      "></div>
    </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
};

function FocusFacility({ facilities, focusTarget, onFacilitySelect, onFocused }) {
  const map = useMap();
  const lastRequestRef = useRef(null);

  useEffect(() => {
    if (!focusTarget || facilities.length === 0) return;
    if (lastRequestRef.current === focusTarget.requestedAt) return;

    const targetName = (focusTarget.facility_name || focusTarget.name || '').toLowerCase();
    const match = facilities.find((facility) => facility.id === focusTarget.facility_id)
      || facilities.find((facility) => (facility.name || '').toLowerCase() === targetName)
      || facilities.find((facility) => targetName && (facility.name || '').toLowerCase().includes(targetName));

    if (!match) return;

    lastRequestRef.current = focusTarget.requestedAt;
    map.flyTo([match.lat, match.lon], Math.max(map.getZoom(), 12), {
      duration: 0.9
    });
    onFocused(match);
    onFacilitySelect(match);
  }, [facilities, focusTarget, map, onFacilitySelect, onFocused]);

  return null;
}

function HeatmapLayer({ data, type }) {
  const map = useMap();
  
  useEffect(() => {
    const heatData = (data || [])
      .map(point => {
        const lat = Number(point.lat);
        const lon = Number(point.lon);
        const intensity = Number(point.intensity);
        return [lat, lon, Number.isFinite(intensity) ? Math.max(0.05, Math.min(intensity, 1)) : 0.05];
      })
      .filter(([lat, lon]) => Number.isFinite(lat) && Number.isFinite(lon));
    
    // Remove existing heat layer
    map.eachLayer((layer) => {
      if (layer._healthcareHeatLayer) {
        map.removeLayer(layer);
      }
    });

    if (heatData.length === 0) return;
    
    const heatLayer = L.heatLayer(heatData, {
      radius: 25,
      blur: 15,
      maxZoom: 10,
      gradient: {
        0.0: '#10b981',
        0.3: '#f59e0b',
        0.5: '#ef4444',
        0.7: '#8b5cf6',
        1.0: '#6366f1'
      }
    }).addTo(map);
    
    heatLayer._healthcareHeatLayer = true;
    
    return () => {
      if (map.hasLayer(heatLayer)) {
        map.removeLayer(heatLayer);
      }
    };
  }, [map, data, type]);
  
  return null;
}

function MapView({ activeLayers, onFacilitySelect, focusTarget }) {
  const [facilities, setFacilities] = useState([]);
  const [heatmapData, setHeatmapData] = useState(null);
  const [focusedFacilityId, setFocusedFacilityId] = useState(null);
  const [center] = useState([7.9465, -1.0232]); // Ghana center
  const [zoom] = useState(6);

  useEffect(() => {
    fetchFacilities();
  }, []);

  const fetchFacilities = async () => {
    try {
      const response = await fetch(apiUrl('/api/map/facilities'));
      const data = await response.json();
      setFacilities((data || []).filter((facility) => (
        Number.isFinite(Number(facility.lat)) && Number.isFinite(Number(facility.lon))
      )));
    } catch (error) {
      console.error('Error fetching facilities:', error);
    }
  };

  const getActiveHeatmapType = useCallback(() => {
    let type = 'physician_density';
    if (activeLayers.hospitalDensity) type = 'hospital_density';
    if (activeLayers.medicalDesert) type = 'medical_desert';
    return type;
  }, [activeLayers.hospitalDensity, activeLayers.medicalDesert]);
  
  const fetchHeatmapData = useCallback(async () => {
    const type = getActiveHeatmapType();
    
    try {
      const response = await fetch(apiUrl(`/api/map/heatmap?heatmap_type=${type}`));
      const data = await response.json();
      setHeatmapData(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching heatmap data:', error);
      setHeatmapData([]);
    }
  }, [getActiveHeatmapType]);

  useEffect(() => {
    if (activeLayers.physicianDensity || activeLayers.hospitalDensity || activeLayers.medicalDesert) {
      fetchHeatmapData();
    } else {
      setHeatmapData(null);
    }
  }, [
    activeLayers.physicianDensity,
    activeLayers.hospitalDensity,
    activeLayers.medicalDesert,
    fetchHeatmapData
  ]);

  const handleMarkerClick = (facility) => {
    onFacilitySelect(facility);
  };

  const handleFocusedFacility = useCallback((facility) => {
    setFocusedFacilityId(facility.id);
  }, []);

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      <FocusFacility
        facilities={facilities}
        focusTarget={focusTarget}
        onFacilitySelect={onFacilitySelect}
        onFocused={handleFocusedFacility}
      />
      
      {/* Facilities Layer */}
      {activeLayers.facilities && facilities.map((facility) => (
        <Marker
          key={facility.id}
          position={[facility.lat, facility.lon]}
          icon={createCustomIcon(facility.type, focusedFacilityId === facility.id)}
          eventHandlers={{
            click: () => {
              setFocusedFacilityId(facility.id);
              handleMarkerClick(facility);
            }
          }}
        >
          <Popup>
            <div style={{ color: '#000' }}>
              <h3 style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>{facility.name}</h3>
              <p style={{ margin: '4px 0' }}><strong>Type:</strong> {facility.type}</p>
              <p style={{ margin: '4px 0' }}><strong>City:</strong> {facility.city}</p>
              {facility.doctors && <p style={{ margin: '4px 0' }}><strong>Doctors:</strong> {facility.doctors}</p>}
              {facility.capacity && <p style={{ margin: '4px 0' }}><strong>Capacity:</strong> {facility.capacity}</p>}
              <p style={{ margin: '4px 0' }}><strong>Reliability Score:</strong> {(facility.reliability_score * 100).toFixed(1)}%</p>
            </div>
          </Popup>
        </Marker>
      ))}
      
      {/* Heatmap Layer */}
      {(activeLayers.physicianDensity || activeLayers.hospitalDensity || activeLayers.medicalDesert) && heatmapData && (
        <HeatmapLayer 
          data={heatmapData} 
          type={activeLayers.physicianDensity ? 'physician' : activeLayers.hospitalDensity ? 'hospital' : 'desert'}
        />
      )}
    </MapContainer>
  );
}

export default MapView;
