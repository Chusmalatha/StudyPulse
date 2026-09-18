import apiClient from './apiClient';

export const getProjectAnalytics = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/analytics`);
  return response.data;
};

export const getGlobalAnalytics = async () => {
  const response = await apiClient.get('/analytics/overview');
  return response.data;
};
