import axios from 'axios';

// Base API URL - pointing explicitly to the backend port
const API_URL = 'http://localhost:5000/api';

// Create axios instance with CORS configurations
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // Important for cross-origin requests
  withCredentials: false
});

// Add request interceptor for debugging
apiClient.interceptors.request.use(
  config => {
    console.log(`Making ${config.method.toUpperCase()} request to: ${config.baseURL}${config.url}`);
    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
apiClient.interceptors.response.use(
  response => {
    console.log('Response received:', response.status);
    return response;
  },
  error => {
    console.error('Response error:', {
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data,
        headers: error.response.headers
      } : 'No response',
      request: error.request ? 'Request was made but no response received' : 'No request'
    });
    return Promise.reject(error);
  }
);

const apiService = {
  // Chat related endpoints
  chat: {
    sendMessage: async (message, sessionId = null) => {
      try {
        // Add retry logic
        let retries = 3;
        let lastError = null;
        
        while (retries > 0) {
          try {
            const response = await apiClient.post('/chat', { 
              message, 
              session_id: sessionId 
            });
            return response;
          } catch (err) {
            lastError = err;
            retries--;
            // Wait before retrying (exponential backoff)
            await new Promise(r => setTimeout(r, 1000 * (3 - retries)));
          }
        }
        
        // If we've exhausted all retries
        throw lastError;
      } catch (error) {
        console.error('Failed to send message after retries:', error);
        throw error;
      }
    }
  },
  
  // Test connection to backend
  health: {
    check: async () => {
      return apiClient.get('/health');
    }
  },
  
  // Menu related endpoints
  menu: {
    getMenu: () => {
      return apiClient.get('/menu');
    }
  },
  
  // Table availability related endpoints
  availability: {
    getDates: () => {
      return apiClient.get('/availability');
    },
    getTimesByDate: (date) => {
      return apiClient.get(`/availability?date=${date}`);
    }
  },
  
  // Order related endpoints (for admin purposes)
  orders: {
    getAll: () => {
      return apiClient.get('/orders');
    }
  },
  
  // Booking related endpoints (for admin purposes)
  bookings: {
    getAll: () => {
      return apiClient.get('/bookings');
    }
  }
};

export default apiService;