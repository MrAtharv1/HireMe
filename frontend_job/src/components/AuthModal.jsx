import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { X, Mail, Lock, User, AlertCircle, Loader2, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';
import { useApp } from '../context/AppContext';

const AuthModal = () => {
  const {
    isAuthModalOpen,
    setIsAuthModalOpen,
    authModalMode,
    login,
    register,
    authError,
    setAuthError,
    isAuthLoading,
    enterDemoMode,
  } = useApp();

  const navigate = useNavigate();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [successMsg, setSuccessMsg] = useState(null);

  // Sync mode with context state whenever modal opens
  useEffect(() => {
    if (isAuthModalOpen && authModalMode) {
      setMode(authModalMode);
    }
  }, [isAuthModalOpen, authModalMode]);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isAuthModalOpen) {
        handleClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

  const handleClose = () => {
    setIsAuthModalOpen(false);
    setAuthError(null);
    setSuccessMsg(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setAuthError('Please fill in both email and password.');
      return;
    }

    if (mode === 'login') {
      const res = await login(email, password);
      if (res?.success) {
        setSuccessMsg('Signed in successfully!');
        setTimeout(handleClose, 500);
      }
    } else {
      if (password.length < 6) {
        setAuthError('Password must be at least 6 characters.');
        return;
      }
      const res = await register(email, password, fullName);
      if (res?.success) {
        setSuccessMsg('Account created and signed in successfully!');
        setTimeout(handleClose, 500);
      }
    }
  };

  const handleFillDemo = () => {
    setEmail('testuser@example.com');
    setPassword('Password123!');
    setMode('login');
    setAuthError(null);
  };

  const handleLaunchInstantDemo = () => {
    enterDemoMode();
    handleClose();
    navigate('/jobs');
  };

  const modalContent = (
    <div
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md transition-opacity duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
      role="dialog"
      aria-modal="true"
    >
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 sm:p-7 overflow-hidden text-slate-200">
        {/* Decorative ambient glow */}
        <div className="absolute -top-16 -right-16 w-36 h-36 bg-brand-accent/20 rounded-full blur-3xl pointer-events-none" />

        {/* Close button */}
        <button
          type="button"
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
          aria-label="Close dialog"
        >
          <X size={18} />
        </button>

        {/* Header */}
        <div className="text-center mb-5">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-brand-accent/10 border border-brand-accent/30 rounded-2xl text-brand-accent mb-3">
            <Sparkles size={24} />
          </div>
          <h2 className="text-2xl font-bold text-slate-100">
            {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
            {mode === 'login'
              ? 'Sign in to access your tailored resumes, saved facts, and job application history.'
              : 'Join HireMe AI to get curated jobs and minimal-edit ATS resume tailoring.'}
          </p>
        </div>

        {/* Prominent High-Contrast Instant Demo Callout */}
        <div className="mb-5 p-3 rounded-xl bg-gradient-to-r from-amber-500/15 via-yellow-500/10 to-amber-500/15 border border-amber-500/40 shadow-inner">
          <button
            type="button"
            onClick={handleLaunchInstantDemo}
            className="w-full py-2.5 px-3.5 bg-gradient-to-r from-amber-400 to-yellow-400 hover:from-amber-300 hover:to-yellow-300 text-slate-950 font-extrabold rounded-xl text-xs flex items-center justify-center gap-2 shadow-md shadow-amber-500/20 transition-all cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <Sparkles size={14} className="shrink-0 text-slate-950" />
            <span>Launch Instant Demo (No Signup)</span>
            <ArrowRight size={14} className="shrink-0 text-slate-950 ml-auto" />
          </button>
          <p className="text-[10px] text-amber-200/80 text-center mt-1.5 font-medium">
            ⚡ Instant client-side access • 15 pre-scored jobs • Live ATS tailoring
          </p>
        </div>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <div className="relative flex justify-center text-[10px] uppercase tracking-wider">
            <span className="bg-slate-900 px-2.5 text-slate-500 font-bold">
              {mode === 'login' ? 'Or Sign In with Email' : 'Or Create New Account'}
            </span>
          </div>
        </div>

        {/* Success banner */}
        {successMsg && (
          <div className="mb-4 bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-xl text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 size={16} className="shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error banner */}
        {authError && (
          <div className="mb-4 bg-red-500/10 border border-red-500/30 p-3 rounded-xl text-red-400 text-xs flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>{authError}</span>
          </div>
        )}

        {/* Traditional Email & Password Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User size={15} className="absolute left-3.5 top-3 text-slate-500" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Arjun Sharma"
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail size={15} className="absolute left-3.5 top-3 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-slate-400">
                Password
              </label>
              {mode === 'login' && (
                <button
                  type="button"
                  onClick={handleFillDemo}
                  className="text-[11px] text-brand-accent hover:underline cursor-pointer"
                >
                  Quick Demo Login
                </button>
              )}
            </div>
            <div className="relative">
              <Lock size={15} className="absolute left-3.5 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isAuthLoading}
            className="w-full mt-2 bg-brand-accent hover:bg-brand-accent/90 text-slate-950 py-2.5 rounded-xl text-xs font-bold transition-all shadow-md shadow-brand-accent/10 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
          >
            {isAuthLoading && <Loader2 size={14} className="animate-spin" />}
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        {/* Toggle between Login and Register */}
        <div className="mt-4 text-center text-xs text-slate-400 border-t border-slate-800/80 pt-3">
          {mode === 'login' ? (
            <>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setAuthError(null);
                }}
                className="text-brand-accent hover:underline font-semibold cursor-pointer ml-1"
              >
                Sign up free
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setAuthError(null);
                }}
                className="text-brand-accent hover:underline font-semibold cursor-pointer ml-1"
              >
                Sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default AuthModal;
