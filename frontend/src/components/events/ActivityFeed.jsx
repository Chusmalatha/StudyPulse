import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  FileText,
  HelpCircle,
  MessageSquare,
  TrendingUp,
  Sparkles,
  RefreshCw,
  Clock,
  Layers,
  Flame,
} from 'lucide-react';
import { getProjectEvents } from '../../services/api/eventsService';

const getEventBadge = (eventType) => {
  switch (eventType) {
    case 'MATERIAL_UPLOADED':
    case 'MATERIAL_PROCESSING_STARTED':
      return {
        icon: <FileText size={16} className="text-blue-500" />,
        bg: 'bg-blue-50 border-blue-100 text-blue-700',
        label: 'Material Upload',
      };
    case 'MATERIAL_PROCESSED':
      return {
        icon: <CheckCircle2 size={16} className="text-emerald-500" />,
        bg: 'bg-emerald-50 border-emerald-100 text-emerald-700',
        label: 'Material Ready',
      };
    case 'MATERIAL_PROCESSING_FAILED':
      return {
        icon: <AlertCircle size={16} className="text-red-500" />,
        bg: 'bg-red-50 border-red-100 text-red-700',
        label: 'Processing Failed',
      };
    case 'QUIZ_STARTED':
    case 'QUESTION_ANSWERED':
      return {
        icon: <HelpCircle size={16} className="text-amber-500" />,
        bg: 'bg-amber-50 border-amber-100 text-amber-700',
        label: 'Quiz Practice',
      };
    case 'QUIZ_COMPLETED':
      return {
        icon: <Sparkles size={16} className="text-purple-500" />,
        bg: 'bg-purple-50 border-purple-100 text-purple-700',
        label: 'Quiz Completed',
      };
    case 'MASTERY_UPDATED':
      return {
        icon: <TrendingUp size={16} className="text-rose-500" />,
        bg: 'bg-rose-50 border-rose-100 text-rose-700',
        label: 'Mastery Update',
      };
    case 'LEARNING_CONTEXT_UPDATED':
      return {
        icon: <Flame size={16} className="text-indigo-500" />,
        bg: 'bg-indigo-50 border-indigo-100 text-indigo-700',
        label: 'Learning Context',
      };
    case 'GROWTH_ANALYZED':
      return {
        icon: <Layers size={16} className="text-teal-500" />,
        bg: 'bg-teal-50 border-teal-100 text-teal-700',
        label: 'Growth Analysis',
      };
    case 'RECOMMENDATION_CREATED':
      return {
        icon: <Sparkles size={16} className="text-amber-500" />,
        bg: 'bg-amber-50 border-amber-100 text-amber-700',
        label: 'Next Step',
      };
    case 'TUTOR_INTERACTION':
      return {
        icon: <MessageSquare size={16} className="text-indigo-500" />,
        bg: 'bg-indigo-50 border-indigo-100 text-indigo-700',
        label: 'Tutor Chat',
      };
    default:
      return {
        icon: <Activity size={16} className="text-gray-500" />,
        bg: 'bg-gray-50 border-gray-100 text-gray-700',
        label: eventType.replace(/_/g, ' '),
      };
  }
};

const formatEventDescription = (event) => {
  const p = event.payload || {};
  switch (event.event_type) {
    case 'MATERIAL_UPLOADED':
      return `Uploaded PDF material: "${p.filename || 'Document'}"`;
    case 'MATERIAL_PROCESSING_STARTED':
      return `Started PDF processing pipeline (Attempt ${p.attempt || 1})`;
    case 'MATERIAL_PROCESSED':
      return `Successfully extracted and embedded ${p.chunks_count || 0} chunks from "${p.filename || 'Document'}"`;
    case 'MATERIAL_PROCESSING_FAILED':
      return `PDF processing error: ${p.error || 'Unknown error'}`;
    case 'QUIZ_STARTED':
      return `Started ${p.question_count || 5}-question adaptive practice assessment`;
    case 'QUESTION_ANSWERED':
      return `Answered ${p.question_type || ''} question (${p.is_correct ? 'Correct' : 'Needs Review'})`;
    case 'QUIZ_COMPLETED':
      return `Completed quiz with overall score: ${p.score_mcq != null ? `${p.score_mcq}%` : 'Evaluated'}`;
    case 'MASTERY_UPDATED':
      return `Updated concept mastery (${p.concepts_updated_count || 0} concepts affected)`;
    case 'LEARNING_CONTEXT_UPDATED':
      return `Recorded learning signals and mistake patterns in persistent context`;
    case 'GROWTH_ANALYZED':
      return `Generated growth analysis snapshot (Mastery: ${p.overall_mastery || 0}%)`;
    case 'RECOMMENDATION_CREATED':
      return `Created recommendation: "${p.recommendation_title || 'Study Next'}"`;
    case 'TUTOR_INTERACTION':
      return `Interacted with AI Tutor (${p.grounded ? 'Grounded' : 'General response'})`;
    default:
      return JSON.stringify(p);
  }
};

const ActivityFeed = ({ projectId }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProjectEvents(projectId, { limit: 20 });
      setEvents(data.events || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load activity stream.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Activity size={18} className="text-violet-600 animate-pulse" />
            Live Activity & Event Workflows
          </h3>
        </div>
        <div className="py-8 text-center text-xs text-gray-400">Loading activity feed...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Activity size={18} className="text-violet-600" />
            Live Activity & Learning Event Workflows
          </h3>
          <p className="text-xs text-gray-500">
            Real-time event stream powering background learning workflows & mastery updates
          </p>
        </div>
        <button
          onClick={fetchEvents}
          className="p-1.5 text-gray-400 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition-colors cursor-pointer"
          title="Refresh Activity Feed"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {error ? (
        <div className="p-3 bg-red-50 border border-red-100 rounded-lg text-xs text-red-600">{error}</div>
      ) : events.length === 0 ? (
        <div className="py-8 text-center text-xs text-gray-400 border border-dashed border-gray-200 rounded-lg">
          No learning activity recorded yet. Upload a material or take a quiz to trigger background events!
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
          {events.map((ev) => {
            const badge = getEventBadge(ev.event_type);
            return (
              <div
                key={ev.id}
                className="flex items-start gap-3 p-3 bg-gray-50/70 border border-gray-100 rounded-lg text-xs hover:border-violet-200 transition-colors"
              >
                <div className="p-2 bg-white rounded-lg border border-gray-100 shadow-2xs mt-0.5">
                  {badge.icon}
                </div>

                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badge.bg}`}>
                      {badge.label}
                    </span>
                    <span className="text-[10px] text-gray-400 flex items-center gap-1">
                      <Clock size={10} />
                      {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <p className="text-xs text-gray-800 font-medium leading-snug">
                    {formatEventDescription(ev)}
                  </p>

                  {ev.correlation_id && (
                    <div className="text-[10px] text-gray-400 font-mono truncate">
                      Correlation: {ev.correlation_id}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ActivityFeed;
