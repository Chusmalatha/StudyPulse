import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, HelpCircle, RefreshCw, Sparkles, Target, Layers, BookOpen, Zap, ArrowRight } from 'lucide-react';
import { getProjectGrowth, getProjectRecommendations, generateProjectRecommendations, completeRecommendation, dismissRecommendation } from '../../services/api/growthService';
import RecommendationCard from './RecommendationCard';

const GrowthSection = ({ projectId, onNavigateTab }) => {
  const [growthData, setGrowthData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recsLoading, setRecsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL');

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [gData, rData] = await Promise.all([
        getProjectGrowth(projectId),
        getProjectRecommendations(projectId)
      ]);
      setGrowthData(gData);
      setRecommendations(rData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load project growth & recommendations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchData();
    }
  }, [projectId]);

  const handleGenerateRecommendations = async () => {
    setRecsLoading(true);
    try {
      const updatedRecs = await generateProjectRecommendations(projectId);
      setRecommendations(updatedRecs);
    } catch (err) {
      console.error("Failed to generate recommendations:", err);
    } finally {
      setRecsLoading(false);
    }
  };

  const handleCompleteRec = async (recommendationId) => {
    try {
      const updated = await completeRecommendation(projectId, recommendationId);
      setRecommendations(prev => prev.map(r => r.id === recommendationId ? updated : r));
    } catch (err) {
      console.error("Failed to complete recommendation:", err);
    }
  };

  const handleDismissRec = async (recommendationId) => {
    try {
      await dismissRecommendation(projectId, recommendationId);
      setRecommendations(prev => prev.filter(r => r.id !== recommendationId));
    } catch (err) {
      console.error("Failed to dismiss recommendation:", err);
    }
  };

  const getCategoryConfig = (category) => {
    switch (category) {
      case 'IMPROVING':
        return {
          badge: (
            <span className="px-2.5 py-1 text-xs rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 font-semibold flex items-center gap-1">
              <TrendingUp size={11} /> Improving
            </span>
          ),
          border: 'border-emerald-500/20 hover:border-emerald-400/40',
          icon: <TrendingUp size={16} className="text-emerald-400" />,
          glow: 'shadow-emerald-500/5',
        };
      case 'REQUIRING_ATTENTION':
        return {
          badge: (
            <span className="px-2.5 py-1 text-xs rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/25 font-semibold flex items-center gap-1">
              <AlertTriangle size={11} /> Needs Attention
            </span>
          ),
          border: 'border-rose-500/20 hover:border-rose-400/40',
          icon: <AlertTriangle size={16} className="text-rose-400" />,
          glow: 'shadow-rose-500/5',
        };
      case 'STABLE':
        return {
          badge: (
            <span className="px-2.5 py-1 text-xs rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 font-semibold flex items-center gap-1">
              <CheckCircle size={11} /> Stable
            </span>
          ),
          border: 'border-indigo-500/20 hover:border-indigo-400/40',
          icon: <CheckCircle size={16} className="text-indigo-400" />,
          glow: 'shadow-indigo-500/5',
        };
      default:
        return {
          badge: (
            <span className="px-2.5 py-1 text-xs rounded-full bg-slate-700/60 text-slate-400 border border-slate-700 font-medium italic flex items-center gap-1">
              <HelpCircle size={11} /> Not Started
            </span>
          ),
          border: 'border-slate-800 hover:border-slate-600',
          icon: <HelpCircle size={16} className="text-slate-500" />,
          glow: '',
        };
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4">
        <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 text-sm">Analyzing concept trajectories & generating insights...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 flex justify-between items-center">
        <span>{error}</span>
        <button onClick={fetchData} className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium rounded-lg">
          Retry
        </button>
      </div>
    );
  }

  const activeRecommendations = recommendations.filter(r => r.status !== 'DISMISSED');

  const FILTERS = [
    { key: 'ALL', label: 'All' },
    { key: 'REQUIRING_ATTENTION', label: 'Needs Attention' },
    { key: 'IMPROVING', label: 'Improving' },
    { key: 'STABLE', label: 'Stable' },
    { key: 'INSUFFICIENT_EVIDENCE', label: 'Not Started' },
  ];

  const filteredSnapshots = (growthData?.snapshots || []).filter(s =>
    activeFilter === 'ALL' || s.category === activeFilter
  );

  const practicedCount = (growthData?.snapshots || []).filter(s => s.category !== 'INSUFFICIENT_EVIDENCE').length;
  const totalCount = growthData?.total_concepts || 0;
  const progressPct = totalCount > 0 ? Math.round((practicedCount / totalCount) * 100) : 0;

  return (
    <div className="space-y-8">

      {/* ── Header Banner ── */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-violet-950/30 to-slate-900 border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row justify-between items-start gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Zap size={18} className="text-violet-400" />
              <h2 className="text-xl font-bold text-white tracking-wide">Growth Analysis & Next Actions</h2>
            </div>
            <p className="text-sm text-slate-400">
              How your understanding of each concept evolves over time — based on quiz evidence.
            </p>

            {/* AI Narrative */}
            {growthData?.ai_narrative && (
              <div className="mt-4 p-4 rounded-xl bg-violet-950/30 border border-violet-500/20">
                <div className="flex items-start gap-2">
                  <Sparkles size={14} className="text-violet-400 mt-0.5 shrink-0" />
                  <p className="text-sm text-violet-100 leading-relaxed">{growthData.ai_narrative}</p>
                </div>
              </div>
            )}
          </div>

          {/* Stats Pills */}
          <div className="flex items-center gap-2 shrink-0 flex-wrap">
            <div className="flex items-center gap-3 bg-slate-950/70 px-4 py-3 rounded-xl border border-slate-800">
              <div className="text-center">
                <div className="text-[10px] text-emerald-400 uppercase tracking-wider font-bold">Improving</div>
                <div className="text-xl font-black text-emerald-300">{growthData?.improving_count || 0}</div>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <div className="text-[10px] text-rose-400 uppercase tracking-wider font-bold">Attention</div>
                <div className="text-xl font-black text-rose-300">{growthData?.requiring_attention_count || 0}</div>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Not Started</div>
                <div className="text-xl font-black text-slate-300">{growthData?.insufficient_evidence_count || 0}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Coverage progress bar */}
        <div className="mt-5">
          <div className="flex justify-between items-center mb-1.5 text-xs text-slate-400">
            <span>Concept Coverage</span>
            <span className="font-semibold text-white">{practicedCount} / {totalCount} tested</span>
          </div>
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-400 transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* ── Recommended Next Actions ── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles size={16} className="text-amber-400" />
              Recommended Next Actions
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Personalized, material-grounded steps to boost your mastery.</p>
          </div>
          <button
            onClick={handleGenerateRecommendations}
            disabled={recsLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <RefreshCw size={12} className={recsLoading ? 'animate-spin text-indigo-400' : ''} />
            Refresh
          </button>
        </div>

        {activeRecommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeRecommendations.map(rec => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onComplete={handleCompleteRec}
                onDismiss={handleDismissRec}
              />
            ))}
          </div>
        ) : (
          <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
            <Target size={28} className="mx-auto text-slate-600" />
            <p className="text-sm font-medium text-slate-300">No pending recommendations</p>
            <p className="text-xs text-slate-500">Complete quizzes or click Refresh to generate new recommendations.</p>
            {onNavigateTab && (
              <button
                onClick={() => onNavigateTab('quiz')}
                className="mx-auto mt-2 flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs font-semibold transition-all"
              >
                <BookOpen size={13} /> Take a Quiz
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Concept Growth Trajectories ── */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers size={16} className="text-violet-400" />
            Concept Growth Trajectories
            <span className="text-xs font-normal text-slate-400 ml-1">({totalCount} total)</span>
          </h3>

          {/* Filter chips */}
          <div className="flex flex-wrap gap-2">
            {FILTERS.map(f => (
              <button
                key={f.key}
                onClick={() => setActiveFilter(f.key)}
                className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                  activeFilter === f.key
                    ? 'bg-violet-600/30 border-violet-500/50 text-violet-200'
                    : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                {f.label}
                {f.key !== 'ALL' && (
                  <span className="ml-1 opacity-60">
                    ({(growthData?.snapshots || []).filter(s => s.category === f.key).length})
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSnapshots.map((snapshot) => {
            const config = getCategoryConfig(snapshot.category);
            const isUntested = snapshot.category === 'INSUFFICIENT_EVIDENCE';
            return (
              <div
                key={snapshot.concept_id}
                onClick={() => setSelectedSnapshot(snapshot)}
                className={`p-5 rounded-xl bg-slate-900/80 border transition-all cursor-pointer shadow-md ${config.border} ${config.glow}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {config.icon}
                      <h4 className="text-sm font-bold text-white truncate">{snapshot.concept_name}</h4>
                    </div>
                    <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-2">{snapshot.explanation}</p>
                  </div>
                  <div className="shrink-0">{config.badge}</div>
                </div>

                {/* Mastery bar */}
                {!isUntested && (
                  <div className="mt-3">
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          snapshot.current_mastery >= 75 ? 'bg-emerald-400' :
                          snapshot.current_mastery >= 45 ? 'bg-amber-400' : 'bg-rose-400'
                        }`}
                        style={{ width: `${Math.min(100, snapshot.current_mastery)}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                  <span>
                    {isUntested
                      ? <span className="italic text-slate-500">Not yet assessed — take a quiz</span>
                      : <span>Current: <strong className="text-white">{snapshot.current_mastery}%</strong></span>
                    }
                  </span>
                  {!isUntested && snapshot.change_percentage !== 0 && (
                    <span className={`font-mono font-bold flex items-center gap-1 ${snapshot.change_percentage >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {snapshot.change_percentage >= 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                      {snapshot.change_percentage >= 0 ? `+${snapshot.change_percentage}%` : `${snapshot.change_percentage}%`}
                    </span>
                  )}
                  {isUntested && onNavigateTab && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onNavigateTab('quiz'); }}
                      className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
                    >
                      Start <ArrowRight size={11} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {filteredSnapshots.length === 0 && (
          <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center text-slate-400">
            <HelpCircle size={24} className="mx-auto mb-2 text-slate-600" />
            <p className="text-sm">No concepts in this category yet.</p>
          </div>
        )}
      </div>

      {/* ── Concept Detail Modal ── */}
      {selectedSnapshot && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-slate-800 flex justify-between items-start bg-slate-950/50">
              <div>
                <h3 className="text-lg font-bold text-white">{selectedSnapshot.concept_name}</h3>
                <div className="mt-2">{getCategoryConfig(selectedSnapshot.category).badge}</div>
              </div>
              <button
                onClick={() => setSelectedSnapshot(null)}
                className="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800/50"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-5 text-xs text-slate-300">
              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
                <div>
                  <div className="text-slate-500 uppercase text-[10px] tracking-wider">Mastery</div>
                  <div className="text-xl font-bold text-indigo-400 mt-1">
                    {selectedSnapshot.category === 'INSUFFICIENT_EVIDENCE' ? '—' : `${selectedSnapshot.current_mastery}%`}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 uppercase text-[10px] tracking-wider">Previous</div>
                  <div className="text-xl font-bold text-slate-300 mt-1">
                    {selectedSnapshot.category === 'INSUFFICIENT_EVIDENCE' ? '—' : `${selectedSnapshot.previous_mastery}%`}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 uppercase text-[10px] tracking-wider">Evidence</div>
                  <div className="text-xl font-bold text-white mt-1">{selectedSnapshot.evidence_count}</div>
                </div>
              </div>

              {/* Change */}
              {selectedSnapshot.category !== 'INSUFFICIENT_EVIDENCE' && (
                <div className={`flex items-center justify-between p-3 rounded-lg border ${
                  selectedSnapshot.change_percentage >= 0
                    ? 'bg-emerald-950/30 border-emerald-500/20'
                    : 'bg-rose-950/30 border-rose-500/20'
                }`}>
                  <span className="text-slate-400">Score Change</span>
                  <span className={`font-mono font-bold text-base ${selectedSnapshot.change_percentage >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {selectedSnapshot.change_percentage >= 0 ? `+${selectedSnapshot.change_percentage}%` : `${selectedSnapshot.change_percentage}%`}
                  </span>
                </div>
              )}

              {/* Explanation */}
              <div>
                <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-[11px] mb-2">Analysis</h4>
                <p className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 text-slate-300 leading-relaxed">
                  {selectedSnapshot.explanation}
                </p>
              </div>

              {/* CTA */}
              {selectedSnapshot.category === 'INSUFFICIENT_EVIDENCE' && onNavigateTab && (
                <button
                  onClick={() => { setSelectedSnapshot(null); onNavigateTab('quiz'); }}
                  className="w-full py-2.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 font-semibold flex items-center justify-center gap-2 transition-all"
                >
                  <BookOpen size={14} /> Take a Quiz on {selectedSnapshot.concept_name}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GrowthSection;
