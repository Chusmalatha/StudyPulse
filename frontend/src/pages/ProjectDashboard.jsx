import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Folder,
  Target,
  FileText,
  BrainCircuit,
  MessageSquare,
  HelpCircle,
  TrendingUp,
  BarChart3,
  Sparkles,
  Edit2,
  Trash2,
  Loader2,
  Clock,
  Layers,
  LayoutDashboard,
  UploadCloud,
} from 'lucide-react';
import spacesService from '../services/api/spacesService';
import projectsService from '../services/api/projectsService';
import { useProject } from '../context/ProjectContext';
import ProjectModal from '../components/projects/ProjectModal';
import MaterialsSection from '../components/materials/MaterialsSection';
import KnowledgeSection from '../components/knowledge/KnowledgeSection';
import TutorSection from '../components/tutor/TutorSection';
import AssessmentsSection from '../components/assessments/AssessmentsSection';
import AnalyticsGrowthSection from '../components/analytics/AnalyticsGrowthSection';
import ActivityFeed from '../components/events/ActivityFeed';

const ProjectDashboard = () => {
  const { spaceId, projectId } = useParams();
  const navigate = useNavigate();
  const { setSpace, setProject } = useProject();

  const [project, setProjectData] = useState(null);
  const [space, setSpaceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [quizTargetConceptId, setQuizTargetConceptId] = useState(null);
  const [quizTargetConceptName, setQuizTargetConceptName] = useState(null);

  const handleNavigateTab = (tabId, conceptId = null, conceptName = null) => {
    if (conceptId || conceptName) {
      setQuizTargetConceptId(conceptId);
      setQuizTargetConceptName(conceptName);
    } else if (tabId !== 'quiz') {
      setQuizTargetConceptId(null);
      setQuizTargetConceptName(null);
    }
    setActiveTab(tabId);
  };

  // Edit Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProjectDetails = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [projData, spaceData] = await Promise.all([
        spacesService.getSpaceProjectDetails(spaceId, projectId),
        spacesService.getSpace(spaceId),
      ]);
      setProjectData(projData);
      setSpaceData(spaceData);
      setProject(projData);
      setSpace(spaceData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Project not found or access denied.');
    } finally {
      setIsLoading(false);
    }
  }, [spaceId, projectId, setProject, setSpace]);

  useEffect(() => {
    fetchProjectDetails();
  }, [fetchProjectDetails]);

  const handleUpdateProject = async (formData) => {
    setIsSubmitting(true);
    try {
      const updated = await projectsService.updateProject(projectId, formData);
      setProjectData(updated);
      setProject(updated);
      setIsEditModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update project.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteProject = async () => {
    if (window.confirm(`Are you sure you want to delete project "${project?.name}"?`)) {
      try {
        await projectsService.deleteProject(projectId);
        navigate(`/spaces/${spaceId}`, { replace: true });
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete project.');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400 gap-3">
        <Loader2 size={32} className="animate-spin text-violet-600" />
        <p className="text-sm font-medium">Loading project workspace...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-xl mx-auto my-12 bg-white rounded-xl border border-gray-200 p-8 text-center shadow-sm space-y-4">
        <div className="w-12 h-12 bg-red-50 text-red-600 rounded-full flex items-center justify-center mx-auto">
          <Folder size={24} />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">Project Not Found</h2>
        <p className="text-sm text-gray-500">{error || "The requested project doesn't exist in this space."}</p>
        <Link
          to={`/spaces/${spaceId}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-violet-600 hover:text-violet-700 bg-violet-50 px-4 py-2 rounded-lg transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Space
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs text-gray-500 font-medium">
        <Link to="/spaces" className="hover:text-indigo-600 transition-colors">
          Spaces
        </Link>
        <span>/</span>
        <Link to={`/spaces/${spaceId}`} className="hover:text-indigo-600 transition-colors line-clamp-1 max-w-[150px]">
          {space?.name || 'Space'}
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-semibold line-clamp-1 max-w-[200px]">{project.name}</span>
      </div>

      {/* Project Header Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-gray-100 pb-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-violet-50 text-violet-600 rounded-xl mt-0.5">
              <Folder size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
                <span className="bg-violet-50 text-violet-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-violet-100">
                  Active Workspace
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                <Clock size={12} />
                Created {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-violet-600 bg-gray-50 hover:bg-violet-50 px-3 py-2 rounded-lg border border-gray-200 transition-colors cursor-pointer"
            >
              <Edit2 size={14} />
              Edit Project
            </button>
            <button
              onClick={handleDeleteProject}
              className="flex items-center gap-1.5 text-xs font-medium text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 px-3 py-2 rounded-lg border border-red-100 transition-colors cursor-pointer"
            >
              <Trash2 size={14} />
              Delete Project
            </button>
          </div>
        </div>

        {/* Description & Learning Goal */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50/70 border border-gray-100 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              Project Description
            </h3>
            <p className="text-sm text-gray-700">
              {project.description || 'No description provided for this project.'}
            </p>
          </div>

          <div className="bg-amber-50/60 border border-amber-200/70 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-amber-900 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Target size={14} className="text-amber-600" />
              Learning Goal
            </h3>
            <p className="text-sm text-amber-950 font-medium">
              {project.learning_goal || 'No specific learning goal set.'}
            </p>
          </div>
        </div>

        {/* Tab Navigation — horizontal scroll on mobile */}
        <div className="border-t border-gray-100 pt-3 -mx-1">
          <div className="flex items-center gap-1 overflow-x-auto pb-1 px-1 scrollbar-hide">
            {[
              { id: 'overview', icon: <LayoutDashboard size={14} />, label: 'Overview' },
              { id: 'materials', icon: <UploadCloud size={14} />, label: 'Materials' },
              { id: 'knowledge', icon: <BrainCircuit size={14} />, label: 'Knowledge' },
              { id: 'tutor', icon: <MessageSquare size={14} />, label: 'AI Tutor' },
              { id: 'quiz', icon: <HelpCircle size={14} />, label: 'Quiz' },
              { id: 'analytics', icon: <TrendingUp size={14} />, label: 'Analytics & Growth' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleNavigateTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors cursor-pointer whitespace-nowrap shrink-0 ${
                  activeTab === tab.id
                    ? 'bg-violet-600 text-white shadow-xs'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Main Tab View */}
      {activeTab === 'materials' ? (
        <MaterialsSection projectId={projectId} />
      ) : activeTab === 'knowledge' ? (
        <KnowledgeSection projectId={projectId} />
      ) : activeTab === 'tutor' ? (
        <TutorSection projectId={projectId} />
      ) : activeTab === 'quiz' ? (
        <AssessmentsSection
          projectId={projectId}
          targetConceptId={quizTargetConceptId}
          targetConceptName={quizTargetConceptName}
        />
      ) : activeTab === 'analytics' ? (
        <AnalyticsGrowthSection projectId={projectId} onNavigateTab={handleNavigateTab} />
      ) : (

        /* Overview Section - Clean Workspace Shortcuts & Activity Feed */
        <div className="space-y-6">
          {/* Quick Action Shortcuts Banner */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Sparkles size={18} className="text-violet-600" />
                Quick Workspace Actions
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Jump directly to learning workflows or track your concept mastery.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <button
                onClick={() => setActiveTab('materials')}
                className="flex flex-col items-center justify-center p-4 bg-violet-50/50 hover:bg-violet-50 border border-violet-100 rounded-xl transition-all cursor-pointer group text-center space-y-2"
              >
                <div className="p-2.5 bg-violet-100 text-violet-700 rounded-lg group-hover:scale-105 transition-transform">
                  <UploadCloud size={20} />
                </div>
                <div>
                  <span className="block text-xs font-bold text-gray-900">Upload PDF</span>
                  <span className="block text-[10px] text-gray-500">Add course materials</span>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('tutor')}
                className="flex flex-col items-center justify-center p-4 bg-indigo-50/50 hover:bg-indigo-50 border border-indigo-100 rounded-xl transition-all cursor-pointer group text-center space-y-2"
              >
                <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-lg group-hover:scale-105 transition-transform">
                  <MessageSquare size={20} />
                </div>
                <div>
                  <span className="block text-xs font-bold text-gray-900">Ask AI Tutor</span>
                  <span className="block text-[10px] text-gray-500">Interactive study chat</span>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('quiz')}
                className="flex flex-col items-center justify-center p-4 bg-amber-50/50 hover:bg-amber-50 border border-amber-100 rounded-xl transition-all cursor-pointer group text-center space-y-2"
              >
                <div className="p-2.5 bg-amber-100 text-amber-700 rounded-lg group-hover:scale-105 transition-transform">
                  <HelpCircle size={20} />
                </div>
                <div>
                  <span className="block text-xs font-bold text-gray-900">Take Quiz</span>
                  <span className="block text-[10px] text-gray-500">Adaptive assessments</span>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('analytics')}
                className="flex flex-col items-center justify-center p-4 bg-emerald-50/50 hover:bg-emerald-50 border border-emerald-100 rounded-xl transition-all cursor-pointer group text-center space-y-2"
              >
                <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-lg group-hover:scale-105 transition-transform">
                  <TrendingUp size={20} />
                </div>
                <div>
                  <span className="block text-xs font-bold text-gray-900">View Progress</span>
                  <span className="block text-[10px] text-gray-500">Mastery & Analytics</span>
                </div>
              </button>
            </div>
          </div>

          {/* Activity & Background Learning Workflow Feed */}
          <ActivityFeed projectId={projectId} />
        </div>
      )}

      {/* Edit Project Modal */}
      <ProjectModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleUpdateProject}
        initialData={project}
        isSubmitting={isSubmitting}
      />
    </div>
  );
};

export default ProjectDashboard;
