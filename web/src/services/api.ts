import axios from 'axios';

/**
 * Single shared Axios instance for all API calls.
 * Base URL is read from the VITE_API_BASE_URL environment variable.
 * In development the Vite proxy forwards /api/* to the FastAPI server.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  headers: {
    'Content-Type': 'application/json',
  },
});
