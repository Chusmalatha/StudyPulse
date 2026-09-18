import apiClient from './apiClient';

export const getAdminOverview = async () => {
  const response = await apiClient.get('/admin/overview');
  return response.data;
};

export const getAdminUsers = async (params = {}) => {
  const response = await apiClient.get('/admin/users', { params });
  return response.data;
};

export const getAdminUserJourney = async (userId) => {
  const response = await apiClient.get(`/admin/users/${userId}`);
  return response.data;
};

export const getAdminActivity = async (params = {}) => {
  const response = await apiClient.get('/admin/activity', { params });
  return response.data;
};

export const getAdminEngagement = async () => {
  const response = await apiClient.get('/admin/engagement');
  return response.data;
};

export const getAdminAIUsage = async () => {
  const response = await apiClient.get('/admin/ai-usage');
  return response.data;
};

export const getAdminAIEvaluation = async () => {
  const response = await apiClient.get('/admin/ai-evaluation');
  return response.data;
};

export const getAdminJobs = async (params = {}) => {
  const response = await apiClient.get('/admin/jobs', { params });
  return response.data;
};

export const getAdminSystemHealth = async () => {
  const response = await apiClient.get('/admin/system-health');
  return response.data;
};
