import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  TrendingUp,
  Activity,
  HelpCircle,
  MessageSquare,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Brain,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { getProjectAnalytics } from '../../services/api/analyticsService';

const ProjectAnalyticsSection = ({ projectId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProjectAnalytics(projectId);
      setData(res);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load project analytics.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 space-y-3 shadow-sm">
        <BarChart3 size={32} className="animate-bounce text-violet-600 mx-auto" />
        <p className="text-sm font-medium">Calculating project learning analytics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-3">
        <div className="p-3 bg-red-50 text-red-600 rounded-lg text-xs font-medium">{error || 'Analytics unavailable.'}</div>
        <button
          onClick={fetchAnalytics}
          className="text-xs font-semibold text-violet-600 hover:text-violet-700 bg-violet-50 px-3 py-1.5 rounded-lg border border-violet-100 transition-colors cursor-pointer"
        >
          Retry
        </button>
      </div>
    );
  }

  const { learning_activity, quiz_performance, mastery, ai_activity } = data;

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 size={20} className="text-violet-600" />
            Project Learning Analytics
          </h2>
          <p className="text-xs text-gray-500">Real-time performance metrics, concept trends, and AI activity</p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="p-2 text-gray-400 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition-colors cursor-pointer"
          title="Refresh Analytics"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Events</span>
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <Activity size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-gray-900">{learning_activity.total_events}</div>
          <p className="text-[11px] text-gray-500">{learning_activity.activity_this_week} events this week</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Quiz Accuracy</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <HelpCircle size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-emerald-600">{quiz_performance.accuracy_percentage}%</div>
          <p className="text-[11px] text-gray-500">{quiz_performance.assessments_completed} assessments completed</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Mastery</span>
            <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
              <TrendingUp size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-rose-600">{mastery.average_mastery}%</div>
          <p className="text-[11px] text-gray-500">{mastery.total_concepts_tracked} concepts tracked</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Tutor Chats</span>
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <MessageSquare size={18} />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-indigo-600">{ai_activity.tutor_requests}</div>
          <p className="text-[11px] text-gray-500">{ai_activity.total_ai_operations} total AI operations</p>
        </div>
      </div>

      {/* Main Grid: Learning Activity & Quiz Performance Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Learning Activity Time-Series */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Activity size={16} className="text-blue-600" />
            Learning Activity (Last 14 Days)
          </h3>
          {learning_activity.time_series.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-400">No recent learning activity recorded.</div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-end gap-1.5 h-36 pt-4 border-b border-gray-100">
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
                      <span className="text-[9px] text-gray-400 rotate-45 origin-left hidden sm:inline-block">
                        {pt.date.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500 pt-1">
                <span>Today: <strong>{learning_activity.activity_today}</strong></span>
                <span>This Month: <strong>{learning_activity.activity_this_month}</strong></span>
              </div>
            </div>
          )}
        </div>

        {/* Quiz Performance Trend */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <HelpCircle size={16} className="text-emerald-600" />
            Quiz Performance Trajectory
          </h3>

          {quiz_performance.trend.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-400 border border-dashed border-gray-200 rounded-lg">
              No completed practice assessments yet. Take a quiz to view score trajectories!
            </div>
          ) : (
            <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
              {quiz_performance.trend.map((pt, idx) => (
                <div key={pt.assessment_id || idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-xs">
                  <div className="space-y-0.5">
                    <p className="font-semibold text-gray-900">{pt.title}</p>
                    <p className="text-[10px] text-gray-400">{new Date(pt.completed_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                      {pt.score_mcq != null ? `${pt.score_mcq}%` : 'Evaluated'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Concept Mastery Trends & AI Operations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Concept Growth Trends Table */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <TrendingUp size={16} className="text-rose-600" />
            Concept Mastery & Growth Trajectory
          </h3>

          {mastery.concept_trends.length === 0 ? (
            <div className="py-8 text-center text-xs text-gray-400 border border-dashed border-gray-200 rounded-lg">
              No concept mastery evidence recorded yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-400 uppercase text-[10px]">
                    <th className="pb-2 font-semibold">Concept Name</th>
                    <th className="pb-2 font-semibold">Mastery</th>
                    <th className="pb-2 font-semibold">Growth Category</th>
                    <th className="pb-2 font-semibold">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {mastery.concept_trends.map((c) => (
                    <tr key={c.concept_id} className="hover:bg-gray-50/50">
                      <td className="py-2.5 font-medium text-gray-900">{c.concept_name}</td>
                      <td className="py-2.5 font-bold text-violet-700">{c.current_mastery}%</td>
                      <td className="py-2.5">
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                            c.status_label === 'IMPROVING'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : c.status_label === 'REQUIRING_ATTENTION'
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-gray-50 text-gray-700 border-gray-200'
                          }`}
                        >
                          {c.status_label.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-2.5 text-gray-500">{c.evidence_count} attempts</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* AI Operations Summary */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Sparkles size={16} className="text-indigo-600" />
            Project AI Usage Breakdown
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Tutor Messages</span>
              <span className="font-bold text-gray-900">{ai_activity.tutor_requests}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Quiz Generations</span>
              <span className="font-bold text-gray-900">{ai_activity.quiz_generations}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Open-Ended Evaluations</span>
              <span className="font-bold text-gray-900">{ai_activity.open_ended_evaluations}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600 font-medium">Extracted Concepts</span>
              <span className="font-bold text-gray-900">{ai_activity.knowledge_extractions}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectAnalyticsSection;
