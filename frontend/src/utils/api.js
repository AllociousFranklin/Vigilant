import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const vigilantApi = {
  scan: async (payload) => {
    const response = await apiClient.post('/scan', payload);
    return response.data;
  },
  
  getHistory: async (page = 1, pageSize = 20, severity = null, channel = null) => {
    const params = { page, page_size: pageSize };
    if (severity) params.severity = severity;
    if (channel) params.channel = channel;
    
    const response = await apiClient.get('/history', { params });
    return response.data;
  },
  
  getStats: async () => {
    const response = await apiClient.get('/stats');
    return response.data;
  },
  
  submitFeedback: async (scanId, verdict, notes = null) => {
    const response = await apiClient.post('/feedback', {
      scan_id: scanId,
      verdict,
      notes,
    });
    return response.data;
  },
  
  checkHealth: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  }
};
