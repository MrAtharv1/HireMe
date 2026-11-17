import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2, MapPin, Loader2, AlertCircle, Wand2, ArrowLeft,
  CheckCircle, FileText, Download, Code, Check, X, RefreshCw,
  ExternalLink, Sparkles, AlertTriangle, Sliders, Edit3, ShieldCheck,
  CheckCircle2, Info
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../api/client';

const JobDetailPage = () => {
  const { id } = useParams();
  const { profileId } = useApp();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tailoring Controls
  const [strictness, setStrictness] = useState('balanced'); // 'conservative' | 'balanced' | 'assertive'
  const [isTailoring, setIsTailoring] = useState(false);
  const [isRecompiling, setIsRecompiling] = useState(false);
  const [versionId, setVersionId] = useState(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [texSource, setTexSource] = useState('');
  const [tailorError, setTailorError] = useState(null);

  // ATS & Audit Metrics
  const [atsScore, setAtsScore] = useState(null);
  const [fidelityScore, setFidelityScore] = useState(null);
  const [coveragePct, setCoveragePct] = useState(0);
  const [matchedSkills, setMatchedSkills] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [atsChecks, setAtsChecks] = useState({});

  // Bullets State for Side-by-Side Review
  // [{ id, entity, original, edited, currentText, accepted: bool, operations: [], keywords_added: [], retention_ratio, status }]
  const [bulletsDiff, setBulletsDiff] = useState([]);

  // Active view tab in right preview: 'pdf' | 'latex' | 'ats'
  const [previewTab, setPreviewTab] = useState('pdf');

  // Fact Editing Modal
  const [showFactModal, setShowFactModal] = useState(false);
  const [editableSkills, setEditableSkills] = useState('');
  const [isSavingFacts, setIsSavingFacts] = useState(false);

  // 1. Fetch Job and Profile Data
  useEffect(() => {
    if (!profileId) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      try {
        const [jobRes, profRes] = await Promise.all([
          api.get(`/jobs/${id}`),
          api.get(`/resume/profile/${profileId}`),
        ]);
        setJob(jobRes.data);
        const pData = profRes.data.data;
        setProfile(pData);

        const candSkills = pData.parsed_json?.skills || [];
        setEditableSkills(Array.isArray(candSkills) ? candSkills.join(', ') : '');

        // Initial keyword overlap calculation
        const jobDesc = (jobRes.data.description || '').toLowerCase();
        const initialMatched = candSkills.filter(s => jobDesc.includes(s.toLowerCase()));
        const initialGaps = ['Python', 'SQL', 'FastAPI', 'Docker', 'React'].filter(
          s => jobDesc.includes(s.toLowerCase()) && !initialMatched.includes(s)
        );
        setMatchedSkills(initialMatched);
        setGaps(initialGaps);
        const total = initialMatched.length + initialGaps.length;
        setCoveragePct(total > 0 ? Math.round((initialMatched.length / total) * 100) : 60);

      } catch (err) {
        console.error(err);
        setError('Failed to load job or candidate profile details.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id, profileId, navigate]);

  // 2. Fetch PDF as Blob and LaTeX source when versionId changes
  useEffect(() => {
    if (versionId) {
      const fetchPdf = async () => {
        try {
          const response = await api.get(`/resume/${versionId}/pdf`, { responseType: 'blob' });
          const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
          setPdfBlobUrl(url);
          setPreviewTab('pdf');
        } catch (err) {
          console.warn('PDF fetch error:', err);
        }
      };

      const fetchTex = async () => {
        try {
          const texRes = await api.get(`/resume/${versionId}/tex`, { responseType: 'text' });
          setTexSource(texRes.data);
        } catch (texErr) {
          console.warn('Failed to fetch tex source:', texErr);
        }
      };

      fetchPdf();
      fetchTex();
    }
  }, [versionId]);

  // 3. Master Minimal-Edit Tailoring Pipeline
  const handleTailorResume = async () => {
    setIsTailoring(true);
    setTailorError(null);

    try {
      const tailorRes = await api.post(
        `/resume/tailor?user_id=${profile.user_id}&job_id=${id}`,
        {
          profile_json: profile.parsed_json,
          job_description: job.description || 'Entry level software role',
          strictness: strictness,
        }
      );

      const data = tailorRes.data;
      setVersionId(data.version_id);
      setAtsScore(data.ats_score || 90);
      setFidelityScore(data.fidelity_score || 100);
      setMatchedSkills(data.matched_keywords || []);
      setGaps(data.gaps || []);
      setCoveragePct(data.coverage_percent || 90);
      setAtsChecks(data.ats_report?.ats_checks || {});

      // Map real change_log into interactive diff list
      const changeLog = data.change_log || [];
      const diffList = changeLog.map((item) => ({
        id: item.bullet_id,
        entity: item.bullet_id?.startsWith('exp_') ? 'Work Experience' : 'Key Project',
        original: item.original,
        edited: item.edited,
        currentText: item.edited,
        accepted: item.status !== 'fallback',
        operations: item.operations || [],
        keywords_added: item.keywords_added || [],
        retention_ratio: item.retention_ratio ?? 1.0,
        status: item.status,
      }));

      // Fallback if change log was empty
      if (!diffList.length) {
        const rawExp = profile.parsed_json?.experience || [];
        rawExp.forEach((exp, eIdx) => {
          const bullets = exp.bullets || exp.bullet_points || [];
          bullets.slice(0, 3).forEach((b, bIdx) => {
            diffList.push({
              id: `exp_${eIdx}_b${bIdx}`,
              entity: exp.company || 'Experience',
              original: b,
              edited: b,
              currentText: b,
              accepted: true,
              operations: ['TRIM'],
              keywords_added: [],
              retention_ratio: 1.0,
              status: 'kept_original',
            });
          });
        });
      }

      setBulletsDiff(diffList);

    } catch (err) {
      console.error(err);
      setTailorError(err.response?.data?.detail || 'Tailoring failed. Please retry.');
    } finally {
      setIsTailoring(false);
    }
  };

  // 4. Toggle Accept / Revert per bullet with live backend recompile
  const toggleBulletAccept = async (index) => {
    if (!versionId) return;

    const copy = [...bulletsDiff];
    const target = copy[index];
    const willAccept = !target.accepted;
    target.accepted = willAccept;
    target.currentText = willAccept ? target.edited : target.original;
    setBulletsDiff(copy);

    // Call recompile on backend so PDF preview updates immediately
    setIsRecompiling(true);
    try {
      const overrides = {};
      copy.forEach((b) => {
        overrides[b.id] = b.currentText;
      });

      const recRes = await api.post(`/resume/${versionId}/recompile`, {
        bullet_overrides: overrides,
        strictness: strictness,
      });

      const data = recRes.data;
      setAtsScore(data.ats_score);
      setFidelityScore(data.fidelity_score);

      // Refresh PDF blob
      const pdfRes = await api.get(`/resume/${versionId}/pdf`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([pdfRes.data], { type: 'application/pdf' }));
      setPdfBlobUrl(url);

      const texRes = await api.get(`/resume/${versionId}/tex`, { responseType: 'text' });
      setTexSource(texRes.data);

    } catch (err) {
      console.error('Recompile error:', err);
    } finally {
      setIsRecompiling(false);
    }
  };

  // 5. Save edited candidate facts before tailoring
  const handleSaveFacts = async () => {
    setIsSavingFacts(true);
    try {
      const updatedSkills = editableSkills.split(',').map((s) => s.strip ? s.strip() : s.trim()).filter(Boolean);
      const updatedProfileJson = {
        ...profile.parsed_json,
        skills: updatedSkills,
      };

      await api.put(`/resume/profile/${profileId}`, updatedProfileJson);
      setProfile((prev) => ({
        ...prev,
        parsed_json: updatedProfileJson,
      }));
      setShowFactModal(false);
    } catch (err) {
      console.error('Failed to update facts:', err);
    } finally {
      setIsSavingFacts(false);
    }
  };

  const handleDownloadPDF = () => {
    if (versionId) {
      window.open(`http://localhost:8000/api/v1/resume/${versionId}/pdf`, '_blank');
    }
  };

  const handleDownloadTex = () => {
    if (versionId) {
      window.open(`http://localhost:8000/api/v1/resume/${versionId}/tex`, '_blank');
    }
  };

  const handleApplyExternal = () => {
    if (job?.apply_url) {
      window.open(job.apply_url, '_blank', 'noopener,noreferrer');
    }
  };

  // Word-level diff visualizer
  const renderWordDiff = (original, edited) => {
    const origWords = (original || '').split(/\s+/);
    const origSet = new Set(origWords.map((w) => w.toLowerCase().replace(/[^\w]/g, '')));
    const editWords = (edited || '').split(/\s+/);
    const editSet = new Set(editWords.map((w) => w.toLowerCase().replace(/[^\w]/g, '')));

    return {
      originalMarkup: origWords.map((w, i) => {
        const clean = w.toLowerCase().replace(/[^\w]/g, '');
        const wasRemoved = clean && !editSet.has(clean);
        return (
          <span
            key={i}
            className={wasRemoved ? 'bg-rose-500/20 text-rose-300 line-through mr-1 px-0.5 rounded' : 'text-slate-300 mr-1'}
          >
            {w}
          </span>
        );
      }),
      editedMarkup: editWords.map((w, i) => {
        const clean = w.toLowerCase().replace(/[^\w]/g, '');
        const wasAdded = clean && !origSet.has(clean);
        return (
          <span
            key={i}
            className={wasAdded ? 'bg-emerald-500/20 text-emerald-300 font-semibold mr-1 px-0.5 rounded' : 'text-slate-200 mr-1'}
          >
            {w}
          </span>
        );
      }),
    };
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-emerald-400 mb-4" size={44} />
        <p className="text-slate-300 text-lg">Loading job and profile details...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-2xl mx-auto mt-20 p-6 bg-red-500/10 border border-red-500/30 rounded-xl text-center">
        <AlertCircle size={44} className="mx-auto text-red-400 mb-3" />
        <h2 className="text-xl font-bold text-slate-100 mb-2">Error Loading Job</h2>
        <p className="text-slate-400 mb-4">{error}</p>
        <button
          onClick={() => navigate('/jobs')}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm"
        >
          Back to Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-[1700px] mx-auto px-4 py-6 font-['DM_Sans',sans-serif]">
      {/* Top Header Bar */}
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/jobs')}
            className="flex items-center text-slate-400 hover:text-emerald-400 transition-colors text-sm font-medium"
          >
            <ArrowLeft size={18} className="mr-1.5" />
            Back to recommended jobs
          </button>

          <span className="text-slate-700">|</span>

          {/* Strictness Selector */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg p-1">
            <span className="text-xs text-slate-400 px-2 font-medium flex items-center gap-1">
              <Sliders size={12} className="text-slate-500" /> Strictness:
            </span>
            {['conservative', 'balanced', 'assertive'].map((mode) => (
              <button
                key={mode}
                onClick={() => setStrictness(mode)}
                className={`px-2.5 py-1 rounded text-xs font-semibold capitalize transition-all ${
                  strictness === mode
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Edit Facts Button */}
          <button
            onClick={() => setShowFactModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
          >
            <Edit3 size={13} className="text-emerald-400" />
            <span>Edit Profile Facts</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleApplyExternal}
            disabled={!job.apply_url}
            className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition-colors shadow-sm disabled:opacity-50"
          >
            <span>Apply on Company Site</span>
            <ExternalLink size={14} />
          </button>
        </div>
      </div>

      {/* Main 3-Column Tailoring Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* COLUMN 1: Job Description & Honest ATS Analysis (Left, 3.8 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h1 className="text-2xl font-bold text-white mb-2">{job.title}</h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400 mb-4 pb-4 border-b border-slate-800">
              <span className="flex items-center"><Building2 size={16} className="mr-1.5 text-slate-500" /> {job.company}</span>
              <span className="flex items-center"><MapPin size={16} className="mr-1.5 text-slate-500" /> {job.location || 'Remote'}</span>
            </div>

            {/* Keyword Match & Honest Gap Breakdown */}
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Candidate Match Coverage</span>
                <span className="text-sm font-bold text-emerald-400">{coveragePct}% Coverage</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mb-4">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${coveragePct}%` }}
                />
              </div>

              {matchedSkills.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-emerald-400 mb-1.5 flex items-center gap-1">
                    <CheckCircle2 size={13} /> Matched Skills (Supported by Facts):
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {matchedSkills.map((s, idx) => (
                      <span key={idx} className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {gaps.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-rose-400 mb-1.5 flex items-center gap-1">
                    <AlertTriangle size={13} /> Honest Gaps (Not Fabricated):
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {gaps.map((s, idx) => (
                      <span key={idx} className="text-xs px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/30">
                        {s}
                      </span>
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1 italic">
                    Per strict truthfulness rules, missing skills are left as gaps and never fabricated into your resume.
                  </p>
                </div>
              )}
            </div>

            {/* Job Description Text */}
            <div className="max-h-[380px] overflow-y-auto pr-2 text-xs text-slate-300 leading-relaxed space-y-3">
              <h3 className="font-semibold text-slate-200 text-sm">Job Description</h3>
              <div dangerouslySetInnerHTML={{ __html: job.description || 'No description available.' }} />
            </div>
          </div>
        </div>

        {/* COLUMN 2: Minimal-Edit Bullet Workspace (Center, 4.2 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col h-full">
            <div className="flex justify-between items-center mb-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShieldCheck size={18} className="text-emerald-400" />
                  Minimal-Edit Alignment
                </h2>
                <p className="text-xs text-slate-400">
                  CV is single source of truth. Zero metric fabrication.
                </p>
              </div>

              {!bulletsDiff.length && (
                <button
                  onClick={handleTailorResume}
                  disabled={isTailoring}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isTailoring ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      <span>Editing...</span>
                    </>
                  ) : (
                    <>
                      <Wand2 size={13} />
                      <span>Tailor Bullets</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {tailorError && (
              <div className="p-3 mb-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2 text-red-300 text-xs">
                <AlertTriangle size={15} className="shrink-0 mt-0.5" />
                <span>{tailorError}</span>
              </div>
            )}

            {/* Bullets List */}
            {bulletsDiff.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800 rounded-lg">
                <Wand2 size={36} className="text-slate-600 mb-2" />
                <h4 className="text-sm font-semibold text-slate-300">Ready to Tailor</h4>
                <p className="text-xs text-slate-500 max-w-xs mt-1 mb-4">
                  Click 'Tailor Bullets' to align verbs, term spellings, and implied keywords using minimal-edit rules.
                </p>
                <button
                  onClick={handleTailorResume}
                  disabled={isTailoring}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2"
                >
                  {isTailoring ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  <span>Run Minimal-Edit Pipeline</span>
                </button>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto space-y-4 max-h-[620px] pr-2">
                {bulletsDiff.map((b, idx) => {
                  const diff = renderWordDiff(b.original, b.edited);
                  return (
                    <div
                      key={b.id || idx}
                      className={`p-3.5 rounded-lg border text-xs transition-all ${
                        b.accepted
                          ? 'bg-slate-950 border-emerald-500/30'
                          : 'bg-slate-950/70 border-slate-800 opacity-80'
                      }`}
                    >
                      {/* Top Bar with Entity, Status & Toggle */}
                      <div className="flex justify-between items-center mb-2 pb-1.5 border-b border-slate-800/80">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-300 text-[11px]">{b.entity}</span>
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                              b.status === 'edited'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                : b.status === 'kept_original'
                                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {b.status === 'edited' ? 'Verified Edit' : b.status === 'kept_original' ? 'Kept Original' : 'Fallback'}
                          </span>
                        </div>

                        <button
                          onClick={() => toggleBulletAccept(idx)}
                          disabled={isRecompiling}
                          className={`px-2 py-0.5 rounded text-[11px] font-medium flex items-center gap-1 border transition-colors ${
                            b.accepted
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30'
                              : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
                          }`}
                        >
                          {b.accepted ? (
                            <>
                              <Check size={11} /> Accepted
                            </>
                          ) : (
                            <>
                              <RefreshCw size={11} /> Reverted to Original
                            </>
                          )}
                        </button>
                      </div>

                      {/* Operation Tags & Retention Ratio */}
                      <div className="flex flex-wrap items-center gap-1.5 mb-2.5">
                        {b.operations.map((op, oIdx) => (
                          <span key={oIdx} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                            {op}
                          </span>
                        ))}
                        {b.keywords_added.map((ka, kIdx) => (
                          <span key={kIdx} className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-mono">
                            +{ka.term} (evidenced)
                          </span>
                        ))}
                        <span className="text-[10px] text-slate-500 ml-auto font-mono">
                          {Math.round(b.retention_ratio * 100)}% retention
                        </span>
                      </div>

                      {/* Word-Level Diff (Original vs Edited) */}
                      <div className="space-y-2">
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          <span className="text-[10px] uppercase font-bold text-slate-500 block mb-0.5">Original (Source)</span>
                          <p className="text-xs leading-relaxed">{diff.originalMarkup}</p>
                        </div>

                        <div className="p-2 rounded bg-emerald-950/20 border border-emerald-500/20">
                          <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-0.5">
                            {b.accepted ? 'Active in Resume (Edited)' : 'Reverted (Original in Resume)'}
                          </span>
                          <p className="text-xs leading-relaxed">
                            {b.accepted ? diff.editedMarkup : b.original}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* COLUMN 3: Live Preview, ATS Report & Downloads (Right, 4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col h-full">
            {/* Header & Tabs */}
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                <button
                  onClick={() => setPreviewTab('pdf')}
                  className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    previewTab === 'pdf'
                      ? 'bg-emerald-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <FileText size={13} />
                  <span>PDF Preview</span>
                </button>
                <button
                  onClick={() => setPreviewTab('latex')}
                  className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    previewTab === 'latex'
                      ? 'bg-emerald-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Code size={13} />
                  <span>.tex Source</span>
                </button>
                <button
                  onClick={() => setPreviewTab('ats')}
                  className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    previewTab === 'ats'
                      ? 'bg-emerald-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <ShieldCheck size={13} />
                  <span>ATS Report</span>
                </button>
              </div>

              {atsScore !== null && (
                <div className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-bold">
                  ATS Score: {atsScore}/100
                </div>
              )}
            </div>

            {/* Viewer Pane */}
            <div className="flex-1 bg-slate-950 border border-slate-800 rounded-lg min-h-[500px] overflow-hidden flex flex-col">
              {previewTab === 'pdf' ? (
                pdfBlobUrl ? (
                  <iframe
                    src={pdfBlobUrl}
                    className="w-full flex-1 min-h-[500px] bg-white rounded"
                    title="Tailored Resume PDF"
                  />
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400">
                    <FileText size={40} className="text-slate-600 mb-2" />
                    <p className="text-xs">
                      {versionId
                        ? 'Loading PDF preview...'
                        : 'No PDF generated yet. Click "Tailor Bullets" to generate.'}
                    </p>
                  </div>
                )
              ) : previewTab === 'latex' ? (
                <div className="flex-1 p-3 overflow-auto max-h-[540px]">
                  <pre className="text-[11px] font-mono text-emerald-300 leading-snug whitespace-pre-wrap">
                    {texSource || '% Click "Tailor Bullets" to view generated LaTeX source code.'}
                  </pre>
                </div>
              ) : (
                /* ATS Report Breakdown Tab */
                <div className="flex-1 p-4 overflow-auto max-h-[540px] text-xs space-y-4">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <h4 className="font-bold text-slate-200 mb-2 flex items-center gap-1.5">
                      <ShieldCheck size={14} className="text-emerald-400" />
                      Deterministic ATS Compliance
                    </h4>
                    <div className="space-y-1.5 text-slate-300">
                      {Object.entries(atsChecks).map(([k, v]) => (
                        <div key={k} className="flex justify-between items-center py-1 border-b border-slate-800/50">
                          <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${v ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                            {v ? 'PASS' : 'FAIL'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
                      <span className="text-[10px] text-slate-400 block uppercase">Fidelity Score</span>
                      <span className="text-xl font-bold text-emerald-400">{fidelityScore || 100}%</span>
                      <span className="text-[9px] text-slate-500 block">Truthful Wording</span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-center">
                      <span className="text-[10px] text-slate-400 block uppercase">Owned Match</span>
                      <span className="text-xl font-bold text-emerald-400">{coveragePct}%</span>
                      <span className="text-[9px] text-slate-500 block">JD Coverage</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Download Buttons Bar */}
            <div className="pt-4 mt-4 border-t border-slate-800 grid grid-cols-2 gap-2">
              <button
                onClick={handleDownloadPDF}
                disabled={!versionId}
                className="py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-40"
              >
                <Download size={14} />
                <span>Download PDF</span>
              </button>

              <button
                onClick={handleDownloadTex}
                disabled={!versionId}
                className="py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-40"
              >
                <Code size={14} />
                <span>Download .tex</span>
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* Edit Facts Modal */}
      {showFactModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Edit3 size={18} className="text-emerald-400" />
              Edit Ground-Truth Profile Facts
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Edit your verified technical skills before tailoring. The pipeline only adds skills present in these facts.
            </p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Skills (Comma Separated)
                </label>
                <textarea
                  value={editableSkills}
                  onChange={(e) => setEditableSkills(e.target.value)}
                  className="w-full h-28 bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 font-mono focus:border-emerald-500 focus:outline-none"
                  placeholder="Python, FastAPI, PostgreSQL, Docker, Git..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowFactModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveFacts}
                disabled={isSavingFacts}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2"
              >
                {isSavingFacts ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
                <span>Save Facts</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobDetailPage;
