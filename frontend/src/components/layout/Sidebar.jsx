import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, LayoutDashboard, Folder, Folders, Settings, X, BookOpen } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { user } = useAuth();

  const navItems = [
    { name: 'Home', path: '/', icon: <Home size={20} /> },
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'Spaces', path: '/spaces', icon: <Folders size={20} /> },
    { name: 'Projects', path: '/projects', icon: <Folder size={20} /> },
  ];

  const handleNavClick = () => {
    // Close sidebar on mobile after navigation
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-0 left-0 h-full z-30 w-64 bg-white/90 backdrop-blur-xl border-r border-slate-200/70 flex flex-col shadow-xl sm:shadow-none
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:relative lg:translate-x-0 lg:z-auto lg:flex
        `}
      >
        {/* Logo + close button */}
        <div className="h-20 flex items-center justify-between px-6 border-b border-slate-100 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-violet-600 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-500/20">
              <BookOpen size={20} />
            </div>
            <span className="text-xl font-bold text-slate-900 tracking-tight">StudyPulse<span className="text-indigo-600">.AI</span></span>
          </div>
          {/* Close button — only visible on mobile */}
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={handleNavClick}
                className={`flex items-center gap-3.5 px-4 py-3 rounded-2xl font-medium text-sm transition-all duration-200 ${isActive
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white font-semibold shadow-md shadow-indigo-500/20 transform translate-x-0.5'
                  : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                  }`}
              >
                <div className={`${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-900'}`}>
                  {item.icon}
                </div>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* User badge at the bottom */}
        {user && (
          <div className="px-4 py-4 border-t border-slate-100 shrink-0">
            <div className="flex items-center gap-3 px-3.5 py-3 bg-slate-50/80 border border-slate-100 rounded-2xl">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 text-white flex items-center justify-center shrink-0 text-sm font-bold uppercase shadow-sm">
                {user.name?.charAt(0)}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-slate-900 truncate">{user.name}</p>
                <p className="text-[11px] text-slate-400 truncate capitalize font-medium">{user.role}</p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
};

export default Sidebar;
