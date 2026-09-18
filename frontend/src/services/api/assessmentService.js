import apiClient from './apiClient';

const assessmentService = {
  /**
   * Create a new adaptive assessment for a project
   * @param {string} projectId
   * @param {number} questionCount
   * @returns {Promise<Object>} Assessment object with initial question list
   */
  createAssessment: async (projectId, questionCount = 5, targetConceptId = null) => {
    const payload = { question_count: questionCount };
    if (targetConceptId) {
      payload.target_concept_id = targetConceptId;
    }
    const response = await apiClient.post(`/projects/${projectId}/assessments`, payload);
    return response.data;
  },

  /**
   * List all past assessments for a project
   * @param {string} projectId
   * @returns {Promise<Array>} List of assessment objects
   */
  getAssessments: async (projectId) => {
    const response = await apiClient.get(`/projects/${projectId}/assessments`);
    return response.data;
  },

  /**
   * Get single assessment details & current questions
   * @param {string} projectId
   * @param {string} assessmentId
   * @returns {Promise<Object>} Assessment object
   */
  getAssessment: async (projectId, assessmentId) => {
    const response = await apiClient.get(`/projects/${projectId}/assessments/${assessmentId}`);
    return response.data;
  },

  /**
   * Submit answer for MCQ or Open-Ended question
   * @param {string} projectId
   * @param {string} assessmentId
   * @param {string} questionId
   * @param {string} answer
   * @returns {Promise<Object>} Result response containing correctness or qualitative evaluation
   */
  submitAnswer: async (projectId, assessmentId, questionId, answer) => {
    const response = await apiClient.post(
      `/projects/${projectId}/assessments/${assessmentId}/questions/${questionId}/answer`,
      { answer }
    );
    return response.data;
  },

  /**
   * Complete an assessment and compute overall score
   * @param {string} projectId
   * @param {string} assessmentId
   * @returns {Promise<Object>} Completed assessment object
   */
  completeAssessment: async (projectId, assessmentId) => {
    const response = await apiClient.post(`/projects/${projectId}/assessments/${assessmentId}/complete`);
    return response.data;
  },
};

export default assessmentService;
