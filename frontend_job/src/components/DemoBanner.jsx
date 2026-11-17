import React from 'react';
import { Sparkles, X, ArrowRight } from 'lucide-react';
import { useApp } from '../context/AppContext';

const DemoBanner = () => {
  const { isDemoMode, exitDemoMode, openAuthModal } = useApp();

  if (!isDemoMode) return null;

  const handleSignUpClick = () => {
    exitDemoMode();
    openAuthModal('register');
  };

  return (
    <aside
      aria-label="Instant Demo Mode notification"
      className="sticky top-0 z-[99999] w-full bg-slate-950/95 border-b border-emerald-500/30 backdrop-blur-md px-4 py-2 text-xs md:text-sm text-slate-200 shadow-md transition-all duration-200"
    >
      <div className="container mx-auto flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="flex items-center justify-center w-5 h-5 rounded-md bg-emerald-500/20 text-emerald-400 shrink-0">
            <Sparkles size={13} />
          </div>
          <p className="truncate font-medium text-slate-300">
            <span>You are exploring Instant Demo Mode — </span>
            <button
              type="button"
              onClick={handleSignUpClick}
              className="text-emerald-400 hover:text-emerald-300 font-bold underline underline-offset-2 transition-colors cursor-pointer inline-flex items-center"
            >
              Sign Up Free
            </button>
            <span> to upload your own PDF resume and run live ATS matching.</span>
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={exitDemoMode}
            className="text-xs text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 px-2.5 py-1 rounded-lg flex items-center gap-1 transition-colors cursor-pointer"
            title="Exit Demo Mode"
          >
            <span>Exit Demo</span>
            <X size={12} />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default DemoBanner;
