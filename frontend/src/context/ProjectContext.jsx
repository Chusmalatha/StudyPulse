import React, { createContext, useContext, useState, useCallback } from 'react';

const ProjectContext = createContext(null);

export const ProjectProvider = ({ children }) => {
  const [currentSpace, setCurrentSpace] = useState(null);
  const [currentProject, setCurrentProject] = useState(null);

  const setSpace = useCallback((space) => {
    setCurrentSpace(space);
  }, []);

  const setProject = useCallback((project) => {
    setCurrentProject(project);
  }, []);

  const clearProjectContext = useCallback(() => {
    setCurrentSpace(null);
    setCurrentProject(null);
  }, []);

  const value = {
    currentSpace,
    currentProject,
    setSpace,
    setProject,
    clearProjectContext,
  };

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
};

export const useProject = () => {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error('useProject must be used inside <ProjectProvider>');
  return ctx;
};

export default ProjectContext;
