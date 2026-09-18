import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  Trash2,
  Eye,
  Loader2,
  Clock,
  HardDrive,
  BookOpen,
  X,
  Layers,
  Sparkles,
} from 'lucide-react';
import materialsService from '../../services/api/materialsService';

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

const MaterialsSection = ({ projectId }) => {
  const [materials, setMaterials] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Chunk Inspector Modal State
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [isLoadingChunks, setIsLoadingChunks] = useState(false);
  const [chunkError, setChunkError] = useState(null);

  // Retry loading state per material
  const [retryingId, setRetryingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // Fetch materials for current project
  const fetchMaterials = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true);
    try {
      const data = await materialsService.getProjectMaterials(projectId);
      setMaterials(data);
    } catch (err) {
      console.error('Failed to fetch materials:', err);
    } finally {
      if (!silent) setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchMaterials();
  }, [fetchMaterials]);

  // Live Auto-polling when any material is QUEUED or PROCESSING
  useEffect(() => {
    const hasPending = materials.some(
      (m) => m.status === 'QUEUED' || m.status === 'PROCESSING'
    );

    if (!hasPending) return;

    const interval = setInterval(() => {
      fetchMaterials(true);
    }, 3000);

    return () => clearInterval(interval);
  }, [materials, fetchMaterials]);

  // Handle PDF file upload
  const handleUploadFile = async (file) => {
    setUploadError(null);

    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF files are supported.');
      return;
    }

    if (file.size === 0) {
      setUploadError('Selected PDF file is empty.');
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setUploadError(
        `File size exceeds 25MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`
      );
      return;
    }

    setIsUploading(true);
    try {
      const newMaterial = await materialsService.uploadMaterial(projectId, file);
      setMaterials((prev) => [newMaterial, ...prev.filter((m) => m.id !== newMaterial.id)]);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to upload PDF material.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUploadFile(e.dataTransfer.files[0]);
    }
  };

  // Retry failed material
  const handleRetry = async (materialId) => {
    setRetryingId(materialId);
    try {
      await materialsService.retryMaterial(materialId);
      await fetchMaterials(true);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to retry material.');
    } finally {
      setRetryingId(null);
    }
  };

  // Delete material
  const handleDelete = async (material) => {
    if (
      !window.confirm(
        `Are you sure you want to delete material "${material.filename}"? This will permanently remove its stored file and processed chunks.`
      )
    ) {
      return;
    }

    setDeletingId(material.id);
    try {
      await materialsService.deleteMaterial(material.id);
      setMaterials((prev) => prev.filter((m) => m.id !== material.id));
      if (selectedMaterial?.id === material.id) {
        setSelectedMaterial(null);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete material.');
    } finally {
      setDeletingId(null);
    }
  };

  // View chunks in inspector modal
  const handleInspectChunks = async (material) => {
    setSelectedMaterial(material);
    setIsLoadingChunks(true);
    setChunkError(null);
    try {
      const data = await materialsService.getMaterialChunks(material.id);
      setChunks(data);
    } catch (err) {
      setChunkError(err.response?.data?.detail || 'Failed to load chunks.');
    } finally {
      setIsLoadingChunks(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
            Queued
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-violet-50 text-violet-700 border border-violet-200">
            <Loader2 size={12} className="animate-spin text-violet-600" />
            Processing...
          </span>
        );
      case 'READY':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 size={13} className="text-emerald-600" />
            Ready
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <AlertCircle size={13} className="text-red-600" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Upload Box / Dropzone */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <UploadCloud size={20} className="text-violet-600" />
              Upload PDF Materials
            </h2>
            <p className="text-xs text-gray-500">
              Upload textbook chapters, lecture slides, or study notes. Pages are extracted & chunked with citation metadata.
            </p>
          </div>
        </div>

        {uploadError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs font-medium text-red-700 flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            dragActive
              ? 'border-violet-500 bg-violet-50/50'
              : 'border-gray-200 hover:border-violet-400 hover:bg-gray-50/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => e.target.files?.[0] && handleUploadFile(e.target.files[0])}
            className="hidden"
          />

          <div className="w-12 h-12 bg-violet-100 text-violet-600 rounded-full flex items-center justify-center mx-auto mb-3">
            {isUploading ? (
              <Loader2 size={24} className="animate-spin" />
            ) : (
              <UploadCloud size={24} />
            )}
          </div>

          <p className="text-sm font-semibold text-gray-800 mb-1">
            {isUploading ? 'Uploading PDF Material...' : 'Click to upload or drag & drop PDF'}
          </p>
          <p className="text-xs text-gray-400">PDF documents up to 25MB</p>
        </div>
      </div>

      {/* Materials List Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BookOpen size={20} className="text-violet-600" />
              Project Materials ({materials.length})
            </h2>
            <p className="text-xs text-gray-500">
              Processed learning documents ready for AI grounded citations.
            </p>
          </div>
          {materials.some((m) => m.status === 'QUEUED' || m.status === 'PROCESSING') && (
            <div className="flex items-center gap-1.5 text-xs text-violet-600 font-medium bg-violet-50 px-3 py-1.5 rounded-full border border-violet-100 animate-pulse">
              <Loader2 size={13} className="animate-spin" />
              Auto-refreshing status...
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-gray-400 gap-2">
            <Loader2 size={24} className="animate-spin text-violet-600" />
            <span className="text-sm">Loading materials...</span>
          </div>
        ) : materials.length === 0 ? (
          <div className="text-center py-12 bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
            <FileText size={40} className="mx-auto text-gray-300 mb-2" />
            <h3 className="text-sm font-semibold text-gray-700">No Materials Uploaded Yet</h3>
            <p className="text-xs text-gray-400 max-w-sm mx-auto mt-1">
              Upload your first PDF document above to start extracting knowledge chunks.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {materials.map((mat) => (
              <div
                key={mat.id}
                className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-2xs"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-violet-50 text-violet-600 rounded-xl mt-0.5 shrink-0">
                    <FileText size={22} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-gray-900 text-sm">{mat.filename}</h3>
                      {renderStatusBadge(mat.status)}
                    </div>

                    <div className="flex items-center gap-4 text-xs text-gray-400 mt-1">
                      <span className="flex items-center gap-1">
                        <HardDrive size={12} />
                        {formatFileSize(mat.file_size)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        Uploaded {new Date(mat.created_at).toLocaleDateString()}
                      </span>
                      {mat.processing_attempts > 0 && (
                        <span>Attempts: {mat.processing_attempts}</span>
                      )}
                    </div>

                    {mat.status === 'FAILED' && mat.error_message && (
                      <div className="mt-2 text-xs font-medium text-red-600 bg-red-50 p-2 rounded-md border border-red-100 flex items-center gap-1.5">
                        <AlertCircle size={14} className="shrink-0" />
                        <span>{mat.error_message}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  {mat.status === 'READY' && (
                    <button
                      onClick={() => handleInspectChunks(mat)}
                      className="flex items-center gap-1.5 text-xs font-medium text-violet-600 hover:text-violet-700 bg-violet-50 hover:bg-violet-100 px-3 py-1.5 rounded-lg border border-violet-100 transition-colors"
                    >
                      <Eye size={14} />
                      Inspect Chunks
                    </button>
                  )}

                  {mat.status === 'FAILED' && (
                    <button
                      onClick={() => handleRetry(mat.id)}
                      disabled={retryingId === mat.id}
                      className="flex items-center gap-1.5 text-xs font-medium text-amber-700 hover:text-amber-800 bg-amber-50 hover:bg-amber-100 px-3 py-1.5 rounded-lg border border-amber-200 transition-colors disabled:opacity-50"
                    >
                      <RotateCw
                        size={14}
                        className={retryingId === mat.id ? 'animate-spin' : ''}
                      />
                      Retry
                    </button>
                  )}

                  <button
                    onClick={() => handleDelete(mat)}
                    disabled={deletingId === mat.id}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    title="Delete Material"
                  >
                    {deletingId === mat.id ? (
                      <Loader2 size={16} className="animate-spin text-red-600" />
                    ) : (
                      <Trash2 size={16} />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chunk Inspector Modal */}
      {selectedMaterial && (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-gray-100">
            {/* Header */}
            <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50 rounded-t-2xl">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-violet-100 text-violet-700 rounded-xl">
                  <Layers size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-base">
                    Chunk Citation Metadata Inspector
                  </h3>
                  <p className="text-xs text-gray-500 line-clamp-1">
                    {selectedMaterial.filename} • {chunks.length} Extracted Chunks
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedMaterial(null)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {isLoadingChunks ? (
                <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-2">
                  <Loader2 size={28} className="animate-spin text-violet-600" />
                  <span className="text-sm font-medium">Loading extracted chunks & vector metadata...</span>
                </div>
              ) : chunkError ? (
                <div className="p-4 bg-red-50 text-red-700 rounded-xl text-xs font-medium border border-red-200 flex items-center gap-2">
                  <AlertCircle size={16} />
                  <span>{chunkError}</span>
                </div>
              ) : chunks.length === 0 ? (
                <div className="text-center py-12 text-gray-400 text-xs">
                  No extracted chunks found for this material.
                </div>
              ) : (
                <div className="space-y-3">
                  {chunks.map((chunk, i) => (
                    <div
                      key={chunk.id || i}
                      className="bg-gray-50/70 border border-gray-200 rounded-xl p-4 text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between text-gray-500 border-b border-gray-200/60 pb-2">
                        <span className="font-semibold text-violet-700 bg-violet-50 px-2.5 py-0.5 rounded-md border border-violet-100 flex items-center gap-1">
                          <Sparkles size={11} />
                          Page {chunk.page_number}
                        </span>
                        <span className="font-mono text-[11px] text-gray-400">
                          Chunk #{chunk.chunk_index + 1}
                        </span>
                      </div>
                      <p className="text-gray-800 font-normal leading-relaxed whitespace-pre-wrap">
                        {chunk.chunk_text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-100 bg-gray-50/50 rounded-b-2xl flex justify-end">
              <button
                onClick={() => setSelectedMaterial(null)}
                className="px-4 py-2 text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaterialsSection;
