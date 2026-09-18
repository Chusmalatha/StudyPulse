import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  BrainCircuit,
  BookOpen,
  Sparkles,
  Layers,
  FileText,
  RotateCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Hash,
  ChevronRight,
  Bookmark,
  Info,
} from 'lucide-react';
import knowledgeService from '../../services/api/knowledgeService';
import FormattedMarkdown from '../common/FormattedMarkdown';

const KnowledgeSection = ({ projectId }) => {
  const [knowledge, setKnowledge] = useState({ concepts: [], topics: [], sections: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState(null);

  // Active view tab ('all', 'concepts', 'topics', 'sections')
  const [activeSubTab, setActiveSubTab] = useState('all');

  const fetchKnowledge = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await knowledgeService.getProjectKnowledge(projectId);
      setKnowledge(data);
    } catch (err) {
      console.error('Failed to fetch project knowledge:', err);
      setError('Failed to load project knowledge base.');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchKnowledge();
  }, [fetchKnowledge]);

  const handleTriggerExtraction = async () => {
    setIsExtracting(true);
    try {
      const data = await knowledgeService.extractProjectKnowledge(projectId);
      setKnowledge(data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to extract project knowledge.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await knowledgeService.searchProjectKnowledge(projectId, searchQuery.trim(), 5);
      setSearchResults(data);
    } catch (err) {
      setSearchError(err.response?.data?.detail || 'Search query failed.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
    setSearchError(null);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Search Header Card */}
      <div className="bg-gradient-to-br from-violet-950 via-slate-900 to-indigo-950 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-violet-300 uppercase tracking-widest">
            <Sparkles size={14} className="text-amber-400 animate-pulse" />
            Semantic Retrieval & Grounded Vector Search
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Search Project Knowledge
          </h2>
          <p className="text-sm text-gray-300 leading-relaxed">
            Query your uploaded materials with natural language to retrieve relevant text chunks, page citations, and similarity scores.
          </p>

          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 pt-2">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ask a question (e.g. 'What is regularization and gradient descent?')"
                className="w-full bg-white/10 backdrop-blur-md border border-white/20 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-gray-400 focus:outline-hidden focus:ring-2 focus:ring-violet-400 focus:bg-white/15 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={isSearching || !searchQuery.trim()}
              className="flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 text-white text-sm font-semibold px-6 py-3 rounded-xl shadow-lg transition-all cursor-pointer shrink-0"
            >
              {isSearching ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              Search Knowledge
            </button>
          </form>

          {searchResults && (
            <div className="flex items-center justify-between text-xs text-violet-300 pt-1">
              <span>
                Found {searchResults.total_results} relevant results for "{searchResults.query}"
              </span>
              <button
                onClick={handleClearSearch}
                className="hover:text-white underline cursor-pointer"
              >
                Clear Results
              </button>
            </div>
          )}
        </div>
      </div>

      {/* RAG Search Results Section */}
      {searchResults && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="font-bold text-gray-900 text-base flex items-center gap-2">
              <BrainCircuit size={20} className="text-violet-600" />
              Top Semantic Search Results ({searchResults.results.length})
            </h3>
          </div>

          {searchError && (
            <div className="p-3 bg-red-50 text-red-700 rounded-lg text-xs font-medium border border-red-200 flex items-center gap-2">
              <AlertCircle size={16} />
              <span>{searchError}</span>
            </div>
          )}

          {searchResults.results.length === 0 ? (
            <div className="text-center py-10 text-gray-500 bg-gray-50/50 rounded-xl border border-dashed border-gray-200 space-y-1">
              <Info size={28} className="mx-auto text-gray-400" />
              <p className="text-sm font-semibold text-gray-700">No sufficiently relevant project knowledge found.</p>
              <p className="text-xs text-gray-400 max-w-md mx-auto">
                Try rephrasing your search query or upload additional PDF materials to expand the knowledge base.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {searchResults.results.map((result, idx) => (
                <div
                  key={result.chunk_id || idx}
                  className="bg-white border border-gray-200 rounded-xl p-5 hover:border-violet-300 transition-all shadow-2xs space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="bg-violet-100 text-violet-800 text-xs font-bold px-2.5 py-0.5 rounded-md flex items-center gap-1">
                        <FileText size={12} />
                        {result.filename}
                      </span>
                      <span className="bg-amber-100 text-amber-900 text-xs font-bold px-2.5 py-0.5 rounded-md flex items-center gap-1">
                        <Sparkles size={11} className="text-amber-600" />
                        Page {result.page_number}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      <span>Relevance: {(result.score * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  <FormattedMarkdown content={result.chunk_text} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Knowledge Base Content Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <BrainCircuit size={20} className="text-emerald-600" />
              Extracted Project Knowledge Structure
            </h2>
            <p className="text-xs text-gray-500">
              Grounded concepts, domain topics, and document sections auto-extracted from project PDFs.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleTriggerExtraction}
              disabled={isExtracting}
              className="flex items-center gap-1.5 text-xs font-semibold text-violet-700 bg-violet-50 hover:bg-violet-100 px-3.5 py-2 rounded-xl border border-violet-200 transition-colors disabled:opacity-50 cursor-pointer"
            >
              <RotateCw size={14} className={isExtracting ? 'animate-spin' : ''} />
              {isExtracting ? 'Extracting Knowledge...' : 'Refresh Knowledge'}
            </button>
          </div>
        </div>

        {/* Navigation Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-gray-100 pb-3">
          {[
            { id: 'all', label: 'All Knowledge', count: knowledge.concepts.length + knowledge.sections.length },
            { id: 'concepts', label: 'Concepts', count: knowledge.concepts.length },
            { id: 'sections', label: 'Sections', count: knowledge.sections.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
                activeSubTab === tab.id
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                activeSubTab === tab.id ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-600'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-gray-400 gap-2">
            <Loader2 size={24} className="animate-spin text-emerald-600" />
            <span className="text-sm font-medium">Loading project knowledge...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl text-xs font-medium border border-red-200 flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        ) : knowledge.concepts.length === 0 && knowledge.topics.length === 0 && knowledge.sections.length === 0 ? (
          <div className="text-center py-12 bg-gray-50/50 rounded-xl border border-dashed border-gray-200 space-y-2">
            <BrainCircuit size={40} className="mx-auto text-gray-300" />
            <h3 className="text-sm font-semibold text-gray-700">No Extracted Knowledge Yet</h3>
            <p className="text-xs text-gray-400 max-w-sm mx-auto">
              Upload PDF materials in the Materials tab or click "Refresh Knowledge" to generate concepts and topics.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Concepts Section */}
            {(activeSubTab === 'all' || activeSubTab === 'concepts') && (
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Bookmark size={14} className="text-violet-600" />
                  Key Concepts ({knowledge.concepts.length})
                </h3>
                {knowledge.concepts.length === 0 ? (
                  <p className="text-xs text-gray-400 italic">No concepts extracted yet.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {knowledge.concepts.map((concept) => (
                      <div
                        key={concept.id}
                        className="bg-white border border-gray-200 rounded-xl p-4 hover:border-violet-300 transition-all shadow-2xs space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-semibold text-gray-900 text-sm line-clamp-1">{concept.name}</h4>
                          <span className="bg-violet-50 text-violet-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-violet-100 shrink-0">
                            Concept
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 leading-relaxed line-clamp-2">{concept.description}</p>
                        {concept.source_pages && concept.source_pages.length > 0 && (
                          <div className="flex items-center gap-1.5 text-[11px] text-gray-400 pt-1">
                            <Sparkles size={11} className="text-amber-500" />
                            <span>Pages: {concept.source_pages.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}


            {/* Sections List */}
            {(activeSubTab === 'all' || activeSubTab === 'sections') && (
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                  <BookOpen size={14} className="text-indigo-600" />
                  Document Sections ({knowledge.sections.length})
                </h3>
                {knowledge.sections.length === 0 ? (
                  <p className="text-xs text-gray-400 italic">No document sections extracted yet.</p>
                ) : (
                  <div className="space-y-2">
                    {knowledge.sections.map((sec) => (
                      <div
                        key={sec.id}
                        className="bg-gray-50/70 border border-gray-200 rounded-xl p-3 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-gray-400 font-semibold">#{sec.section_order}</span>
                          <span className="font-semibold text-gray-800">{sec.title}</span>
                        </div>
                        <span className="bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-md font-semibold border border-indigo-100">
                          Pages {sec.page_start} - {sec.page_end}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeSection;
