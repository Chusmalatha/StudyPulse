import React, { useState, useEffect } from 'react';
import { X, Loader2, Folder, Target } from 'lucide-react';

const ProjectModal = ({ isOpen, onClose, onSubmit, initialData = null, isSubmitting = false }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [learningGoal, setLearningGoal] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialData) {
      setName(initialData.name || '');
      setDescription(initialData.description || '');
      setLearningGoal(initialData.learning_goal || '');
    } else {
      setName('');
      setDescription('');
      setLearningGoal('');
    }
    setError('');
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Project name is required.');
      return;
    }
    setError('');
    onSubmit({
      name: name.trim(),
      description: description.trim(),
      learning_goal: learningGoal.trim(),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden border border-gray-100">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-violet-50 text-violet-600 rounded-lg">
              <Folder size={20} />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">
              {initialData ? 'Edit Project' : 'Create New Project'}
            </h2>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Build ML Fundamentals"
              maxLength={100}
              required
              disabled={isSubmitting}
              className="w-full px-3.5 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 text-sm outline-none transition-all disabled:bg-gray-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of what this project covers..."
              rows={2}
              maxLength={1000}
              disabled={isSubmitting}
              className="w-full px-3.5 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 text-sm outline-none transition-all disabled:bg-gray-50 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1.5">
              <Target size={14} className="text-amber-500" />
              Learning Goal
            </label>
            <textarea
              value={learningGoal}
              onChange={(e) => setLearningGoal(e.target.value)}
              placeholder="What do you aim to achieve? (e.g., Master regression models & evaluation metrics)"
              rows={3}
              maxLength={1000}
              disabled={isSubmitting}
              className="w-full px-3.5 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 text-sm outline-none transition-all disabled:bg-gray-50 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">
              Used by AI Tutor, Quizzes, and Mastery tracking in upcoming phases.
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-violet-600 hover:bg-violet-700 rounded-lg transition-colors disabled:opacity-50 shadow-sm"
            >
              {isSubmitting && <Loader2 size={16} className="animate-spin" />}
              {initialData ? 'Save Changes' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProjectModal;
