import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Plus, Folder, Target, Edit2, Trash2, ArrowRight, Loader2, Folders } from 'lucide-react';
import spacesService from '../services/api/spacesService';
import projectsService from '../services/api/projectsService';
import { useProject } from '../context/ProjectContext';
import SpaceModal from '../components/spaces/SpaceModal';
import ProjectModal from '../components/projects/ProjectModal';

const SpaceDetails = () => {
  const { spaceId } = useParams();
  const navigate = useNavigate();
  const { setSpace } = useProject();

  const [space, setSpaceData] = useState(null);
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Space Modal
  const [isSpaceModalOpen, setIsSpaceModalOpen] = useState(false);
  const [isUpdatingSpace, setIsUpdatingSpace] = useState(false);

  // Project Modal
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [isSubmittingProject, setIsSubmittingProject] = useState(false);

  const fetchSpaceDetails = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [spaceData, projectsData] = await Promise.all([
        spacesService.getSpace(spaceId),
        spacesService.getSpaceProjects(spaceId),
      ]);
      setSpaceData(spaceData);
      setProjects(projectsData);
      setSpace(spaceData); // Sync context
    } catch (err) {
      setError(err.response?.data?.detail || 'Space not found or access denied.');
    } finally {
      setIsLoading(false);
    }
  }, [spaceId, setSpace]);

  useEffect(() => {
    fetchSpaceDetails();
  }, [fetchSpaceDetails]);

  // Space Actions
  const handleUpdateSpace = async (formData) => {
    setIsUpdatingSpace(true);
    try {
      const updated = await spacesService.updateSpace(spaceId, formData);
      setSpaceData(updated);
      setSpace(updated);
      setIsSpaceModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update space.');
    } finally {
      setIsUpdatingSpace(false);
    }
  };

  const handleDeleteSpace = async () => {
    if (window.confirm(`Are you sure you want to delete "${space?.name}"? All projects in this space will be deleted.`)) {
      try {
        await spacesService.deleteSpace(spaceId);
        navigate('/spaces', { replace: true });
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete space.');
      }
    }
  };

  // Project Actions
  const handleCreateProjectOpen = () => {
    setEditingProject(null);
    setIsProjectModalOpen(true);
  };

  const handleEditProjectOpen = (e, project) => {
    e.stopPropagation();
    setEditingProject(project);
    setIsProjectModalOpen(true);
  };

  const handleDeleteProject = async (e, projectId, projectName) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete project "${projectName}"?`)) {
      try {
        await projectsService.deleteProject(projectId);
        setProjects((prev) => prev.filter((p) => p.id !== projectId));
        setSpaceData((prev) => (prev ? { ...prev, project_count: Math.max(0, (prev.project_count || 1) - 1) } : prev));
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete project.');
      }
    }
  };

  const handleProjectModalSubmit = async (formData) => {
    setIsSubmittingProject(true);
    try {
      if (editingProject) {
        const updated = await projectsService.updateProject(editingProject.id, formData);
        setProjects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      } else {
        const created = await spacesService.createSpaceProject(spaceId, formData);
        setProjects((prev) => [created, ...prev]);
        setSpaceData((prev) => (prev ? { ...prev, project_count: (prev.project_count || 0) + 1 } : prev));
      }
      setIsProjectModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save project.');
    } finally {
      setIsSubmittingProject(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400 gap-3">
        <Loader2 size={32} className="animate-spin text-indigo-600" />
        <p className="text-sm font-medium">Loading space details...</p>
      </div>
    );
  }

  if (error || !space) {
    return (
      <div className="max-w-xl mx-auto my-12 bg-white rounded-xl border border-gray-200 p-8 text-center shadow-sm space-y-4">
        <div className="w-12 h-12 bg-red-50 text-red-600 rounded-full flex items-center justify-center mx-auto">
          <Folders size={24} />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">Space Not Found</h2>
        <p className="text-sm text-gray-500">{error || "The space you requested doesn't exist or you don't have access."}</p>
        <Link
          to="/spaces"
          className="inline-flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-4 py-2 rounded-lg transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Spaces
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          to="/spaces"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft size={14} />
          Back to Spaces
        </Link>
      </div>

      {/* Space Header Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
                <Folders size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{space.name}</h1>
                <p className="text-xs text-gray-400">
                  Created on {new Date(space.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            {space.description && (
              <p className="text-sm text-gray-600 pt-1 pl-1 max-w-3xl">
                {space.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setIsSpaceModalOpen(true)}
              className="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-indigo-600 bg-gray-50 hover:bg-indigo-50 px-3 py-2 rounded-lg border border-gray-200 transition-colors"
            >
              <Edit2 size={14} />
              Edit Space
            </button>
            <button
              onClick={handleDeleteSpace}
              className="flex items-center gap-1.5 text-xs font-medium text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 px-3 py-2 rounded-lg border border-red-100 transition-colors"
            >
              <Trash2 size={14} />
              Delete Space
            </button>
          </div>
        </div>
      </div>

      {/* Projects Section Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Folder size={20} className="text-violet-600" />
            Projects ({projects.length})
          </h2>
          <p className="text-xs text-gray-500">
            Focused learning journeys inside this Space.
          </p>
        </div>
        <button
          onClick={handleCreateProjectOpen}
          id="create-project-btn"
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white font-medium text-sm px-4 py-2 rounded-lg shadow-sm transition-colors"
        >
          <Plus size={16} />
          Create Project
        </button>
      </div>

      {/* Projects Grid / Empty State */}
      {projects.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
          <div className="w-14 h-14 bg-violet-50 text-violet-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Folder size={28} />
          </div>
          <h3 className="text-base font-semibold text-gray-900 mb-1">No Projects Yet</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto mb-5">
            Create a project inside "{space.name}" to organize learning materials, quizzes, and tutor sessions.
          </p>
          <button
            onClick={handleCreateProjectOpen}
            className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white font-medium text-xs px-4 py-2.5 rounded-lg shadow-sm transition-colors"
          >
            <Plus size={16} />
            Create Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => navigate(`/spaces/${spaceId}/projects/${project.id}`)}
              className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md hover:border-violet-300 transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2.5 bg-violet-50 text-violet-600 rounded-lg group-hover:bg-violet-600 group-hover:text-white transition-colors">
                      <Folder size={20} />
                    </div>
                    <h3 className="font-semibold text-gray-900 group-hover:text-violet-600 transition-colors line-clamp-1">
                      {project.name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => handleEditProjectOpen(e, project)}
                      title="Edit Project"
                      className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={(e) => handleDeleteProject(e, project.id, project.name)}
                      title="Delete Project"
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-gray-600 line-clamp-2 min-h-[2rem] mb-3">
                  {project.description || 'No description provided.'}
                </p>

                {project.learning_goal && (
                  <div className="bg-amber-50/60 border border-amber-200/60 rounded-lg p-2.5 mb-3 flex items-start gap-2">
                    <Target size={14} className="text-amber-600 shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-900 font-medium line-clamp-2">
                      {project.learning_goal}
                    </p>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
                <span>Updated {new Date(project.updated_at || project.created_at).toLocaleDateString()}</span>
                <span className="flex items-center gap-1 text-violet-600 font-semibold group-hover:translate-x-0.5 transition-transform">
                  Dashboard
                  <ArrowRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      <SpaceModal
        isOpen={isSpaceModalOpen}
        onClose={() => setIsSpaceModalOpen(false)}
        onSubmit={handleUpdateSpace}
        initialData={space}
        isSubmitting={isUpdatingSpace}
      />

      <ProjectModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        onSubmit={handleProjectModalSubmit}
        initialData={editingProject}
        isSubmitting={isSubmittingProject}
      />
    </div>
  );
};

export default SpaceDetails;
