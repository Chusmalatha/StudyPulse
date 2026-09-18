import apiClient from './apiClient';

const authService = {
  /**
   * POST /auth/register
   * Returns the newly created user (no token — user must then log in).
   */
  register: async ({ name, email, password }) => {
    const resp = await apiClient.post('/auth/register', { name, email, password });
    return resp.data;
  },

  /**
   * POST /auth/login
   * Returns { access_token, token_type, user }
   */
  login: async ({ email, password }) => {
    const resp = await apiClient.post('/auth/login', { email, password });
    return resp.data;
  },

  /**
   * GET /auth/me
   * Returns the currently authenticated user profile.
   */
  me: async () => {
    const resp = await apiClient.get('/auth/me');
    return resp.data;
  },
};

export default authService;
