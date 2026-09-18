import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../services/api/apiClient';
import authService from '../services/api/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true); // true while verifying token on mount

  // ── Load user from stored token on first render ────────────────────────────
  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      // Token exists — verify it and load current user
      try {
        const userData = await authService.me();
        setUser(userData);
      } catch {
        // Token is invalid/expired — clean up
        localStorage.removeItem('access_token');
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  // ── Actions ────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const data = await authService.login({ email, password });
    localStorage.setItem('access_token', data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (name, email, password) => {
    return await authService.register({ name, email, password });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setUser(null);
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};

export default AuthContext;
