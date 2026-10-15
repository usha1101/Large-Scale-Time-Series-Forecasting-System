/**
 * API Service Layer
 * Handles all communication with the FastAPI backend
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const login = (username, password) =>
  api.post('/auth/login', { username, password });

// Predictions
export const predict = (sku, store_id, start_date, end_date) =>
  api.post('/predict', { sku, store_id, start_date, end_date });

export const batchPredict = (predictions) =>
  api.post('/batch_predict', { predictions });

// Metrics
export const getMetrics = () => api.get('/metrics');
export const getSkus = () => api.get('/metrics/skus');

// Health
export const getHealth = () => api.get('/health');

// Data
export const uploadData = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/upload_data', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const getDatasets = () => api.get('/datasets');
export const getDataSample = (filename, n = 100) =>
  api.get(`/data/sample?filename=${filename}&n=${n}`);

export default api;
