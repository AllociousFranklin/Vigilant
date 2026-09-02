import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sentinelApi = {
  assessTransaction: async (payload) => {
    const response = await apiClient.post('/assess', payload);
    return response.data;
  },

  getTransactions: async (page = 1, pageSize = 20, riskLevel = null, merchantId = null) => {
    const params = { page, page_size: pageSize };
    if (riskLevel) params.risk_level = riskLevel;
    if (merchantId) params.merchant_id = merchantId;
    const response = await apiClient.get('/transactions', { params });
    return response.data;
  },

  getStats: async () => {
    const response = await apiClient.get('/stats');
    return response.data;
  },

  submitFeedback: async (transactionId, outcome, notes = null) => {
    const response = await apiClient.post('/feedback', {
      transaction_id: transactionId,
      outcome,
      notes,
    });
    return response.data;
  },

  getDisputeDossier: async (assessmentId) => {
    const response = await apiClient.get(`/dispute/${assessmentId}`);
    return response.data;
  },

  getMetrics: async () => {
    const response = await apiClient.get('/metrics');
    return response.data;
  },
};
