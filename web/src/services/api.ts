import axios, { AxiosError } from 'axios';

import type { ApiError } from '@/types';

/**
 * Single shared Axios instance for all API calls.
 * Base URL is read from the VITE_API_BASE_URL environment variable.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Response interceptor — normalises FastAPI error responses.
 * FastAPI returns `{ detail: string }` on 4xx/5xx; this re-throws
 * an Error whose message is that detail string so callers receive a
 * plain, readable message instead of a raw AxiosError.
 */
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const detail = error.response?.data?.detail;
    const message = detail ?? error.message ?? 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  },
);
