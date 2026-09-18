import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  RefreshCw,
  Sparkles,
  Target,
  Layers,
  BarChart3,
  Activity,
  MessageSquare,
  ArrowRight,
  Brain,
  Zap,
} from 'lucide-react';
import {
  getProjectGrowth,
  getProjectRecommendations,
  completeRecommendation,
  dismissRecommendation,
} from '../../services/api/growthService';
import { getProjectAnalytics } from '../../services/api/analyticsService';

const AnalyticsGrowthSection = ({ projectId, onNavigateTab }) => {
  const [growthData, setGrowthData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  const fetchData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const [growthRes, analyticsRes, recsRes] = await Promise.all([
        getProjectGrowth(projectId).catch(() => null),
        getProjectAnalytics(projectId).catch(() => null),
        getProjectRecommendations(projectId).catch(() => []),
      ]);

      setGrowthData(growthRes);
      setAnalyticsData(analyticsRes);
      setRecommendations(recsRes || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load growth & analytics data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchData();
    }
  }, [projectId, fetchData]);

  const handleCompleteRec = async (recId) => {
    try {
      await completeRecommendation(projectId, recId);
      setRecommendations((prev) => prev.filter((r) => r.recommendation_id !== recId));
    } catch (err) {
      console.error('Failed to complete recommendation:', err);
    }
  };

  const handleDismissRec = async (recId) => {
    try {
      await dismissRecommendation(projectId, recId);
      setRecommendations((prev) => prev.filter((r) => r.recommendation_id !== recId));
    } catch (err) {
      console.error('Failed to dismiss recommendation:', err);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center space-y-3 shadow-sm">
        <Sparkles size={32} className="animate-spin text-violet-600 mx-auto" />
        <p className="text-sm font-medium text-gray-600">Analyzing project growth & performance metrics...</p>
      </div>
    );
  }

  if (error && !growthData && !analyticsData) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex items-center justify-between">
        <span className="text-xs text-red-600 font-medium">{error}</span>
        <button
          onClick={() => fetchData()}
          className="text-xs font-semibold text-violet-600 hover:text-violet-700 bg-violet-50 px-3 py-1.5 rounded-lg border border-violet-100 transition-colors cursor-pointer"
        >
          Retry
        </button>
      </div>
    );
  }

  const concepts = growthData?.snapshots || [];
  const categories = ['ALL', ...new Set(concepts.map((c) => c.category || 'General').filter(Boolean))];

  const filteredConcepts =
    selectedCategory === 'ALL'
      ? concepts
      : concepts.filter((c) => (c.category || 'General') === selectedCategory);

  const testedCount = concepts.filter((c) => c.evidence_count > 0).length;
  const totalCount = concepts.length;
  const coveragePct = totalCount > 0 ? Math.round((testedCount / totalCount) * 100) : 0;

  const { learning_activity, quiz_performance, mastery, ai_activity } = analyticsData || {
    learning_activity: { total_events: 0, activity_this_week: 0, time_series: [] },
    quiz_performance: { accuracy_percentage: 0, assessments_completed: 0, trend: [] },
    mastery: { average_mastery: 0, total_concepts_tracked: totalCount },
    ai_activity: { tutor_requests: 0, total_ai_operations: 0 },
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: AI Growth Narrative */}
      <div className="bg-gradient-to-r from-violet-900 via-indigo-900 to-slate-900 text-white rounded-xl p-6 shadow-md border border-violet-800/50 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-violet-600/30 border border-violet-400/30 rounded-xl text-violet-300 shrink-0">
              <Sparkles size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold tracking-tight">AI Growth & Analytics Insights</h2>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Live Analysis
                </span>
              </div>
              <p className="text-xs text-violet-200/80 mt-0.5">
                Real-time tracking of mastery trajectories and personalized recommendations.
              </p>
            </div>
          </div>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="self-start sm:self-center flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-lg border border-white/10 transition-colors cursor-pointer"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Refresh Insights'}
          </button>
        </div>

        {/* Narrative Paragraph */}
        {growthData?.ai_narrative && (
          <div className="bg-white/10 backdrop-blur-xs border border-white/15 rounded-lg p-3.5 text-xs leading-relaxed text-violet-100 font-medium">
            "{growthData.ai_narrative}"
          </div>
        )}

        {/* Coverage Progress Bar */}
        <div className="space-y-1.5 pt-1">
          <div className="flex justify-between items-center text-xs font-semibold text-violet-200">
            <span>Concept Evaluation Progress</span>
            <span>
              {testedCount} / {totalCount} Concepts Assessed ({coveragePct}%)
            </span>
          </div>
          <div className="h-2 bg-slate-800/80 rounded-full overflow-hidden border border-white/10">
            <div
              className="h-full bg-gradient-to-r from-violet-400 to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${coveragePct}%` }}
            />
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Mastery</span>
            <div className="p-2 bg-violet-50 text-violet-600 rounded-lg">
              <TrendingUp size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-gray-900">{mastery?.average_mastery || 0}%</div>
          <p className="text-[11px] text-gray-500">{totalCount} total concepts tracked</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Quiz Accuracy</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <HelpCircle size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-emerald-600">{quiz_performance?.accuracy_percentage || 0}%</div>
          <p className="text-[11px] text-gray-500">{quiz_performance?.assessments_completed || 0} quizzes completed</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Events</span>
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <Activity size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-gray-900">{learning_activity?.total_events || 0}</div>
          <p className="text-[11px] text-gray-500">{learning_activity?.activity_this_week || 0} events this week</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Tutor Sessions</span>
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <MessageSquare size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-indigo-600">{ai_activity?.tutor_requests || 0}</div>
          <p className="text-[11px] text-gray-500">{ai_activity?.total_ai_operations || 0} total AI operations</p>
        </div>
      </div>

      {/* AI Recommendations Banner (if any) */}
      {recommendations.length > 0 && (
        <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-5 shadow-xs space-y-3">
          <h3 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
            <Zap size={14} className="text-amber-600 fill-amber-600" />
            Recommended Action Plan ({recommendations.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recommendations.slice(0, 2).map((rec) => (
              <div key={rec.recommendation_id} className="bg-white border border-amber-200/80 rounded-lg p-3.5 flex flex-col justify-between gap-3 shadow-2xs">
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-900">{rec.title}</span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                      {rec.type || 'Action'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 leading-relaxed">{rec.description}</p>
                </div>
                <div className="flex items-center justify-between border-t border-gray-100 pt-2 text-xs">
                  <button
                    onClick={() => {
                      if (onNavigateTab) {
                        onNavigateTab(rec.target_action === 'CHAT' ? 'tutor' : 'quiz');
                      }
                    }}
                    className="font-semibold text-violet-600 hover:text-violet-700 flex items-center gap-1 cursor-pointer"
                  >
                    Start Now <ArrowRight size={12} />
                  </button>
                  <button
                    onClick={() => handleDismissRec(rec.recommendation_id)}
                    className="text-[11px] text-gray-400 hover:text-gray-600 cursor-pointer"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category Filter Chips & Concept Mastery Grid */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-3">
          <div>
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Layers size={18} className="text-violet-600" />
              Concept Mastery & Growth Cards
            </h3>
            <p className="text-xs text-gray-500">
              Track mastery percentages and status trends extracted from your uploaded materials.
            </p>
          </div>

          {/* Category Chips */}
          {categories.length > 1 && (
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`text-xs font-semibold px-3 py-1 rounded-full border transition-colors cursor-pointer whitespace-nowrap ${
                    selectedCategory === cat
                      ? 'bg-violet-600 text-white border-violet-600 shadow-2xs'
                      : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Concept Cards Grid */}
        {filteredConcepts.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-xs text-gray-400">
            No concepts match the selected category.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredConcepts.map((c) => {
              const score = Math.round(c.current_mastery || 0);
              const attempts = c.evidence_count || 0;
              const isUntested = attempts === 0 || c.category === 'INSUFFICIENT_EVIDENCE';

              const isImproving = c.category === 'IMPROVING';
              const isAttention = c.category === 'REQUIRING_ATTENTION';
              const isStable = c.category === 'STABLE';

              return (
                <div
                  key={c.concept_id}
                  className={`bg-white rounded-xl border p-4 shadow-xs transition-all space-y-3 ${
                    isAttention
                      ? 'border-red-200 hover:border-red-300 bg-red-50/20'
                      : isImproving
                      ? 'border-emerald-200 hover:border-emerald-300'
                      : 'border-gray-200 hover:border-violet-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-0.5">
                      <h4 className="font-bold text-gray-900 text-sm line-clamp-1">{c.concept_name}</h4>
                      <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">
                        {c.category || 'General'}
                      </span>
                    </div>

                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${
                        isUntested
                          ? 'bg-gray-100 text-gray-600 border-gray-200'
                          : isAttention
                          ? 'bg-red-50 text-red-700 border-red-200'
                          : isImproving
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-blue-50 text-blue-700 border-blue-200'
                      }`}
                    >
                      {isUntested
                        ? 'Not Started'
                        : isAttention
                        ? 'Needs Focus'
                        : isImproving
                        ? 'Improving ↑'
                        : 'Stable'}
                    </span>
                  </div>

                  {/* Progress Bar & Score */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500 font-medium">Mastery Score</span>
                      <span className="font-bold text-gray-900">{isUntested ? '—' : `${score}%`}</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isUntested
                            ? 'bg-gray-200'
                            : score >= 75
                            ? 'bg-emerald-500'
                            : score >= 45
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${isUntested ? 0 : score}%` }}
                      />
                    </div>
                  </div>

                  {/* Footer Meta & Action */}
                  <div className="flex items-center justify-between pt-2 border-t border-gray-100 text-xs">
                    <span className="text-gray-400 text-[11px]">
                      {attempts > 0 ? `${attempts} test attempts` : 'No test evidence yet'}
                    </span>
                    <button
                      onClick={() => onNavigateTab && onNavigateTab('quiz', c.concept_id, c.concept_name)}
                      className="font-semibold text-violet-600 hover:text-violet-700 flex items-center gap-1 cursor-pointer"
                    >
                      {isUntested ? 'Test Now' : 'Practice'} <ArrowRight size={12} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Visual Activity & Quiz Trajectory Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* Activity Chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Activity size={16} className="text-blue-600" />
            Learning Activity (Last 14 Days)
          </h3>

          {learning_activity.time_series.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-400">No activity recorded yet.</div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-end gap-1.5 h-32 pt-4 border-b border-gray-100">
                {learning_activity.time_series.map((pt) => {
                  const maxCount = Math.max(...learning_activity.time_series.map((t) => t.count), 1);
                  const heightPct = Math.round((pt.count / maxCount) * 100);
                  return (
                    <div key={pt.date} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
                      <div
                        style={{ height: `${Math.max(heightPct, 8)}%` }}
                        className={`w-full max-w-[18px] rounded-t-sm transition-all ${
                          pt.count > 0 ? 'bg-violet-600 group-hover:bg-violet-700' : 'bg-gray-100'
                        }`}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500 pt-1">
                <span>Today: <strong>{learning_activity.activity_today || 0} events</strong></span>
                <span>This Month: <strong>{learning_activity.activity_this_month || 0} events</strong></span>
              </div>
            </div>
          )}
        </div>

        {/* Quiz Performance History */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <HelpCircle size={16} className="text-emerald-600" />
            Quiz Score History
          </h3>

          {quiz_performance.trend.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-400 border border-dashed border-gray-200 rounded-lg">
              No completed practice quizzes yet. Take a quiz to track accuracy!
            </div>
          ) : (
            <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
              {quiz_performance.trend.map((pt, idx) => (
                <div key={pt.assessment_id || idx} className="flex items-center justify-between p-3 bg-gray-50/80 border border-gray-100 rounded-lg text-xs">
                  <div className="space-y-0.5">
                    <p className="font-bold text-gray-900">{pt.title}</p>
                    <p className="text-[10px] text-gray-400">{new Date(pt.completed_at).toLocaleDateString()}</p>
                  </div>
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                    {pt.score_mcq != null ? `${pt.score_mcq}% Score` : 'Evaluated'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsGrowthSection;
