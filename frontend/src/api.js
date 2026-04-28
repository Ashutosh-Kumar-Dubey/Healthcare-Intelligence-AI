export const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8001';

export const apiUrl = (path) => `${API_BASE}${path}`;
