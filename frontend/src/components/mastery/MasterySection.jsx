import React, { useState, useEffect } from 'react';
import { getProjectMastery, getConceptMasteryDetail } from '../../services/api/masteryService';
import knowledgeService from '../../services/api/knowledgeService';

const MasterySection = ({ projectId }) => {
  const [masteryData, setMasteryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [conceptDetail, setConceptDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState(null);

  const fetchMastery = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getProjectMastery(projectId);
      setMasteryData(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load project mastery summary.');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncFromPDF = async () => {
    try {
      setSyncing(true);
      setSyncMsg(null);
      await knowledgeService.extractProjectKnowledge(projectId);
      setSyncMsg('✓ Concepts re-extracted from PDF successfully!');
      await fetchMastery();
    } catch (err) {
      setSyncMsg('✗ ' + (err.response?.data?.detail || 'Sync failed. Please try again.'));
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMsg(null), 4000);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchMastery();
    }
  }, [projectId]);

  const handleInspectConcept = async (concept) => {
    setSelectedConcept(concept);
    setDetailLoading(true);
    try {
      const data = await getConceptMasteryDetail(projectId, concept.concept_id);
      setConceptDetail(data);
    } catch (err) {
      console.error("Failed to fetch concept detail:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const getScoreColor = (score, attempts) => {
    if (attempts === 0) return 'text-slate-400 bg-slate-800/50 border-slate-700/50';
    if (score >= 75) return 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30';
    if (score >= 45) return 'text-amber-400 bg-amber-950/40 border-amber-500/30';
    return 'text-rose-400 bg-rose-950/40 border-rose-500/30';
  };

  const getConfidenceBadge = (confidence) => {
    const pct = Math.round(confidence * 100);
    if (pct >= 70) return <span className="px-2 py-0.5 text-xs rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">High Confidence ({pct}%)</span>;
    if (pct >= 40) return <span className="px-2 py-0.5 text-xs rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Medium Confidence ({pct}%)</span>;
    return <span className="px-2 py-0.5 text-xs rounded bg-slate-500/10 text-slate-400 border border-slate-500/20">Low Confidence ({pct}%)</span>;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 text-sm">Evaluating learning evidence & concept mastery...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 flex justify-between items-center">
        <span>{error}</span>
        <button onClick={fetchMastery} className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium rounded-lg">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Summary Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Concept Mastery Tracker</h2>
          <p className="text-sm text-slate-400 mt-1">
            Evidence-based mastery scores updated automatically from quiz and assessment attempts.
          </p>
          {syncMsg && (
            <p className={`text-xs mt-2 font-medium ${syncMsg.startsWith('✓') ? 'text-emerald-400' : 'text-rose-400'}`}>
              {syncMsg}
            </p>
          )}
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          {/* Sync from PDF button */}
          <button
            onClick={handleSyncFromPDF}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 hover:text-indigo-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing ? (
              <><span className="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin inline-block"></span> Syncing PDF…</>
            ) : (
              <>📄 Sync from PDF</>
            )}
          </button>
          {/* Stats */}
          <div className="flex items-center space-x-6 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="text-center">
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Overall Mastery</div>
              <div className="text-2xl font-black text-indigo-400 mt-0.5">
                {masteryData?.practiced_concepts > 0 ? `${masteryData.overall_mastery}%` : '0%'}
              </div>
            </div>
            <div className="h-8 w-px bg-slate-800"></div>
            <div className="text-center">
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Practiced</div>
              <div className="text-2xl font-black text-emerald-400 mt-0.5">
                {masteryData?.practiced_concepts || 0} / {masteryData?.total_concepts || 0}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Concept Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {masteryData?.concepts?.map((c) => (
          <div
            key={c.concept_id}
            onClick={() => handleInspectConcept(c)}
            className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 transition-all cursor-pointer group shadow-md flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0 pr-3">
                  <h3 className="text-base font-semibold text-white group-hover:text-indigo-400 transition-colors">
                    {c.name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">{c.description}</p>
                </div>
                <div className={`flex-shrink-0 px-3 py-1.5 rounded-xl text-lg font-bold border ${getScoreColor(c.mastery_score, c.attempts)}`}>
                  {c.attempts === 0 ? '—' : `${Math.round(c.mastery_score)}%`}
                </div>
              </div>
              {/* Mastery progress bar */}
              {c.attempts > 0 && (
                <div className="mt-3">
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        c.mastery_score >= 75 ? 'bg-emerald-400' :
                        c.mastery_score >= 45 ? 'bg-amber-400' : 'bg-rose-400'
                      }`}
                      style={{ width: `${Math.min(100, c.mastery_score)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
              <div>
                {c.attempts === 0 ? (
                  <span className="text-xs text-slate-500 italic">Take a quiz to start tracking</span>
                ) : (
                  getConfidenceBadge(c.confidence)
                )}
              </div>
              <div className="text-xs text-slate-400">
                {c.attempts > 0 ? (
                  <span>{c.correct} correct / {c.attempts} attempts</span>
                ) : (
                  <span>0 attempts</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Concept Detail Modal */}
      {selectedConcept && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-slate-800 flex justify-between items-start bg-slate-950/50">
              <div>
                <h3 className="text-xl font-bold text-white">{selectedConcept.name}</h3>
                <p className="text-sm text-slate-400 mt-1">{selectedConcept.description}</p>
              </div>
              <button
                onClick={() => { setSelectedConcept(null); setConceptDetail(null); }}
                className="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800/50"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
              {detailLoading ? (
                <div className="text-center py-8 text-slate-400">Loading audit history & details...</div>
              ) : (
                <>
                  {/* Summary Metrics */}
                  <div className="grid grid-cols-3 gap-3 p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
                    <div>
                      <div className="text-xs text-slate-500 uppercase">Mastery Score</div>
                      <div className="text-xl font-bold text-indigo-400 mt-1">
                        {selectedConcept.attempts === 0 ? 'No evidence' : `${selectedConcept.mastery_score}%`}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase">Confidence</div>
                      <div className="text-xl font-bold text-emerald-400 mt-1">
                        {Math.round((conceptDetail?.confidence || selectedConcept.confidence) * 100)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase">Attempts</div>
                      <div className="text-xl font-bold text-white mt-1">
                        {selectedConcept.attempts}
                      </div>
                    </div>
                  </div>

                  {/* Repeated Mistakes */}
                  {conceptDetail?.repeated_mistakes?.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2">
                        Tracked Mistakes ({conceptDetail.repeated_mistakes.length})
                      </h4>
                      <div className="space-y-2">
                        {conceptDetail.repeated_mistakes.map((m) => (
                          <div key={m.id} className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/20 text-xs text-rose-200 flex justify-between items-center">
                            <span>{m.mistake_description}</span>
                            <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono font-bold">
                              x{m.occurrence_count}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Audit Event History */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                      Recent Evidence & Mastery Updates
                    </h4>
                    {conceptDetail?.recent_events?.length > 0 ? (
                      <div className="space-y-2">
                        {conceptDetail.recent_events.map((evt) => (
                          <div key={evt.id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                            <div className="flex justify-between items-center">
                              <span className="font-semibold text-indigo-300">[{evt.evidence_type}] {evt.reason}</span>
                              <span className="font-mono text-slate-400">
                                {evt.previous_score}% → <strong className="text-white">{evt.new_score}%</strong>
                              </span>
                            </div>
                            <div className="text-[10px] text-slate-500">
                              {new Date(evt.created_at).toLocaleString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">No attempt audit logs recorded yet.</p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterySection;
