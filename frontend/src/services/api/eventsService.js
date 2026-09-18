import apiClient from './apiClient';

export const getProjectEvents = async (projectId, params = {}) => {
  const response = await apiClient.get(`/projects/${projectId}/events`, { params });
  return response.data;
};

export const getEventDetail = async (projectId, eventId) => {
  const response = await apiClient.get(`/projects/${projectId}/events/${eventId}`);
  return response.data;
};
