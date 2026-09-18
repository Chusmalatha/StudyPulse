import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Mail,
  ShieldCheck,
  Folders,
  Folder,
  HelpCircle,
  TrendingUp,
  Activity,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';
import { getGlobalAnalytics } from '../services/api/analyticsService';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    getGlobalAnalytics()
      .then((data) => {
        if (isMounted) setAnalytics(data);
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const isAdmin = user?.role === 'admin';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-8">
      {/* STUDENT PROFILE HERO BANNER */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-indigo-800 to-slate-900 rounded-3xl p-5 sm:p-8 text-white shadow-xl border border-indigo-700/40">
        {/* Background Ambient Glows */}
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-72 h-72 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-10 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          {/* Header Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-500 text-white flex items-center justify-center font-black text-lg uppercase shadow-md ring-4 ring-white/10 shrink-0">
                {user?.name?.charAt(0) || 'S'}
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                    Welcome back, {user?.name}! 👋
                  </h1>
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 text-[10px] font-extrabold uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Active Learner
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-indigo-100/80 mt-0.5 font-medium">
                  Your personalized AI Study Companion learning dashboard & progress portal.
                </p>
              </div>
            </div>

            {isAdmin && (
              <button
                onClick={() => navigate('/admin')}
                className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-extrabold px-4 py-2.5 rounded-xl shadow-md transition-all cursor-pointer self-start sm:self-auto border border-indigo-400/30"
              >
                <ShieldCheck size={16} />
                <span>Open Admin Portal</span>
                <ArrowRight size={14} />
              </button>
            )}
          </div>

          {/* USER IDENTITY GLASS CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-indigo-700/40">
            {/* Name Card */}
            <div className="flex items-center gap-3 p-3.5 sm:p-4 bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl">
              <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-200 border border-indigo-400/20 shrink-0">
                <User size={18} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] text-indigo-200 uppercase font-bold tracking-wider">Learner Name</p>
                <p className="text-xs sm:text-sm font-bold text-white truncate">{user?.name}</p>
              </div>
            </div>

            {/* Email Card */}
            <div className="flex items-center gap-3 p-3.5 sm:p-4 bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl">
              <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-200 border border-indigo-400/20 shrink-0">
                <Mail size={18} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] text-indigo-200 uppercase font-bold tracking-wider">Account Email</p>
                <p className="text-xs sm:text-sm font-bold text-white truncate">{user?.email}</p>
              </div>
            </div>

            {/* Role Card */}
            <div className="flex items-center gap-3 p-3.5 sm:p-4 bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl">
              <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-200 border border-indigo-400/20 shrink-0">
                <ShieldCheck size={18} />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] text-indigo-200 uppercase font-bold tracking-wider">Account Privilege</p>
                <p className="text-xs sm:text-sm font-bold text-white capitalize">{user?.role || 'Student'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* GLOBAL LEARNING OVERVIEW METRICS */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xs font-extrabold text-gray-500 uppercase tracking-wider">
            Global Learning Overview
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Spaces */}
          <div
            onClick={() => navigate('/spaces')}
            className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:border-indigo-300 hover:-translate-y-0.5 transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div>
              <div className="mb-3 p-2.5 bg-indigo-50 text-indigo-600 rounded-xl w-fit group-hover:bg-indigo-600 group-hover:text-white transition-colors shadow-2xs">
                <Folders size={22} />
              </div>
              <div className="flex items-center justify-between">
                <p className="font-bold text-gray-900 text-sm group-hover:text-indigo-600 transition-colors">Study Spaces</p>
                <span className="text-xl font-black text-indigo-600">
                  {loading ? '...' : analytics?.total_spaces ?? 0}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">Subject areas & course organization.</p>
            </div>
          </div>

          {/* Card 2: Projects */}
          <div
            onClick={() => navigate('/projects')}
            className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:border-violet-300 hover:-translate-y-0.5 transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div>
              <div className="mb-3 p-2.5 bg-violet-50 text-violet-600 rounded-xl w-fit group-hover:bg-violet-600 group-hover:text-white transition-colors shadow-2xs">
                <Folder size={22} />
              </div>
              <div className="flex items-center justify-between">
                <p className="font-bold text-gray-900 text-sm group-hover:text-violet-600 transition-colors">Project Workspaces</p>
                <span className="text-xl font-black text-violet-600">
                  {loading ? '...' : analytics?.total_projects ?? 0}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                {analytics?.active_projects_count ? `${analytics.active_projects_count} active in 30 days` : 'Targeted study workspaces.'}
              </p>
            </div>
          </div>

          {/* Card 3: Quiz Accuracy */}
          <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl w-fit shadow-2xs">
                <HelpCircle size={22} />
              </div>
              <span className="text-xl font-black text-emerald-600">
                {loading ? '...' : `${analytics?.overall_accuracy_percentage ?? 0}%`}
              </span>
            </div>
            <div>
              <p className="font-bold text-gray-900 text-sm">Quiz Accuracy</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {analytics?.assessments_completed ?? 0} quizzes ({analytics?.questions_attempted ?? 0} questions)
              </p>
            </div>
          </div>

          {/* Card 4: Overall Mastery */}
          <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-rose-50 text-rose-600 rounded-xl w-fit shadow-2xs">
                <TrendingUp size={22} />
              </div>
              <span className="text-xl font-black text-rose-600">
                {loading ? '...' : `${analytics?.overall_average_mastery ?? 0}%`}
              </span>
            </div>
            <div>
              <p className="font-bold text-gray-900 text-sm">Overall Mastery</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {analytics?.concepts_requiring_attention_count
                  ? `${analytics.concepts_requiring_attention_count} concepts require review`
                  : 'Calculated from learning evidence'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ACTIVE WORKSPACES SUMMARY */}
      {analytics?.active_projects && analytics.active_projects.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200/90 p-5 sm:p-6 shadow-2xs space-y-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Activity size={16} className="text-violet-600" />
            Active Learning Workspaces
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {analytics.active_projects.map((p) => (
              <div
                key={p.project_id}
                onClick={() => navigate('/projects')}
                className="p-4 bg-gray-50/70 border border-gray-100 rounded-2xl hover:border-violet-300 transition-all cursor-pointer space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold text-violet-700 bg-violet-50 px-2.5 py-0.5 rounded-full border border-violet-100 uppercase">
                    {p.space_name}
                  </span>
                  <span className="text-[10px] text-gray-400 font-semibold">
                    {p.total_events} events
                  </span>
                </div>
                <h4 className="font-bold text-gray-900 text-sm truncate group-hover:text-violet-600 transition-colors">
                  {p.project_name}
                </h4>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
