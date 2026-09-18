import apiClient from './apiClient';

const tutorService = {
  /**
   * Create a new Tutor conversation in a project
   * @param {string} projectId
   * @param {string} [title]
   * @returns {Promise<Object>} Conversation object
   */
  createConversation: async (projectId, title = null) => {
    const response = await apiClient.post(`/projects/${projectId}/tutor/conversations`, {
      title: title || undefined,
    });
    return response.data;
  },

  /**
   * List all Tutor conversations for a project
   * @param {string} projectId
   * @returns {Promise<Array>} List of conversation objects
   */
  getConversations: async (projectId) => {
    const response = await apiClient.get(`/projects/${projectId}/tutor/conversations`);
    return response.data;
  },

  /**
   * Get single conversation details
   * @param {string} projectId
   * @param {string} conversationId
   * @returns {Promise<Object>} Conversation object
   */
  getConversation: async (projectId, conversationId) => {
    const response = await apiClient.get(`/projects/${projectId}/tutor/conversations/${conversationId}`);
    return response.data;
  },

  /**
   * Get message history for a conversation
   * @param {string} projectId
   * @param {string} conversationId
   * @returns {Promise<Array>} List of message objects
   */
  getMessages: async (projectId, conversationId) => {
    if (!conversationId || conversationId === 'undefined') {
      return [];
    }
    const response = await apiClient.get(`/projects/${projectId}/tutor/conversations/${conversationId}/messages`);
    return response.data;
  },

  /**
   * Send a question to the AI Tutor in a conversation
   * @param {string} projectId
   * @param {string} conversationId
   * @param {string} message
   * @returns {Promise<Object>} Tutor answer with citations and grounded flag
   */
  sendMessage: async (projectId, conversationId, message) => {
    if (!conversationId || conversationId === 'undefined') {
      throw new Error('Invalid conversation ID');
    }
    const response = await apiClient.post(`/projects/${projectId}/tutor/conversations/${conversationId}/messages`, {
      message,
    });
    return response.data;
  },
};

export default tutorService;
