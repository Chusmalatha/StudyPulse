import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

/**
 * Wraps public-only routes (login, register).
 * - While auth state is loading → show spinner.
 * - Already authenticated → redirect to /dashboard (no need to register/login again).
 * - Not authenticated → render the public page (login or register).
 */
const PublicRoute = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (isAuthenticated) {
    const target = user?.role === 'admin' ? '/admin' : '/dashboard';
    return <Navigate to={target} replace />;
  }

  return children;
};

export default PublicRoute;
