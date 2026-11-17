import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, Search, Filter, SlidersHorizontal, RefreshCw, Briefcase, MapPin, Globe } from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../api/client';
import JobCard from '../components/JobCard';

const JobsPage = () => {
  const { profileId } = useApp();
  const navigate = useNavigate();

  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters State
  const [roleQuery, setRoleQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [jobType, setJobType] = useState('all'); // all, internship, fulltime
  const [minMatch, setMinMatch] = useState(0);
  const [maxDaysOld, setMaxDaysOld] = useState(30);
  const [sortBy, setSortBy] = useState('best_match'); // best_match, newest, highest_match

  const fetchJobs = async () => {
    if (!profileId) {
      navigate('/');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      // Primary: calls the 3-stage funnel recommended endpoint
      const params = new URLSearchParams({
        profile_id: profileId,
        min_fresher_score: '60',
        limit: '100',
      });
      if (maxDaysOld) params.append('max_days_old', maxDaysOld.toString());
      if (remoteOnly) params.append('remote_only', 'true');
      if (roleQuery) params.append('role', roleQuery);
      if (locationQuery) params.append('location', locationQuery);

      let response;
      try {
        response = await api.get(`/jobs/recommended?${params.toString()}`);
      } catch (e) {
        // Fallback to legacy recommendations if backend doesn't have recommended endpoint
        response = await api.get(`/jobs/recommendations/${profileId}`);
      }
      setJobs(response.data || []);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch job recommendations. Verify the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [profileId, remoteOnly, maxDaysOld]);

  // Client-side filtering & sorting
  const filteredAndSortedJobs = useMemo(() => {
    let result = [...jobs];

    // Filter by Role/Title
    if (roleQuery.trim()) {
      const q = roleQuery.toLowerCase();
      result = result.filter(j => (j.title || '').toLowerCase().includes(q) || (j.company || '').toLowerCase().includes(q));
    }

    // Filter by Location
    if (locationQuery.trim()) {
      const loc = locationQuery.toLowerCase();
      result = result.filter(j => (j.location || '').toLowerCase().includes(loc));
    }

    // Filter by Job Type (Internship vs Fulltime)
    if (jobType === 'internship') {
      result = result.filter(j => 
        (j.title || '').toLowerCase().includes('intern') || 
        (j.title || '').toLowerCase().includes('trainee')
      );
    } else if (jobType === 'fulltime') {
      result = result.filter(j => 
        !(j.title || '').toLowerCase().includes('intern')
      );
    }

    // Filter by Min Match %
    if (minMatch > 0) {
      result = result.filter(j => {
        const score = j.match_percent !== undefined ? j.match_percent : (j.score || 0);
        return score >= minMatch;
      });
    }

    // Sorting
    result.sort((a, b) => {
      const matchA = a.match_percent !== undefined ? a.match_percent : (a.score || 0);
      const matchB = b.match_percent !== undefined ? b.match_percent : (b.score || 0);
      const fresherA = a.fresher_score || 50;
      const fresherB = b.fresher_score || 50;

      if (sortBy === 'best_match') {
        return (fresherB * matchB) - (fresherA * matchA);
      } else if (sortBy === 'highest_match') {
        return matchB - matchA;
      } else if (sortBy === 'newest') {
        const dateA = a.posted_at ? new Date(a.posted_at).getTime() : 0;
        const dateB = b.posted_at ? new Date(b.posted_at).getTime() : 0;
        return dateB - dateA;
      }
      return 0;
    });

    return result;
  }, [jobs, roleQuery, locationQuery, jobType, minMatch, sortBy]);

  if (isLoading && jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-emerald-400 mb-4" size={44} />
        <p className="text-slate-300 text-lg font-medium">Curating verified fresher jobs...</p>
        <p className="text-slate-500 text-sm mt-1">Filtering 0-2 yrs experience & working apply links</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Verified Fresher Jobs</h1>
          <p className="text-slate-400 mt-1">
            Genuine 0-2 years roles with verified apply links, customized for your skills.
          </p>
        </div>
        <button
          onClick={fetchJobs}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors border border-slate-700"
        >
          <RefreshCw size={15} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 shadow-md">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
          {/* Role Search */}
          <div className="relative">
            <Search size={16} className="absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Search by role or company..."
              value={roleQuery}
              onChange={(e) => setRoleQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Location Search */}
          <div className="relative">
            <MapPin size={16} className="absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Filter by city or country..."
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Job Type */}
          <div>
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Roles (Intern + Full-time)</option>
              <option value="internship">Internships / Trainees</option>
              <option value="fulltime">Full-Time / Graduate Roles</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="best_match">Sort by: Best Match (AI + Fresher)</option>
              <option value="highest_match">Sort by: Highest Match %</option>
              <option value="newest">Sort by: Newest Posted</option>
            </select>
          </div>
        </div>

        {/* Secondary Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80 text-xs">
          <div className="flex items-center gap-4 flex-wrap">
            {/* Remote Only Toggle */}
            <label className="flex items-center gap-2 cursor-pointer text-slate-300 font-medium">
              <input
                type="checkbox"
                checked={remoteOnly}
                onChange={(e) => setRemoteOnly(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
              />
              <span className="flex items-center gap-1">
                <Globe size={13} className="text-blue-400" /> Remote only
              </span>
            </label>

            {/* Min Match Filter */}
            <div className="flex items-center gap-1.5 text-slate-400">
              <span>Min Match:</span>
              <select
                value={minMatch}
                onChange={(e) => setMinMatch(Number(e.target.value))}
                className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-slate-200 text-xs"
              >
                <option value={0}>Any</option>
                <option value={40}>40%+</option>
                <option value={60}>60%+</option>
                <option value={80}>80%+</option>
              </select>
            </div>

            {/* Date Posted Filter */}
            <div className="flex items-center gap-1.5 text-slate-400">
              <span>Posted within:</span>
              <select
                value={maxDaysOld}
                onChange={(e) => setMaxDaysOld(Number(e.target.value))}
                className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-slate-200 text-xs"
              >
                <option value={1}>24 hours</option>
                <option value={3}>3 days</option>
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={30}>30 days</option>
              </select>
            </div>
          </div>

          <div className="text-slate-400">
            Showing <span className="font-semibold text-white">{filteredAndSortedJobs.length}</span> positions
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3">
          <AlertCircle size={22} className="text-red-400 shrink-0" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Jobs Grid */}
      {filteredAndSortedJobs.length === 0 ? (
        <div className="text-center py-16 px-4 bg-slate-900/50 border border-slate-800 rounded-xl">
          <Briefcase size={44} className="mx-auto text-slate-600 mb-3" />
          <h3 className="text-lg font-bold text-slate-200">No jobs match your filter criteria</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto mt-1 mb-4">
            Try lowering the minimum match threshold, expanding your location, or clearing search keywords.
          </p>
          <button
            onClick={() => {
              setRoleQuery('');
              setLocationQuery('');
              setRemoteOnly(false);
              setJobType('all');
              setMinMatch(0);
              setMaxDaysOld(30);
            }}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredAndSortedJobs.map((job) => (
            <JobCard
              key={job.id || job.job_id}
              job={job}
              onApplied={(appliedJobId) => {
                setJobs(prev => prev.map(j => (j.id === appliedJobId || j.job_id === appliedJobId) ? { ...j, is_applied: true } : j));
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default JobsPage;
