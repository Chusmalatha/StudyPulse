import apiClient from './apiClient';

const spacesService = {
  getSpaces: async () => {
    const res = await apiClient.get('/spaces');
    return res.data;
  },

  getSpace: async (spaceId) => {
    const res = await apiClient.get(`/spaces/${spaceId}`);
    return res.data;
  },

  createSpace: async (spaceData) => {
    const res = await apiClient.post('/spaces', spaceData);
    return res.data;
  },

  updateSpace: async (spaceId, spaceData) => {
    const res = await apiClient.patch(`/spaces/${spaceId}`, spaceData);
    return res.data;
  },

  deleteSpace: async (spaceId) => {
    const res = await apiClient.delete(`/spaces/${spaceId}`);
    return res.data;
  },

  getSpaceProjects: async (spaceId) => {
    const res = await apiClient.get(`/spaces/${spaceId}/projects`);
    return res.data;
  },

  createSpaceProject: async (spaceId, projectData) => {
    const res = await apiClient.post(`/spaces/${spaceId}/projects`, projectData);
    return res.data;
  },

  getSpaceProjectDetails: async (spaceId, projectId) => {
    const res = await apiClient.get(`/spaces/${spaceId}/projects/${projectId}`);
    return res.data;
  },
};

export default spacesService;
