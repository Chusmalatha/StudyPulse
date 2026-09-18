import apiClient from './apiClient';

export const getProjectMastery = async (projectId) => {
  const response = await apiClient.get(`/projects/${projectId}/mastery`);
  return response.data;
};

export const getConceptMasteryDetail = async (projectId, conceptId) => {
  const response = await apiClient.get(`/projects/${projectId}/mastery/${conceptId}`);
  return response.data;
};

