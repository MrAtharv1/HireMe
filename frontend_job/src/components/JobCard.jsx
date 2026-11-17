import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, MapPin, ExternalLink, Wand2, CheckCircle2, XCircle, Clock, ShieldCheck, Check } from 'lucide-react';
import api from '../api/client';
import { useApp } from '../context/AppContext';

const JobCard = ({ job, onApplied }) => {
  const navigate = useNavigate();
  const { profileId } = useApp();
  const [isApplying, setIsApplying] = useState(false);
  const [isApplied, setIsApplied] = useState(job.is_applied || false);

  const getScoreColor = (score) => {
    if (score >= 75) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
  };

  const formatDaysAgo = (dateStr) => {
    if (!dateStr) return 'Recently';
    const posted = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now - posted) / (1000 * 60 * 60));
    if (diffHours < 24) return `${Math.max(1, diffHours)}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const handleMarkApplied = async (e) => {
    e.stopPropagation();
    if (!profileId || isApplied) return;
    setIsApplying(true);
    try {
      await api.post('/applications/apply', {
        profile_id: profileId,
        job_id: job.id || job.job_id,
        notes: 'Applied via job board link',
      });
      setIsApplied(true);
      if (onApplied) onApplied(job.id || job.job_id);
    } catch (err) {
      console.error('Failed to mark as applied:', err);
      // If already applied, set local status true
      if (err.response?.status === 400) {
        setIsApplied(true);
      }
    } finally {
      setIsApplying(false);
    }
  };

  const handleApplyClick = (e) => {
    e.stopPropagation();
    if (job.apply_url) {
      window.open(job.apply_url, '_blank', 'noopener,noreferrer');
    }
  };

  const isRemote = job.remote || (job.location && job.location.toLowerCase().includes('remote'));
  const matchPct = job.match_percent !== undefined ? job.match_percent : (job.score || 70);
  const fresherScore = job.fresher_score !== undefined ? Math.round(job.fresher_score) : null;
  const sourceName = job.source ? job.source.toUpperCase() : 'DIRECT';

  return (
    <div className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-all duration-200 flex flex-col h-full shadow-lg relative group">
      {/* Top Bar: Company, Location, Badges */}
      <div className="flex justify-between items-start mb-3 gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {sourceName}
            </span>
            {isRemote && (
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Remote
              </span>
            )}
            <span className="text-xs text-slate-500 flex items-center">
              <Clock size={12} className="mr-1 inline" /> {formatDaysAgo(job.posted_at)}
            </span>
          </div>

          <h3 className="text-lg font-bold text-slate-100 truncate hover:text-white" title={job.title}>
            {job.title}
          </h3>

          <div className="flex items-center space-x-3 text-sm text-slate-400 mt-1">
            <span className="flex items-center truncate">
              <Building2 size={15} className="mr-1 text-slate-500 shrink-0" /> {job.company || 'Company'}
            </span>
            <span className="flex items-center truncate">
              <MapPin size={15} className="mr-1 text-slate-500 shrink-0" /> {job.location || 'Remote'}
            </span>
          </div>
        </div>

        {/* Scores */}
        <div className="flex flex-col items-end gap-1 shrink-0">
          <div className={`px-2.5 py-1 rounded-lg border font-bold text-xs ${getScoreColor(matchPct)}`}>
            {matchPct}% Match
          </div>
          {fresherScore !== null && (
            <div className="text-[11px] font-medium text-slate-400 flex items-center" title="Fresher-suitability rating">
              <ShieldCheck size={13} className="mr-0.5 text-emerald-400" />
              Fresher Score: {fresherScore}
            </div>
          )}
        </div>
      </div>

      {/* Fresher-Fit Reason */}
      {job.reason && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
          <span className="font-semibold text-emerald-400">Why it fits: </span>
          {job.reason}
        </div>
      )}

      {/* Skills Overlap Chips */}
      <div className="mb-4 flex-grow">
        {job.matched_skills && job.matched_skills.length > 0 && (
          <div className="mb-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center">
              <CheckCircle2 size={12} className="mr-1 text-emerald-400" /> Matched Skills
            </p>
            <div className="flex flex-wrap gap-1.5">
              {job.matched_skills.slice(0, 5).map((skill, idx) => (
                <span key={idx} className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {job.missing_skills && job.missing_skills.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center">
              <XCircle size={12} className="mr-1 text-slate-400" /> Missing Skills
            </p>
            <div className="flex flex-wrap gap-1.5">
              {job.missing_skills.slice(0, 4).map((skill, idx) => (
                <span key={idx} className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-3 border-t border-slate-800/80 flex flex-col gap-2">
        <div className="flex items-center gap-2">
          {/* Apply External Link */}
          <button
            onClick={handleApplyClick}
            disabled={!job.apply_url}
            className="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white rounded-lg font-medium text-xs transition-colors flex items-center justify-center gap-1 shadow-sm disabled:opacity-50"
          >
            <span>Apply</span>
            <ExternalLink size={13} />
          </button>

          {/* Mark As Applied Toggle */}
          <button
            onClick={handleMarkApplied}
            disabled={isApplied || isApplying}
            className={`py-2 px-3 rounded-lg font-medium text-xs transition-colors flex items-center justify-center gap-1 border ${
              isApplied
                ? 'bg-slate-800 text-emerald-400 border-emerald-500/40 cursor-default'
                : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 border-slate-700'
            }`}
          >
            {isApplied ? (
              <>
                <Check size={13} />
                <span>Applied</span>
              </>
            ) : (
              <span>Track App</span>
            )}
          </button>
        </div>

        {/* Tailor Resume Button */}
        <button
          onClick={() => navigate(`/jobs/${job.id || job.job_id}`)}
          className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 active:bg-slate-800 text-indigo-300 hover:text-indigo-200 rounded-lg font-medium text-xs transition-colors flex items-center justify-center gap-1.5 border border-indigo-500/20"
        >
          <Wand2 size={13} className="text-indigo-400" />
          <span>Tailor Resume for this Job</span>
        </button>
      </div>
    </div>
  );
};

export default JobCard;
