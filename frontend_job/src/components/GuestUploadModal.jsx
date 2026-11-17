import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import {
  X,
  Sparkles,
  ArrowRight,
  Lock,
  Mail,
  User,
  UserPlus,
  LogIn,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ChevronLeft,
  FileText,
} from 'lucide-react';
import { useApp } from '../context/AppContext';

/**
 * GuestUploadModal
 * 
 * Displayed whenever an unauthenticated (guest) user attempts to click
 * the upload button or drop a resume file.
 * 
 * Features:
 * 1. Flashy high-contrast Instant Demo button on top.
 * 2. Thin horizontal divider line.
 * 3. Sign In / Sign Up button beneath the line, which seamlessly transitions
 *    to login/registration so the user can use their own resume once signed in.
 */
const GuestUploadModal = ({ isOpen, onClose, pendingFile, onAuthenticatedWithFile }) => {
  const { enterDemoMode, login, register, isAuthLoading } = useApp();
  const navigate = useNavigate();

  // 'choice' (shows the 2 buttons with thin line) | 'login' | 'register'
  const [view, setView] = useState('choice');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Reset view whenever modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setView('choice');
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  if (!isOpen) return null;

  const handleClose = () => {
    setErrorMsg(null);
    setSuccessMsg(null);
    onClose();
  };

  const handleLaunchDemo = () => {
    enterDemoMode();
    handleClose();
    navigate('/jobs');
  };

  const handleSubmitAuth = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!email || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    if (view === 'login') {
      const res = await login(email, password);
      if (res?.success) {
        setSuccessMsg('Signed in successfully!');
        setTimeout(() => {
          handleClose();
          if (pendingFile && onAuthenticatedWithFile) {
            onAuthenticatedWithFile(pendingFile);
          }
        }, 500);
      } else {
        setErrorMsg(res?.error || 'Invalid credentials.');
      }
    } else if (view === 'register') {
      if (password.length < 6) {
        setErrorMsg('Password must be at least 6 characters.');
        return;
      }
      const res = await register(email, password, fullName);
      if (res?.success) {
        setSuccessMsg('Account created! You can now upload your resume.');
        setTimeout(() => {
          handleClose();
          if (pendingFile && onAuthenticatedWithFile) {
            onAuthenticatedWithFile(pendingFile);
          }
        }, 500);
      } else {
        setErrorMsg(res?.error || 'Failed to create account.');
      }
    }
  };

  const modalContent = (
    <div
      className="fixed inset-0 z-[999999] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md transition-opacity duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="guest-modal-title"
    >
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 sm:p-7 overflow-hidden text-slate-200">
        {/* Decorative ambient background glows */}
        <div className="absolute -top-14 -right-14 w-40 h-40 bg-amber-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-14 -left-14 w-40 h-40 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
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
          <div className="inline-flex items-center justify-center w-12 h-12 bg-amber-500/15 border border-amber-500/30 rounded-2xl text-amber-400 mb-3 shadow-inner">
            <Lock size={22} />
          </div>
          <h2 id="guest-modal-title" className="text-2xl font-bold text-slate-100">
            {view === 'choice' && 'Sign In or Try Instant Demo'}
            {view === 'login' && 'Sign In to Upload Resume'}
            {view === 'register' && 'Create Account to Upload Resume'}
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
            {view === 'choice' &&
              'You need an account to upload your own resume, or you can explore the platform instantly with zero signup.'}
            {view === 'login' && 'Enter your credentials to upload and tailor your personal resume.'}
            {view === 'register' && 'Join in 10 seconds to parse and tailor your resume for 0–2 yr jobs.'}
          </p>
        </div>

        {/* Pending File Indicator (if user dropped a file) */}
        {pendingFile && (
          <div className="mb-4 py-2 px-3 bg-slate-800/80 border border-slate-700/70 rounded-xl flex items-center gap-2 text-xs text-slate-300">
            <FileText size={15} className="text-emerald-400 shrink-0" />
            <span className="truncate flex-1">
              Ready to parse: <strong>{pendingFile.name}</strong>
            </span>
          </div>
        )}

        {/* Success Alert */}
        {successMsg && (
          <div className="mb-4 bg-emerald-500/15 border border-emerald-500/30 p-3 rounded-xl text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 size={16} className="shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 bg-red-500/15 border border-red-500/30 p-3 rounded-xl text-red-400 text-xs flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* ─── VIEW 1: CHOICE (2 BUTTONS SEPARATED BY A THIN LINE) ─── */}
        {view === 'choice' && (
          <div className="space-y-4">
            {/* BUTTON 1: Flashy Instant Demo Button */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-400 via-yellow-300 to-amber-500 rounded-2xl blur-sm opacity-75 group-hover:opacity-100 transition duration-300 animate-pulse" />
              <button
                type="button"
                onClick={handleLaunchDemo}
                className="relative w-full py-3.5 px-4 bg-gradient-to-r from-amber-400 via-amber-300 to-yellow-400 hover:from-amber-300 hover:to-yellow-300 text-slate-950 font-extrabold rounded-xl text-sm flex items-center justify-between shadow-xl cursor-pointer transition-all transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <div className="flex items-center gap-2.5">
                  <span className="p-1 bg-slate-950/15 rounded-lg text-slate-950">
                    <Sparkles size={18} className="animate-spin" style={{ animationDuration: '6s' }} />
                  </span>
                  <div className="text-left">
                    <div className="font-extrabold tracking-tight leading-tight">
                      ⚡ Try Instant Demo (No Signup)
                    </div>
                    <div className="text-[10px] text-slate-900/80 font-medium">
                      Zero latency • 15 Pre-scored jobs • Live ATS tailoring
                    </div>
                  </div>
                </div>
                <ArrowRight size={18} className="text-slate-950 shrink-0 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

            {/* A THIN LINE BENEATH IT */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-700/80" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase tracking-wider">
                <span className="bg-slate-900 px-3 text-slate-400 font-bold">
                  or sign in to use your own resume
                </span>
              </div>
            </div>

            {/* BUTTON 2: Sign In / Sign Up Button (below the line) */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setView('register')}
                className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 shadow-md shadow-emerald-600/20 transition-all cursor-pointer hover:-translate-y-0.5"
              >
                <UserPlus size={16} />
                <span>Create Free Account to Upload</span>
              </button>

              <button
                type="button"
                onClick={() => setView('login')}
                className="w-full py-2.5 px-4 bg-slate-800/90 hover:bg-slate-750 text-slate-200 border border-slate-700 hover:border-slate-600 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <LogIn size={15} className="text-emerald-400" />
                <span>Sign In to Existing Account</span>
              </button>
            </div>

            <p className="text-[10px] text-center text-slate-500 mt-2">
              🔒 Your uploaded resumes & tailored PDFs are private to your account.
            </p>
          </div>
        )}

        {/* ─── VIEW 2: SIGN IN / REGISTER FORM (REVEALED WITHIN MODAL) ─── */}
        {(view === 'login' || view === 'register') && (
          <div>
            {/* Back button & Tab Switcher */}
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setView('choice');
                  setErrorMsg(null);
                }}
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
              >
                <ChevronLeft size={14} />
                <span>Back</span>
              </button>

              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                <button
                  type="button"
                  onClick={() => {
                    setView('register');
                    setErrorMsg(null);
                  }}
                  className={`px-2.5 py-1 rounded-lg font-semibold transition-colors cursor-pointer ${
                    view === 'register' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Sign Up
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setView('login');
                    setErrorMsg(null);
                  }}
                  className={`px-2.5 py-1 rounded-lg font-semibold transition-colors cursor-pointer ${
                    view === 'login' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Sign In
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmitAuth} className="space-y-3.5">
              {view === 'register' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Full Name</label>
                  <div className="relative">
                    <User size={15} className="absolute left-3.5 top-3 text-slate-500" />
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Arjun Sharma"
                      className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Email Address</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Password</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isAuthLoading}
                className="w-full mt-2 bg-emerald-600 hover:bg-emerald-500 text-white py-2.5 rounded-xl text-xs font-bold transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
              >
                {isAuthLoading && <Loader2 size={14} className="animate-spin" />}
                {view === 'login' ? 'Sign In & Continue' : 'Create Account & Continue'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default GuestUploadModal;
