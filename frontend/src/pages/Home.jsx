import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Sparkles,
  BookOpen,
  Folders,
  Folder,
  Brain,
  HelpCircle,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Zap,
  CheckCircle2,
  FileText,
  BarChart3,
  Cpu,
  Compass,
} from 'lucide-react';

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12 px-1">
      {/* HERO SECTION - Floating Glassmorphic Ambient Banner */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-950 via-indigo-900 to-slate-950 rounded-[2.5rem] p-6 sm:p-12 text-white shadow-2xl border border-indigo-500/20">
        {/* Background Ambient Glow Circles */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-16 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-6">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 backdrop-blur-md text-xs font-medium text-indigo-200">
            <Sparkles size={14} className="text-amber-400 animate-pulse" />
            <span>Autonomous AI Study & Knowledge Companion</span>
          </div>

          {/* Headline */}
          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight leading-tight">
            Master Any Subject <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 via-sky-300 to-amber-200">10x Faster</span> with AI Guidance
          </h1>

          {/* Subtitle */}
          <p className="text-sm sm:text-base text-indigo-100/90 leading-relaxed font-normal">
            Welcome, <span className="font-semibold text-white">{user?.name}</span>! Organize your learning into study Spaces, index lecture materials into target Projects, chat with a 100% grounded AI Tutor, and track concept retention in real-time.
          </p>

          {/* Call-to-action buttons */}
          <div className="flex flex-wrap items-center gap-3.5 pt-2">
            <button
              onClick={() => navigate('/spaces')}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 text-white font-semibold text-sm px-6 py-3.5 rounded-2xl shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <Folders size={18} />
              <span>Explore Study Spaces</span>
              <ArrowRight size={16} />
            </button>

            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white font-medium text-sm px-6 py-3.5 rounded-2xl backdrop-blur-md border border-white/15 transition-all cursor-pointer"
            >
              <BarChart3 size={18} />
              <span>View Dashboard</span>
            </button>
          </div>

          {/* System Highlights / Badges */}
          <div className="pt-6 border-t border-indigo-700/40 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs text-indigo-200 font-medium">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <span>100% Grounded RAG</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <span>Adaptive Quizzes</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <span>Concept Mastery Matrix</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
              <span>Background Processing</span>
            </div>
          </div>
        </div>
      </div>

      {/* CORE FEATURE HUBS - Floating Soft Cards (No Harsh Box Borders) */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Compass className="text-indigo-600" size={20} />
              Study & Knowledge Capabilities
            </h2>
            <p className="text-xs text-gray-500">Everything you need to transform static study materials into active retention</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Spaces & Projects */}
          <div
            onClick={() => navigate('/spaces')}
            className="bg-gradient-to-b from-white via-white to-indigo-50/30 rounded-[1.75rem] border border-slate-100 p-6 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 transform hover:-translate-y-1 cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3.5">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100/80 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-2xs">
                <Folders size={22} />
              </div>
              <h3 className="font-semibold text-gray-900 text-base group-hover:text-indigo-600 transition-colors">
                Spaces & Projects
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Structure your courses into subject Spaces and targeted project workspaces with automated file parsing.
              </p>
            </div>
            <div className="mt-5 pt-4 border-t border-slate-100/80 flex items-center text-xs font-medium text-indigo-600">
              <span>Open Spaces</span>
              <ArrowRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Card 2: AI Tutor */}
          <div
            onClick={() => navigate('/projects')}
            className="bg-gradient-to-b from-white via-white to-purple-50/30 rounded-[1.75rem] border border-slate-100 p-6 shadow-sm hover:shadow-xl hover:shadow-purple-500/10 transition-all duration-300 transform hover:-translate-y-1 cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3.5">
              <div className="w-12 h-12 rounded-2xl bg-purple-50 border border-purple-100/80 text-purple-600 flex items-center justify-center group-hover:bg-purple-600 group-hover:text-white transition-all shadow-2xs">
                <Brain size={22} />
              </div>
              <h3 className="font-semibold text-gray-900 text-base group-hover:text-purple-600 transition-colors">
                Grounded AI Tutor
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Ask questions, request summaries, and get step-by-step explanations grounded strictly in your documents.
              </p>
            </div>
            <div className="mt-5 pt-4 border-t border-slate-100/80 flex items-center text-xs font-medium text-purple-600">
              <span>Launch Projects & Tutor</span>
              <ArrowRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Card 3: Adaptive Quizzes */}
          <div
            onClick={() => navigate('/dashboard')}
            className="bg-gradient-to-b from-white via-white to-emerald-50/30 rounded-[1.75rem] border border-slate-100 p-6 shadow-sm hover:shadow-xl hover:shadow-emerald-500/10 transition-all duration-300 transform hover:-translate-y-1 cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3.5">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100/80 text-emerald-600 flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition-all shadow-2xs">
                <HelpCircle size={22} />
              </div>
              <h3 className="font-semibold text-gray-900 text-base group-hover:text-emerald-600 transition-colors">
                Adaptive Assessments
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Dynamic MCQs & open-ended evaluation that challenge your understanding and adapt to your progress.
              </p>
            </div>
            <div className="mt-5 pt-4 border-t border-slate-100/80 flex items-center text-xs font-medium text-emerald-600">
              <span>Review Performance</span>
              <ArrowRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Card 4: Concept Mastery Matrix */}
          <div
            onClick={() => navigate('/dashboard')}
            className="bg-gradient-to-b from-white via-white to-rose-50/30 rounded-[1.75rem] border border-slate-100 p-6 shadow-sm hover:shadow-xl hover:shadow-rose-500/10 transition-all duration-300 transform hover:-translate-y-1 cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3.5">
              <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-100/80 text-rose-600 flex items-center justify-center group-hover:bg-rose-600 group-hover:text-white transition-all shadow-2xs">
                <TrendingUp size={22} />
              </div>
              <h3 className="font-semibold text-gray-900 text-base group-hover:text-rose-600 transition-colors">
                Mastery Analytics
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                Track concept growth scores, pinpoint weak areas, and get automatic AI daily review recommendations.
              </p>
            </div>
            <div className="mt-5 pt-4 border-t border-slate-100/80 flex items-center text-xs font-medium text-rose-600">
              <span>View Analytics</span>
              <ArrowRight size={14} className="ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>

      {/* INTELLIGENT LEARNING WORKFLOW PIPELINE - Soft Curved Glass Container */}
      <div className="bg-gradient-to-b from-white to-slate-50/60 rounded-[2rem] border border-slate-100 p-6 sm:p-10 shadow-sm space-y-6">
        <div>
          <span className="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100/80">
            Intelligent Learning Workflow
          </span>
          <h2 className="text-xl font-semibold text-gray-900 mt-3">
            How StudyPulse AI Transforms Your Learning
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Step 1 */}
          <div className="space-y-3 p-5 bg-white rounded-2xl border border-slate-100 shadow-2xs hover:shadow-md transition-all">
            <div className="w-9 h-9 rounded-2xl bg-indigo-600 text-white font-semibold text-sm flex items-center justify-center shadow-xs">
              1
            </div>
            <h4 className="font-semibold text-gray-900 text-sm">Upload & Index</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              Upload PDF lecture notes or textbook chapters. Background workers extract concepts & build vector embeddings.
            </p>
          </div>

          {/* Step 2 */}
          <div className="space-y-3 p-5 bg-white rounded-2xl border border-slate-100 shadow-2xs hover:shadow-md transition-all">
            <div className="w-9 h-9 rounded-2xl bg-purple-600 text-white font-semibold text-sm flex items-center justify-center shadow-xs">
              2
            </div>
            <h4 className="font-semibold text-gray-900 text-sm">Interact & Clarify</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              Ask questions to your AI Tutor. Get citations and grounded answers directly referencing your materials.
            </p>
          </div>

          {/* Step 3 */}
          <div className="space-y-3 p-5 bg-white rounded-2xl border border-slate-100 shadow-2xs hover:shadow-md transition-all">
            <div className="w-9 h-9 rounded-2xl bg-emerald-600 text-white font-semibold text-sm flex items-center justify-center shadow-xs">
              3
            </div>
            <h4 className="font-semibold text-gray-900 text-sm">Assess Knowledge</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              Generate practice quizzes. Answer open-ended prompts and receive instant AI conceptual evaluations.
            </p>
          </div>

          {/* Step 4 */}
          <div className="space-y-3 p-5 bg-white rounded-2xl border border-slate-100 shadow-2xs hover:shadow-md transition-all">
            <div className="w-9 h-9 rounded-2xl bg-amber-600 text-white font-semibold text-sm flex items-center justify-center shadow-xs">
              4
            </div>
            <h4 className="font-semibold text-gray-900 text-sm">Track & Retain</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              Monitor your concept mastery growth and receive targeted daily study recommendations for long-term retention.
            </p>
          </div>
        </div>
      </div>

      {/* QUICK LAUNCH PAD CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className="bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-700 rounded-[2rem] p-7 text-white shadow-xl flex items-center justify-between">
          <div className="space-y-2.5 max-w-sm">
            <h3 className="text-lg font-semibold">Ready to Start Studying?</h3>
            <p className="text-xs text-indigo-100/90 leading-relaxed">
              Create a new Study Space, upload your course materials, and let StudyPulse AI guide your preparation.
            </p>
            <button
              onClick={() => navigate('/spaces')}
              className="mt-2 inline-flex items-center gap-2 bg-white text-indigo-700 hover:bg-indigo-50 font-semibold text-xs px-5 py-3 rounded-xl shadow-md transition-all transform hover:scale-105 cursor-pointer"
            >
              <span>Go to Spaces</span>
              <ArrowRight size={14} />
            </button>
          </div>
          <Folders size={52} className="text-indigo-300/30 shrink-0 hidden sm:block" />
        </div>

        <div className="bg-slate-950 rounded-[2rem] p-7 text-white shadow-xl flex items-center justify-between border border-slate-800/80">
          <div className="space-y-2.5 max-w-sm">
            <h3 className="text-lg font-semibold">Inspect Learning Analytics</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Review your overall quiz accuracy, total study events, and active learning project summaries.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="mt-2 inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white hover:from-indigo-400 hover:to-indigo-500 font-semibold text-xs px-5 py-3 rounded-xl shadow-md transition-all transform hover:scale-105 cursor-pointer"
            >
              <span>Open Dashboard</span>
              <ArrowRight size={14} />
            </button>
          </div>
          <BarChart3 size={52} className="text-slate-700/50 shrink-0 hidden sm:block" />
        </div>
      </div>
    </div>
  );
};

export default Home;
