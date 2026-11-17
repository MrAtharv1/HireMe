import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create an Axios instance locked to your FastAPI backend
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: automatically attaches JWT Bearer token if logged in
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('hireme_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: automatically handles expired session tokens
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If token is invalid or expired, clear it
      if (localStorage.getItem('hireme_token')) {
        console.warn('Session expired. Clearing stored token.');
        localStorage.removeItem('hireme_token');
        localStorage.removeItem('hireme_user');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
