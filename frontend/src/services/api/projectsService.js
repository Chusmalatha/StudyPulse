import apiClient from './apiClient';

const projectsService = {
  getProject: async (projectId) => {
    const res = await apiClient.get(`/projects/${projectId}`);
    return res.data;
  },

  updateProject: async (projectId, projectData) => {
    const res = await apiClient.patch(`/projects/${projectId}`, projectData);
    return res.data;
  },

  deleteProject: async (projectId) => {
    const res = await apiClient.delete(`/projects/${projectId}`);
    return res.data;
  },
};

export default projectsService;
