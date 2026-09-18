import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LogOut } from 'lucide-react';

const UserHeaderMenu = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setIsOpen(false);
    logout();
    navigate('/login', { replace: true });
  };

  if (!user) return null;

  const initial = user.name?.charAt(0).toUpperCase() || 'U';
  const isAdmin = user.role === 'admin';

  return (
    <div className="relative" ref={menuRef}>
      {/* Circle Avatar Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-600 text-white font-bold text-sm flex items-center justify-center shadow-xs hover:shadow-md hover:scale-105 active:scale-95 transition-all cursor-pointer ring-2 ring-indigo-500/20 focus:outline-none"
        title="Account Menu"
      >
        {initial}
      </button>

      {/* Popover Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50 transition-all">
          {/* User Info Header */}
          <div className="px-4 py-3 border-b border-gray-100">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-bold text-gray-900 truncate max-w-[140px]">
                {user.name}
              </p>
              <span
                className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider border ${
                  isAdmin
                    ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}
              >
                {isAdmin ? 'Admin' : 'Student'}
              </span>
            </div>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>

          {/* Action Menu Items */}
          <div className="p-1.5">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
            >
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserHeaderMenu;
