import apiClient from './apiClient';

const materialsService = {
  /**
   * Upload a PDF file for a project
   * @param {string} projectId
   * @param {File} file
   * @returns {Promise<Object>} Material record
   */
  uploadMaterial: async (projectId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/projects/${projectId}/materials`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * List all materials for a project
   * @param {string} projectId
   * @returns {Promise<Array>} List of materials
   */
  getProjectMaterials: async (projectId) => {
    const response = await apiClient.get(`/projects/${projectId}/materials`);
    return response.data;
  },

  /**
   * Get single material details and processing status
   * @param {string} materialId
   * @returns {Promise<Object>} Material details
   */
  getMaterial: async (materialId) => {
    const response = await apiClient.get(`/materials/${materialId}`);
    return response.data;
  },

  /**
   * Retry background processing for a failed material
   * @param {string} materialId
   * @returns {Promise<Object>} Retry status response
   */
  retryMaterial: async (materialId) => {
    const response = await apiClient.post(`/materials/${materialId}/retry`);
    return response.data;
  },

  /**
   * Get processed text chunks for a material
   * @param {string} materialId
   * @returns {Promise<Array>} List of chunk objects with page_number metadata
   */
  getMaterialChunks: async (materialId) => {
    const response = await apiClient.get(`/materials/${materialId}/chunks`);
    return response.data;
  },

  /**
   * Delete a material, its stored file, and all associated chunks
   * @param {string} materialId
   * @returns {Promise<void>}
   */
  deleteMaterial: async (materialId) => {
    await apiClient.delete(`/materials/${materialId}`);
  },
};

export default materialsService;
