import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Eye, EyeOff, Loader2 } from 'lucide-react';

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [slowLoad, setSlowLoad] = useState(false);
  const slowLoadTimerRef = useRef(null);


  const validate = () => {
    const e = {};
    if (!form.email) e.email = 'Email is required.';
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Enter a valid email address.';
    if (!form.password) e.password = 'Password is required.';
    return e;
  };

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors(prev => ({ ...prev, [e.target.name]: '' }));
    setApiError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const fieldErrors = validate();
    if (Object.keys(fieldErrors).length) { setErrors(fieldErrors); return; }

    setIsSubmitting(true);
    setSlowLoad(false);
    // Show a friendly message after 5s if still waiting (Atlas cold start)
    slowLoadTimerRef.current = setTimeout(() => setSlowLoad(true), 5000);
    try {
      const loggedUser = await login(form.email, form.password);
      if (loggedUser?.role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setApiError('The request timed out. The database may be waking up — please try again in a moment.');
      } else if (!err?.response) {
        setApiError('Unable to connect to the backend server. Please make sure the backend is running on http://localhost:8000.');
      } else if (err.response.status === 503) {
        setApiError('Service temporarily unavailable. The database may be starting up — please wait a moment and try again.');
      } else {
        const detail = err?.response?.data?.detail;
        setApiError(detail || 'Invalid email or password. Please try again.');
      }
    } finally {
      clearTimeout(slowLoadTimerRef.current);
      setSlowLoad(false);
      setIsSubmitting(false);
    }
  };



  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md">
              <BookOpen size={24} />
            </div>
            <span className="text-2xl font-extrabold text-gray-900 tracking-tight">StudyPulse<span className="text-indigo-600">.AI</span></span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Sign in to your account</h1>
          <p className="mt-2 text-sm text-gray-500">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="text-indigo-600 hover:text-indigo-500 font-medium">
              Register
            </Link>
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {apiError && (
            <div className="mb-5 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
              {apiError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.email ? 'border-red-400 bg-red-50' : 'border-gray-300'
                }`}
                placeholder="you@example.com"
              />
              {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={form.password}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 pr-10 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                    errors.password ? 'border-red-400 bg-red-50' : 'border-gray-300'
                  }`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password}</p>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              id="login-submit-btn"
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium py-2.5 rounded-lg transition-colors"
            >
              {isSubmitting
                ? <><Loader2 size={16} className="animate-spin" /> {slowLoad ? 'Connecting to database…' : 'Signing in…'}</>
                : 'Sign in'}
            </button>
            {isSubmitting && slowLoad && (
              <p className="text-center text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg py-2 px-3">
                ⏳ The database is waking up (free tier). This may take up to a minute on first login — please wait.
              </p>
            )}
          </form>

        </div>
      </div>
    </div>
  );
};

export default Login;
