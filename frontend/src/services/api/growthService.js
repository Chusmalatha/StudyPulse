import apiClient from './apiClient';

export const getProjectGrowth = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/growth`);
  return response.data;
};

export const getProjectRecommendations = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/recommendations`);
  return response.data;
};

export const generateProjectRecommendations = async (projectId) => {
  const response = await apiClient.post(`/projects/${projectId}/recommendations/generate`);
  return response.data;
};

export const completeRecommendation = async (projectId, recommendationId) => {
  const response = await apiClient.post(`/projects/${projectId}/recommendations/${recommendationId}/complete`);
  return response.data;
};

export const dismissRecommendation = async (projectId, recommendationId) => {
  const response = await apiClient.post(`/projects/${projectId}/recommendations/${recommendationId}/dismiss`);
  return response.data;
};
