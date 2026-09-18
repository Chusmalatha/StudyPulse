import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from '../components/layout/AppLayout';
import ProtectedRoute from '../components/common/ProtectedRoute';
import PublicRoute from '../components/common/PublicRoute';
import AdminRoute from '../components/common/AdminRoute';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Dashboard from '../pages/Dashboard';
import Spaces from '../pages/Spaces';
import SpaceDetails from '../pages/SpaceDetails';
import ProjectDashboard from '../pages/ProjectDashboard';
import Projects from '../pages/Projects';
import Admin from '../pages/Admin';
import Home from '../pages/Home';
import { ProjectProvider } from '../context/ProjectContext';

const AppRoutes = () => {
  return (
    <Routes>
      {/* Public auth routes — redirect if already logged in */}
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />

      {/* Protected student routes with student AppLayout */}
      <Route
        element={
          <ProtectedRoute>
            <ProjectProvider>
              <AppLayout />
            </ProjectProvider>
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/spaces" element={<Spaces />} />
        <Route path="/spaces/:spaceId" element={<SpaceDetails />} />
        <Route path="/spaces/:spaceId/projects/:projectId" element={<ProjectDashboard />} />
        <Route path="/projects" element={<Projects />} />
      </Route>

      {/* Dedicated Admin Portal Route — strictly protected with AdminRoute */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <Admin />
          </AdminRoute>
        }
      />

      {/* Catch-all → send to register for new users */}
      <Route path="*" element={<Navigate to="/register" replace />} />
    </Routes>
  );
};

export default AppRoutes;
