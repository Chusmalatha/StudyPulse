import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import UserHeaderMenu from '../components/layout/UserHeaderMenu';
import {
  ShieldCheck,
  Users,
  Folder,
  Activity,
  Cpu,
  Sparkles,
  Server,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Search,
  Eye,
  X,
  FileText,
  HelpCircle,
  TrendingUp,
  BookOpen,
  ArrowUpRight,
  Layers,
  Zap,
} from 'lucide-react';
import {
  getAdminOverview,
  getAdminUsers,
  getAdminUserJourney,
  getAdminActivity,
  getAdminEngagement,
  getAdminAIUsage,
  getAdminAIEvaluation,
  getAdminJobs,
  getAdminSystemHealth,
} from '../services/api/adminService';

const Admin = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tab Data States
  const [usersData, setUsersData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [engagementData, setEngagementData] = useState(null);
  const [aiUsageData, setAiUsageData] = useState(null);
  const [aiEvalData, setAiEvalData] = useState(null);
  const [jobsData, setJobsData] = useState(null);
  const [healthData, setHealthData] = useState(null);

  // User Journey Modal State
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [userJourney, setUserJourney] = useState(null);
  const [journeyLoading, setJourneyLoading] = useState(false);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAdminOverview();
      setOverview(data);
    } catch (err) {
      if (err.response?.status === 403) {
        setError('403 Forbidden: Admin privileges required to view Admin Dashboard.');
      } else {
        setError(err.response?.data?.detail || 'Failed to load Admin Dashboard overview.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  // Tab Specific Loaders
  useEffect(() => {
    if (activeTab === 'users') {
      getAdminUsers().then(setUsersData).catch(() => {});
    } else if (activeTab === 'activity') {
      getAdminActivity().then(setActivityData).catch(() => {});
    } else if (activeTab === 'engagement') {
      getAdminEngagement().then(setEngagementData).catch(() => {});
    } else if (activeTab === 'ai-usage') {
      getAdminAIUsage().then(setAiUsageData).catch(() => {});
      getAdminAIEvaluation().then(setAiEvalData).catch(() => {});
    } else if (activeTab === 'jobs') {
      getAdminJobs().then(setJobsData).catch(() => {});
    } else if (activeTab === 'health') {
      getAdminSystemHealth().then(setHealthData).catch(() => {});
    }
  }, [activeTab]);

  const handleInspectUser = async (userId) => {
    setSelectedUserId(userId);
    setJourneyLoading(true);
    try {
      const journey = await getAdminUserJourney(userId);
      setUserJourney(journey);
    } catch (err) {
      alert('Failed to load user journey details.');
    } finally {
      setJourneyLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-slate-400 space-y-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
            <ShieldCheck size={28} className="animate-pulse text-indigo-400" />
          </div>
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-indigo-500 rounded-full animate-ping" />
        </div>
        <p className="text-sm font-semibold text-slate-200">Connecting to Executive Command Center...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl border border-red-200 p-8 text-center shadow-lg space-y-4">
          <div className="w-14 h-14 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mx-auto border border-red-100 shadow-2xs">
            <ShieldCheck size={28} />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Access Denied</h2>
          <p className="text-xs text-gray-600 leading-relaxed">{error}</p>
        </div>
      </div>
    );
  }

  const isWarning = overview?.failed_jobs_count > 5;

  return (
    <div className="min-h-screen bg-gray-50/80 text-gray-900 flex flex-col">
      {/* Top Header Bar */}
      <header className="h-16 bg-white border-b border-gray-200/90 px-4 sm:px-6 flex items-center justify-between shrink-0 shadow-2xs z-20">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white font-bold shadow-xs">
            <BookOpen size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-extrabold text-gray-900 tracking-tight">StudyPulse<span className="text-indigo-600">.AI</span></span>
              <span className="bg-indigo-50 text-indigo-700 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider border border-indigo-200">
                Command Center
              </span>
            </div>
          </div>
        </div>

        <UserHeaderMenu />
      </header>

      {/* Main Container */}
      <div className="flex-1 p-4 sm:p-6 max-w-7xl w-full mx-auto space-y-6">
        {/* EXECUTIVE COMMAND BANNER */}
        <div className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl border border-indigo-700/30">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-xs font-semibold text-indigo-200">
                  <ShieldCheck size={14} className="text-indigo-400" />
                  Executive Control Panel
                </span>

                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                  isWarning 
                    ? 'bg-amber-500/20 text-amber-300 border-amber-400/30' 
                    : 'bg-emerald-500/20 text-emerald-300 border-emerald-400/30'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${isWarning ? 'bg-amber-400 animate-ping' : 'bg-emerald-400 animate-pulse'}`} />
                  System {overview?.system_status || 'HEALTHY'}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                System Administration & Analytics
              </h1>
              <p className="text-xs sm:text-sm text-slate-300 max-w-2xl">
                Global platform oversight, user activity auditing, AI quality metrics, background job queues, and infrastructure diagnostics.
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={fetchOverview}
                className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-white/10 backdrop-blur-md transition-all cursor-pointer shadow-xs"
                title="Refresh All System Overview Metrics"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                <span>Sync Data</span>
              </button>
            </div>
          </div>
        </div>

        {/* NAVIGATION TABS */}
        <div className="bg-white rounded-2xl border border-gray-200/90 p-1.5 shadow-2xs">
          <div className="flex items-center gap-1 overflow-x-auto pb-0.5 scrollbar-hide">
            {[
              { id: 'overview', icon: <ShieldCheck size={15} />, label: 'Overview' },
              { id: 'users', icon: <Users size={15} />, label: 'Users & Journeys' },
              { id: 'activity', icon: <Activity size={15} />, label: 'Global Audit Stream' },
              { id: 'engagement', icon: <TrendingUp size={15} />, label: 'Active Learners' },
              { id: 'ai-usage', icon: <Sparkles size={15} />, label: 'AI Usage & Quality' },
              { id: 'jobs', icon: <Cpu size={15} />, label: 'Worker Queue' },
              { id: 'health', icon: <Server size={15} />, label: 'System Health' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-xs'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 font-semibold'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Card 1: Total Users */}
              <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all space-y-2 border-l-4 border-l-indigo-600">
                <span className="text-[11px] font-extrabold text-indigo-900 uppercase tracking-wider">Total Learners</span>
                <div className="text-3xl font-black text-gray-900">{overview?.total_users ?? 0}</div>
                <p className="text-[11px] text-gray-400 font-medium">Registered student accounts</p>
              </div>

              {/* Card 2: Active Projects */}
              <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all space-y-2 border-l-4 border-l-violet-600">
                <span className="text-[11px] font-extrabold text-violet-900 uppercase tracking-wider">Active Workspaces</span>
                <div className="text-3xl font-black text-violet-600">{overview?.active_projects_count ?? 0}</div>
                <p className="text-[11px] text-gray-400 font-medium">Projects active in 30 days</p>
              </div>

              {/* Card 3: Tutor Requests */}
              <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all space-y-2 border-l-4 border-l-sky-600">
                <span className="text-[11px] font-extrabold text-sky-900 uppercase tracking-wider">Tutor Requests</span>
                <div className="text-3xl font-black text-sky-600">{overview?.total_tutor_requests ?? 0}</div>
                <p className="text-[11px] text-gray-400 font-medium">Interactive Q&A prompts</p>
              </div>

              {/* Card 4: Quiz Attempts */}
              <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all space-y-2 border-l-4 border-l-emerald-600">
                <span className="text-[11px] font-extrabold text-emerald-900 uppercase tracking-wider">Quiz Attempts</span>
                <div className="text-3xl font-black text-emerald-600">{overview?.total_quiz_attempts ?? 0}</div>
                <p className="text-[11px] text-gray-400 font-medium">Questions answered</p>
              </div>

              {/* Card 5: Failed Jobs */}
              <div className="bg-white rounded-2xl border border-gray-200/90 p-5 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all space-y-2 border-l-4 border-l-rose-500">
                <span className="text-[11px] font-extrabold text-rose-900 uppercase tracking-wider">Failed Jobs</span>
                <div className="text-3xl font-black text-rose-600">{overview?.failed_jobs_count ?? 0}</div>
                <p className="text-[11px] text-gray-400 font-medium">Background worker errors</p>
              </div>
            </div>
          </div>
        )}

        {/* USERS TAB */}
        {activeTab === 'users' && (
          <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-gray-100">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Users size={18} className="text-indigo-600" />
                Registered Learners & Journey Inspection
              </h3>
            </div>

            {!usersData ? (
              <div className="py-12 text-center text-xs text-gray-400">Loading user directory...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 text-gray-400 uppercase text-[10px] tracking-wider">
                      <th className="pb-3 font-extrabold">User Identity</th>
                      <th className="pb-3 font-extrabold">Role</th>
                      <th className="pb-3 font-extrabold">Spaces</th>
                      <th className="pb-3 font-extrabold">Projects</th>
                      <th className="pb-3 font-extrabold">Events Recorded</th>
                      <th className="pb-3 font-extrabold">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {usersData.users.map((u) => (
                      <tr key={u.id} className="hover:bg-indigo-50/30 transition-colors">
                        <td className="py-3.5">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs uppercase shrink-0">
                              {u.name?.charAt(0) || 'U'}
                            </div>
                            <div>
                              <p className="font-bold text-gray-900 text-xs">{u.name}</p>
                              <p className="text-[10px] text-gray-400">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5">
                          <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">
                            {u.role}
                          </span>
                        </td>
                        <td className="py-3.5 font-bold text-gray-800">{u.spaces_count}</td>
                        <td className="py-3.5 font-bold text-gray-800">{u.projects_count}</td>
                        <td className="py-3.5 font-extrabold text-indigo-600">{u.total_events_count}</td>
                        <td className="py-3.5">
                          <button
                            onClick={() => handleInspectUser(u.id)}
                            className="flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-xl transition-all cursor-pointer border border-indigo-100 shadow-2xs"
                          >
                            <Eye size={13} />
                            <span>Inspect Journey</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* GLOBAL ACTIVITY STREAM TAB */}
        {activeTab === 'activity' && (
          <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Activity size={18} className="text-violet-600" />
              Global Event Stream & Audit Trail
            </h3>

            {!activityData ? (
              <div className="py-12 text-center text-xs text-gray-400">Loading audit logs...</div>
            ) : (
              <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
                {activityData.events.map((ev) => (
                  <div key={ev.id} className="p-3.5 bg-gray-50/80 border border-gray-100 rounded-xl text-xs flex items-center justify-between hover:bg-gray-100/60 transition-colors">
                    <div className="space-y-1">
                      <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-100 uppercase">
                        {ev.event_type}
                      </span>
                      <p className="text-gray-900 font-semibold text-xs mt-1">User: {ev.user_id} | Workspace: {ev.project_id || 'Global'}</p>
                      <p className="text-[10px] text-gray-400 font-mono">Correlation: {ev.correlation_id}</p>
                    </div>
                    <span className="text-[10px] font-semibold text-gray-400 bg-white border border-gray-200 px-2 py-1 rounded-lg">
                      {new Date(ev.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ACTIVE LEARNERS ENGAGEMENT TAB */}
        {activeTab === 'engagement' && (
          <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp size={18} className="text-emerald-600" />
              Active Learner Engagement Metrics (DAL / WAL / MAL)
            </h3>

            {!engagementData ? (
              <div className="py-12 text-center text-xs text-gray-400">Calculating learner retention metrics...</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="p-5 bg-emerald-50/60 border border-emerald-100 rounded-2xl space-y-1">
                  <span className="text-xs font-extrabold text-emerald-800 uppercase tracking-wider">Daily Active Learners (DAL)</span>
                  <div className="text-4xl font-black text-emerald-950 mt-1">{engagementData.daily_active_learners}</div>
                </div>

                <div className="p-5 bg-sky-50/60 border border-sky-100 rounded-2xl space-y-1">
                  <span className="text-xs font-extrabold text-sky-800 uppercase tracking-wider">Weekly Active Learners (WAL)</span>
                  <div className="text-4xl font-black text-sky-950 mt-1">{engagementData.weekly_active_learners}</div>
                </div>

                <div className="p-5 bg-purple-50/60 border border-purple-100 rounded-2xl space-y-1">
                  <span className="text-xs font-extrabold text-purple-800 uppercase tracking-wider">Monthly Active Learners (MAL)</span>
                  <div className="text-4xl font-black text-purple-950 mt-1">{engagementData.monthly_active_learners}</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI USAGE & EVALUATION TAB */}
        {activeTab === 'ai-usage' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Sparkles size={18} className="text-indigo-600" />
                AI Operation Metrics Breakdown
              </h3>

              {!aiUsageData ? (
                <div className="py-12 text-center text-xs text-gray-400">Loading AI usage metrics...</div>
              ) : (
                <div className="space-y-3">
                  {aiUsageData.operations.map((op) => (
                    <div key={op.operation_type} className="flex items-center justify-between p-3.5 bg-gray-50 rounded-xl text-xs">
                      <span className="font-bold text-gray-900">{op.operation_type}</span>
                      <span className="font-extrabold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2.5 py-1 rounded-lg">
                        {op.request_count} requests
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <CheckCircle2 size={18} className="text-emerald-600" />
                AI Grounding & Evaluation Quality
              </h3>

              {!aiEvalData ? (
                <div className="py-12 text-center text-xs text-gray-400">Loading evaluation rates...</div>
              ) : (
                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
                    <span className="font-bold text-emerald-950">Tutor RAG Grounding Rate</span>
                    <span className="text-xl font-black text-emerald-700">{aiEvalData.grounding_rate_percentage}%</span>
                  </div>
                  <div className="flex items-center justify-between p-3.5 bg-gray-50 rounded-xl">
                    <span className="text-gray-600 font-semibold">Open-Ended Evaluation Count</span>
                    <span className="font-extrabold text-gray-900">{aiEvalData.open_ended_evaluations_count}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* BACKGROUND WORKERS TAB */}
        {activeTab === 'jobs' && (
          <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Cpu size={18} className="text-purple-600" />
              Background Job Queue Inspection
            </h3>

            {!jobsData ? (
              <div className="py-12 text-center text-xs text-gray-400">Loading worker job status...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 text-gray-400 uppercase text-[10px] tracking-wider">
                      <th className="pb-3 font-extrabold">Job Type</th>
                      <th className="pb-3 font-extrabold">Status</th>
                      <th className="pb-3 font-extrabold">Attempts</th>
                      <th className="pb-3 font-extrabold">Error Log</th>
                      <th className="pb-3 font-extrabold">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {jobsData.jobs.map((j) => (
                      <tr key={j.id} className="hover:bg-gray-50/50">
                        <td className="py-3 font-bold text-gray-900">{j.job_type}</td>
                        <td className="py-3">
                          <span
                            className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                              j.status === 'COMPLETED'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : j.status === 'FAILED'
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                          >
                            {j.status}
                          </span>
                        </td>
                        <td className="py-3 text-gray-700 font-semibold">{j.attempts} / {j.max_attempts}</td>
                        <td className="py-3 text-rose-600 max-w-xs truncate font-mono text-[11px]">{j.last_error || 'None'}</td>
                        <td className="py-3 text-gray-400">{new Date(j.created_at).toLocaleTimeString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* SYSTEM HEALTH TAB */}
        {activeTab === 'health' && (
          <div className="bg-white rounded-2xl border border-gray-200/90 p-6 shadow-2xs space-y-4">
            <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Server size={18} className="text-sky-600" />
              Real-Time Infrastructure Health Checks
            </h3>

            {!healthData ? (
              <div className="py-12 text-center text-xs text-gray-400">Executing health probes...</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {healthData.checks.map((chk) => (
                  <div key={chk.component} className="p-4 bg-gray-50 border border-gray-100 rounded-2xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-gray-900 text-xs">{chk.component}</span>
                      <span
                        className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${
                          chk.status === 'Healthy'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {chk.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">{chk.details}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* USER JOURNEY INSPECTION MODAL */}
        {selectedUserId && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl border border-gray-200 p-6 max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <Eye size={18} className="text-indigo-600" />
                  User Learning Journey Audit
                </h3>
                <button
                  onClick={() => setSelectedUserId(null)}
                  className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              {journeyLoading || !userJourney ? (
                <div className="py-12 text-center text-xs text-gray-400">Loading user journey metrics...</div>
              ) : (
                <div className="space-y-4 text-xs">
                  <div className="p-4 bg-indigo-50/80 border border-indigo-100 rounded-xl flex items-center justify-between">
                    <div>
                      <p className="font-bold text-indigo-950 text-sm">{userJourney.user.name}</p>
                      <p className="text-xs text-indigo-700">{userJourney.user.email}</p>
                    </div>
                    <span className="text-[10px] font-extrabold bg-white text-indigo-700 px-3 py-1 rounded-full border border-indigo-200 uppercase">
                      {userJourney.user.role}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div className="p-3 bg-gray-50 rounded-xl">
                      <p className="text-[10px] text-gray-400 font-medium">Spaces</p>
                      <p className="font-black text-gray-900 text-base">{userJourney.spaces_summary.length}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-xl">
                      <p className="text-[10px] text-gray-400 font-medium">Projects</p>
                      <p className="font-black text-gray-900 text-base">{userJourney.projects_summary.length}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-xl">
                      <p className="text-[10px] text-gray-400 font-medium">Materials</p>
                      <p className="font-black text-gray-900 text-base">{userJourney.materials_summary.total}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-xl">
                      <p className="text-[10px] text-gray-400 font-medium">Assessments</p>
                      <p className="font-black text-gray-900 text-base">{userJourney.assessments_summary.total_assessments}</p>
                    </div>
                  </div>

                  {/* Activity Stream Timeline */}
                  <div className="space-y-2">
                    <h4 className="font-bold text-gray-900 text-xs">Chronological Activity Stream</h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                      {userJourney.timeline_events.map((evt, idx) => (
                        <div key={evt.id || idx} className="p-3 bg-gray-50 border border-gray-100 rounded-xl flex items-center justify-between text-xs">
                          <div className="space-y-0.5">
                            <span className="font-bold text-indigo-700">{evt.event_type}</span>
                            <p className="text-[10px] text-gray-500 font-mono">Correlation: {evt.correlation_id}</p>
                          </div>
                          <span className="text-[10px] text-gray-400 font-medium">
                            {evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : 'Recent'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
