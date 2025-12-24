import axios from 'axios';

// Access environment variable or default to localhost
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

console.log('[API] Initializing with base URL:', API_URL);

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Add interceptor for request logging
api.interceptors.request.use(
    (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
        return config;
    },
    (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
    }
);

// Add interceptor for error handling
api.interceptors.response.use(
    (response) => {
        console.log(`[API] Response ${response.status} from ${response.config.url}`);
        return response;
    },
    (error) => {
        // Standardize error handling if needed
        console.error('[API] Error:', error.response?.status, error.response?.data || error.message);
        if (error.code === 'ERR_NETWORK') {
            console.error('[API] Network error - is the backend running on port 8000?');
        }
        return Promise.reject(error);
    }
);

export default api;
