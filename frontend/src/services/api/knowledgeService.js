import apiClient from './apiClient';

const knowledgeService = {
  /**
   * Perform semantic vector RAG search for a project
   * @param {string} projectId
   * @param {string} query
   * @param {number} topK
   * @returns {Promise<Object>} Search results with filename and page citations
   */
  searchProjectKnowledge: async (projectId, query, topK = 5) => {
    const response = await apiClient.post(`/projects/${projectId}/search`, {
      query,
      top_k: topK,
    });
    return response.data;
  },

  /**
   * Get extracted concepts, topics, and sections for a project
   * @param {string} projectId
   * @returns {Promise<Object>} Project knowledge structure
   */
  getProjectKnowledge: async (projectId) => {
    const response = await apiClient.get(`/projects/${projectId}/knowledge`);
    return response.data;
  },

  /**
   * Manually trigger knowledge extraction for a project
   * @param {string} projectId
   * @returns {Promise<Object>} Refreshed project knowledge structure
   */
  extractProjectKnowledge: async (projectId) => {
    const response = await apiClient.post(`/projects/${projectId}/knowledge/extract`);
    return response.data;
  },
};

export default knowledgeService;
