import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Folders, Folder, Edit2, Trash2, ArrowRight, Loader2 } from 'lucide-react';
import spacesService from '../services/api/spacesService';
import SpaceModal from '../components/spaces/SpaceModal';

const Spaces = () => {
  const navigate = useNavigate();
  const [spaces, setSpaces] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSpace, setEditingSpace] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchSpaces = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await spacesService.getSpaces();
      setSpaces(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load spaces.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSpaces();
  }, [fetchSpaces]);

  const handleCreateOpen = () => {
    setEditingSpace(null);
    setIsModalOpen(true);
  };

  const handleEditOpen = (e, space) => {
    e.stopPropagation();
    setEditingSpace(space);
    setIsModalOpen(true);
  };

  const handleDelete = async (e, spaceId, spaceName) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete "${spaceName}"? All projects inside it will be permanently deleted.`)) {
      try {
        await spacesService.deleteSpace(spaceId);
        setSpaces((prev) => prev.filter((s) => s.id !== spaceId));
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete space.');
      }
    }
  };

  const handleModalSubmit = async (formData) => {
    setIsSubmitting(true);
    try {
      if (editingSpace) {
        const updated = await spacesService.updateSpace(editingSpace.id, formData);
        setSpaces((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      } else {
        const created = await spacesService.createSpace(formData);
        setSpaces((prev) => [created, ...prev]);
      }
      setIsModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save space.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredSpaces = spaces.filter(
    (space) =>
      space.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      space.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Folders className="text-indigo-600" size={26} />
            Learning Spaces
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Spaces represent broad learning subjects like Machine Learning, Full Stack, or NPTEL.
          </p>
        </div>
        <button
          onClick={handleCreateOpen}
          id="create-space-btn"
          className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-4 py-2.5 rounded-lg shadow-sm transition-colors shrink-0"
        >
          <Plus size={18} />
          Create Space
        </button>
      </div>

      {/* Search Bar */}
      {spaces.length > 0 && (
        <div className="relative max-w-md">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search spaces..."
            className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
          />
        </div>
      )}

      {/* Main Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
          <Loader2 size={32} className="animate-spin text-indigo-600" />
          <p className="text-sm font-medium">Loading spaces...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm">
          {error}
        </div>
      ) : spaces.length === 0 ? (
        /* Empty State */
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
          <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Folders size={32} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No Spaces Yet</h3>
          <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
            Get started by creating your first Space to organize your learning projects and study goals.
          </p>
          <button
            onClick={handleCreateOpen}
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-5 py-2.5 rounded-lg shadow-sm transition-colors"
          >
            <Plus size={18} />
            Create Your First Space
          </button>
        </div>
      ) : filteredSpaces.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500 text-sm">
          No spaces match your search "{searchQuery}".
        </div>
      ) : (
        /* Spaces Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredSpaces.map((space) => (
            <div
              key={space.id}
              onClick={() => navigate(`/spaces/${space.id}`)}
              className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                      <Folders size={20} />
                    </div>
                    <h2 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                      {space.name}
                    </h2>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => handleEditOpen(e, space)}
                      title="Edit Space"
                      className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      onClick={(e) => handleDelete(e, space.id, space.name)}
                      title="Delete Space"
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-gray-600 line-clamp-2 min-h-[2.5rem] mb-4">
                  {space.description || 'No description provided.'}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                <span className="flex items-center gap-1.5 font-medium text-gray-700 bg-gray-50 px-2.5 py-1 rounded-md border border-gray-100">
                  <Folder size={14} className="text-violet-500" />
                  {space.project_count || 0} {space.project_count === 1 ? 'Project' : 'Projects'}
                </span>

                <span className="flex items-center gap-1 text-indigo-600 font-medium group-hover:translate-x-0.5 transition-transform">
                  View Space
                  <ArrowRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      <SpaceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleModalSubmit}
        initialData={editingSpace}
        isSubmitting={isSubmitting}
      />
    </div>
  );
};

export default Spaces;
