import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Folder, Search, Target, Folders, ArrowRight, Loader2 } from 'lucide-react';
import spacesService from '../services/api/spacesService';

const Projects = () => {
  const navigate = useNavigate();
  const [spaces, setSpaces] = useState([]);
  const [projectsList, setProjectsList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);

  const fetchAllUserProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const userSpaces = await spacesService.getSpaces();
      setSpaces(userSpaces);

      // Fetch projects for all spaces owned by the user
      const projectPromises = userSpaces.map(async (space) => {
        const spaceProjects = await spacesService.getSpaceProjects(space.id);
        return spaceProjects.map((p) => ({ ...p, spaceName: space.name }));
      });

      const allProjectsArrays = await Promise.all(projectPromises);
      const combinedProjects = allProjectsArrays.flat();
      setProjectsList(combinedProjects);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load projects.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllUserProjects();
  }, [fetchAllUserProjects]);

  const filteredProjects = projectsList.filter(
    (proj) =>
      proj.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      proj.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      proj.learning_goal.toLowerCase().includes(searchQuery.toLowerCase()) ||
      proj.spaceName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Folder className="text-violet-600" size={26} />
            All Learning Projects
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Overview of all your focused projects across all Spaces.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      {projectsList.length > 0 && (
        <div className="relative max-w-md">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects or learning goals..."
            className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all shadow-sm"
          />
        </div>
      )}

      {/* Main Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
          <Loader2 size={32} className="animate-spin text-violet-600" />
          <p className="text-sm font-medium">Loading projects...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm">
          {error}
        </div>
      ) : projectsList.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
          <div className="w-16 h-16 bg-violet-50 text-violet-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Folder size={32} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No Projects Found</h3>
          <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
            Projects live inside Spaces. Open or create a Space to add your first learning project.
          </p>
          <Link
            to="/spaces"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-5 py-2.5 rounded-lg shadow-sm transition-colors"
          >
            <Folders size={18} />
            Go to Spaces
          </Link>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500 text-sm">
          No projects match your search "{searchQuery}".
        </div>
      ) : (
        /* Projects Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              onClick={() => navigate(`/spaces/${project.space_id}/projects/${project.id}`)}
              className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md hover:border-violet-300 transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="bg-indigo-50 text-indigo-700 text-xs font-semibold px-2.5 py-1 rounded-md border border-indigo-100/80 flex items-center gap-1.5">
                    <Folders size={12} />
                    {project.spaceName}
                  </span>
                </div>

                <div className="flex items-center gap-2.5 mb-2">
                  <div className="p-2 bg-violet-50 text-violet-600 rounded-lg group-hover:bg-violet-600 group-hover:text-white transition-colors">
                    <Folder size={18} />
                  </div>
                  <h3 className="font-semibold text-gray-900 group-hover:text-violet-600 transition-colors line-clamp-1">
                    {project.name}
                  </h3>
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
                  Open Project
                  <ArrowRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Projects;
