import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add Authorization header to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Stats API
export const getOverview = () => api.get('/stats/overview');
export const getBandwidth = (days = 7) => api.get(`/stats/bandwidth?days=${days}`);
export const getTopFiles = (limit = 20) => api.get(`/stats/top-files?limit=${limit}`);
export const getCachePerformance = () => api.get('/stats/cache-performance');

// Auth API
export const changePassword = (oldPassword, newPassword) => 
  api.patch('/auth/change-password', { old_password: oldPassword, new_password: newPassword });
export const changeUsername = (newUsername, password) => 
  api.patch('/auth/change-username', { new_username: newUsername, password });

// Upload API
export const uploadFile = (formData) => {
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const listFiles = (params = {}) => {
  const queryString = new URLSearchParams(params).toString();
  return api.get(`/files?${queryString}`);
};

export const deleteFile = (fileId) => api.delete(`/files/${fileId}`);

// Cache API
export const getCacheStatus = (path) => api.get(`/cache/status?path=${encodeURIComponent(path)}`);
export const listCachedFiles = (limit = 100, offset = 0) => 
  api.get(`/cache/list?limit=${limit}&offset=${offset}`);

// Purge API
export const purgeSingleFile = (path) => 
  api.delete(`/purge?path=${encodeURIComponent(path)}`);
export const purgeBucket = (bucket) => api.delete(`/purge/bucket/${bucket}`);
export const purgeAllCache = () => api.delete('/purge/all?confirm=true');
export const getPurgeHistory = (limit = 50) => api.get(`/purge/history?limit=${limit}`);

// Admin API
export const listBuckets = () => api.get('/admin/buckets');
export const createBucket = (name) => api.post(`/admin/buckets?name=${name}`);
export const getSystemInfo = () => api.get('/admin/system-info');

// API Keys Management
export const getApiKeys = () => api.get('/auth/api-keys');
export const createApiKey = (data) => api.post('/auth/api-keys', data);
export const deleteApiKey = (keyId) => api.delete(`/auth/api-keys/${keyId}`);
export const toggleApiKey = (keyId) => api.patch(`/auth/api-keys/${keyId}/toggle`);
export const testApiKey = (apiKey) => {
  // Test with Authorization: Bearer header (API Keys start with 'cdn_')
  // Backend recognizes cdn_ prefix as API key, not JWT token
  return axios.get(`${API_BASE_URL}/stats/overview`, {
    headers: {
      'Authorization': `Bearer ${apiKey}`
    }
  });
};

export default api;
