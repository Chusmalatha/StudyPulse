import React, { useState } from 'react';
import { BookOpen, HelpCircle, CheckCircle2, XCircle, ArrowRight, Lightbulb, Sparkles, MessageSquare } from 'lucide-react';

const RecommendationCard = ({ recommendation, onComplete, onDismiss, onNavigateAction }) => {
  const [loading, setLoading] = useState(false);

  const handleComplete = async () => {
    setLoading(true);
    try {
      await onComplete(recommendation.id);
    } catch (err) {
      console.error("Failed to complete recommendation:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = async () => {
    setLoading(true);
    try {
      await onDismiss(recommendation.id);
    } catch (err) {
      console.error("Failed to dismiss recommendation:", err);
    } finally {
      setLoading(false);
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'REVIEW_MATERIAL':
        return <BookOpen size={18} className="text-violet-400" />;
      case 'PRACTICE_QUIZ':
      case 'PRACTICE_OPEN_ENDED':
        return <HelpCircle size={18} className="text-amber-400" />;
      case 'REVISIT_TUTOR':
        return <MessageSquare size={18} className="text-indigo-400" />;
      default:
        return <Lightbulb size={18} className="text-emerald-400" />;
    }
  };

  const isCompleted = recommendation.status === 'COMPLETED';

  return (
    <div className={`p-5 rounded-xl border transition-all shadow-md flex flex-col justify-between space-y-4 ${
      isCompleted 
        ? 'bg-slate-900/40 border-slate-800/60 opacity-75' 
        : 'bg-slate-900/90 border-slate-800 hover:border-violet-500/40'
    }`}>
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50">
              {getTypeIcon(recommendation.type)}
            </div>
            <div>
              <h4 className="text-sm font-bold text-white line-clamp-1">{recommendation.title}</h4>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20">
                {recommendation.priority} PRIORITY
              </span>
            </div>
          </div>
          {isCompleted && (
            <span className="flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
              <CheckCircle2 size={13} />
              Completed
            </span>
          )}
        </div>

        <p className="text-xs text-slate-300 mt-3 leading-relaxed">
          {recommendation.description}
        </p>

        {/* Reason / Why this? */}
        <div className="mt-3 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Sparkles size={13} className="text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-300 font-semibold">Why this? </strong>
            <span>{recommendation.reason}</span>
          </div>
        </div>

        {/* Grounded Material References */}
        {recommendation.material_references?.length > 0 && (
          <div className="mt-3 space-y-1">
            <span className="text-[11px] text-slate-400 font-semibold">Grounded PDF References:</span>
            {recommendation.material_references.map((ref, idx) => (
              <div key={idx} className="text-xs text-indigo-300 bg-indigo-950/30 border border-indigo-500/20 px-2.5 py-1 rounded-lg flex items-center justify-between">
                <span className="truncate">{ref.filename}</span>
                <span className="font-mono font-bold text-[11px] text-indigo-200">Page {ref.page_number}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        <div className="text-xs text-slate-400 font-medium">
          {recommendation.action}
        </div>
        {!isCompleted && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleDismiss}
              disabled={loading}
              className="text-xs text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/10 transition-colors"
              title="Dismiss recommendation"
            >
              <XCircle size={16} />
            </button>
            <button
              onClick={handleComplete}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white shadow-xs transition-colors cursor-pointer"
            >
              <CheckCircle2 size={14} />
              Mark Complete
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationCard;
