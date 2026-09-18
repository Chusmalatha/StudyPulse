import React from 'react';
import { Menu } from 'lucide-react';
import UserHeaderMenu from './UserHeaderMenu';

const Header = ({ onMenuToggle }) => {
  return (
    <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/60 flex items-center justify-between px-4 sm:px-6 shrink-0 sticky top-0 z-20">
      {/* Left: hamburger on mobile */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>
        <span className="lg:hidden text-base font-bold text-slate-900 tracking-tight">
          StudyPulse<span className="text-indigo-600">.AI</span>
        </span>
      </div>

      {/* Right: user header menu */}
      <UserHeaderMenu />
    </header>
  );
};

export default Header;
