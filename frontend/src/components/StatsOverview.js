import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, FileSearch, MapPin, ShieldCheck, Stethoscope } from 'lucide-react';
import { apiUrl } from '../api';
import './components.css';

function StatsOverview() {
  const [stats, setStats] = useState({
    total_facilities: 0,
    total_hospitals: 0,
    total_clinics: 0,
    total_anomalies: 0,
    average_reliability_score: 0,
    total_regions: 0,
    facilities_with_idp_facts: 0,
    mapped_facilities: 0,
    high_risk_regions: 0,
    claim_verification_rate: 0,
    map_coverage_rate: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(apiUrl('/api/stats/overview'));
      const data = await response.json();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  const formatPercent = (value) => `${(value * 100).toFixed(0)}%`;

  const statCards = [
    {
      icon: Stethoscope,
      label: 'Care Network',
      value: stats.total_facilities,
      detail: `${stats.total_hospitals.toLocaleString()} hospitals, ${stats.total_clinics.toLocaleString()} clinics`,
      color: '#38bdf8'
    },
    {
      icon: MapPin,
      label: 'Map Coverage',
      value: formatPercent(stats.map_coverage_rate),
      detail: `${stats.mapped_facilities.toLocaleString()} facilities placed across ${stats.total_regions.toLocaleString()} regions`,
      color: '#22c55e'
    },
    {
      icon: FileSearch,
      label: 'IDP Evidence',
      value: formatPercent(stats.facilities_with_idp_facts / Math.max(stats.total_facilities, 1)),
      detail: `${stats.facilities_with_idp_facts.toLocaleString()} rows with parsed capability facts`,
      color: '#a78bfa',
    },
    {
      icon: AlertTriangle,
      label: 'Risk Watchlist',
      value: stats.high_risk_regions,
      detail: `${stats.total_anomalies.toLocaleString()} suspicious or incomplete claims`,
      color: '#f97316'
    },
    {
      icon: ShieldCheck,
      label: 'Evidence Trust',
      value: formatPercent(stats.average_reliability_score),
      detail: `${formatPercent(stats.claim_verification_rate)} of rows need follow-up`,
      color: '#14b8a6'
    }
  ];

  if (loading) {
    return (
      <div className="stats-overview">
        <div className="stats-loading">Building operational snapshot...</div>
      </div>
    );
  }

  return (
    <div className="stats-overview">
      <div className="stats-heading">
        <span className="stats-eyebrow">Operational Snapshot</span>
        <strong>What planners need to know first</strong>
      </div>
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        
        return (
          <motion.div
            key={index}
            className="stat-card"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="stat-icon" style={{ backgroundColor: `${stat.color}20` }}>
              <Icon size={20} color={stat.color} />
            </div>
            
            <div className="stat-content">
              <span className="stat-label">{stat.label}</span>
              <span className="stat-value">
                {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
              </span>
              <span className="stat-detail">{stat.detail}</span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

export default StatsOverview;
