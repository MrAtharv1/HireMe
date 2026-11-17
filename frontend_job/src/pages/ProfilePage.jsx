import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Briefcase,
  GraduationCap,
  Award,
  Wrench,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Save,
  Loader2,
  Plus,
  Trash2,
  Code,
  Eye,
  Copy,
  ExternalLink,
  MapPin,
  Mail,
  Phone,
  Github,
  Linkedin,
  Sparkles,
  FolderGit2,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../api/client';

const ProfilePage = () => {
  const { profileId } = useApp();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('visual'); // 'visual' | 'json'
  const [profileData, setProfileData] = useState({
    personal_info: {
      name: '',
      email: '',
      phone: '',
      location: '',
      linkedin: '',
      github: '',
      portfolio: '',
      summary: '',
    },
    skills: [],
    education: [],
    experience: [],
    projects: [],
    certifications: [],
    achievements: [],
  });

  const [newSkillInput, setNewSkillInput] = useState('');
  const [newCertInput, setNewCertInput] = useState('');
  const [newAchInput, setNewAchInput] = useState('');
  const [jsonString, setJsonString] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!profileId) {
      navigate('/');
      return;
    }

    const fetchProfile = async () => {
      try {
        const response = await api.get(`/profiles/${profileId}`);
        const raw = response.data?.data?.parsed_json || response.data?.parsed_json || {};
        
        const normalized = {
          personal_info: {
            name: raw.personal_info?.name || raw.name || '',
            email: raw.personal_info?.email || raw.email || '',
            phone: raw.personal_info?.phone || raw.phone || '',
            location: raw.personal_info?.location || raw.location || '',
            linkedin: raw.personal_info?.linkedin || raw.linkedin || '',
            github: raw.personal_info?.github || raw.github || '',
            portfolio: raw.personal_info?.portfolio || raw.portfolio || '',
            summary: raw.personal_info?.summary || raw.summary || '',
          },
          skills: Array.isArray(raw.skills) ? raw.skills : [],
          education: Array.isArray(raw.education) ? raw.education : [],
          experience: Array.isArray(raw.experience) ? raw.experience : [],
          projects: Array.isArray(raw.projects) ? raw.projects : [],
          certifications: Array.isArray(raw.certifications) ? raw.certifications : [],
          achievements: Array.isArray(raw.achievements) ? raw.achievements : [],
        };

        setProfileData(normalized);
        setJsonString(JSON.stringify(normalized, null, 2));
      } catch (err) {
        console.error('Failed to load profile data:', err);
        setError('Failed to load your profile. Please check that the server is running.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [profileId, navigate]);

  const handleVisualDataChange = (updated) => {
    setProfileData(updated);
    setJsonString(JSON.stringify(updated, null, 2));
  };

  const handleJsonChange = (newVal) => {
    setJsonString(newVal);
    try {
      const parsed = JSON.parse(newVal);
      setProfileData(parsed);
      setError(null);
    } catch {
      // Allow user to type JSON without prematurely failing
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    setError(null);

    let payload = profileData;
    if (activeTab === 'json') {
      try {
        payload = JSON.parse(jsonString);
      } catch (err) {
        setError('Invalid JSON format. Please check for missing brackets, commas, or quotes.');
        setIsSaving(false);
        return;
      }
    }

    try {
      await api.patch(`/profiles/${profileId}`, {
        parsed_json: payload,
      });

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3500);
    } catch (err) {
      console.error('Save failed:', err);
      setError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  // Helper additions / removals
  const addSkill = () => {
    const val = newSkillInput.trim();
    if (val && !profileData.skills.includes(val)) {
      handleVisualDataChange({
        ...profileData,
        skills: [...profileData.skills, val],
      });
      setNewSkillInput('');
    }
  };

  const removeSkill = (skillToRemove) => {
    handleVisualDataChange({
      ...profileData,
      skills: profileData.skills.filter((s) => s !== skillToRemove),
    });
  };

  const addCertification = () => {
    const val = newCertInput.trim();
    if (val && !profileData.certifications.includes(val)) {
      handleVisualDataChange({
        ...profileData,
        certifications: [...profileData.certifications, val],
      });
      setNewCertInput('');
    }
  };

  const removeCertification = (index) => {
    const updated = [...profileData.certifications];
    updated.splice(index, 1);
    handleVisualDataChange({ ...profileData, certifications: updated });
  };

  const addAchievement = () => {
    const val = newAchInput.trim();
    if (val && !profileData.achievements.includes(val)) {
      handleVisualDataChange({
        ...profileData,
        achievements: [...profileData.achievements, val],
      });
      setNewAchInput('');
    }
  };

  const removeAchievement = (index) => {
    const updated = [...profileData.achievements];
    updated.splice(index, 1);
    handleVisualDataChange({ ...profileData, achievements: updated });
  };

  const updateExperienceBullet = (expIndex, bulletIndex, newText) => {
    const expCopy = [...profileData.experience];
    expCopy[expIndex].bullets[bulletIndex] = newText;
    handleVisualDataChange({ ...profileData, experience: expCopy });
  };

  const addExperienceBullet = (expIndex) => {
    const expCopy = [...profileData.experience];
    if (!expCopy[expIndex].bullets) expCopy[expIndex].bullets = [];
    expCopy[expIndex].bullets.push('Developed feature with measurable impact.');
    handleVisualDataChange({ ...profileData, experience: expCopy });
  };

  const removeExperienceBullet = (expIndex, bulletIndex) => {
    const expCopy = [...profileData.experience];
    expCopy[expIndex].bullets.splice(bulletIndex, 1);
    handleVisualDataChange({ ...profileData, experience: expCopy });
  };

  const updateProjectBullet = (projIndex, bulletIndex, newText) => {
    const projCopy = [...profileData.projects];
    projCopy[projIndex].bullets[bulletIndex] = newText;
    handleVisualDataChange({ ...profileData, projects: projCopy });
  };

  const addProjectBullet = (projIndex) => {
    const projCopy = [...profileData.projects];
    if (!projCopy[projIndex].bullets) projCopy[projIndex].bullets = [];
    projCopy[projIndex].bullets.push('Implemented component using best practices.');
    handleVisualDataChange({ ...profileData, projects: projCopy });
  };

  const removeProjectBullet = (projIndex, bulletIndex) => {
    const projCopy = [...profileData.projects];
    projCopy[projIndex].bullets.splice(bulletIndex, 1);
    handleVisualDataChange({ ...profileData, projects: projCopy });
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-brand-accent mb-4" size={48} />
        <p className="text-slate-400 font-medium">Loading your verified profile & facts...</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-brand-accent/10 border border-brand-accent/30 rounded-xl text-brand-accent">
              <ShieldCheck size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                Candidate Profile & Facts Store
              </h1>
              <p className="text-sm text-slate-400">
                Single source of truth for your resume facts. The tailoring engine uses this exact data with <strong className="text-slate-200">zero metric or tool fabrication</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {/* Tab Switcher */}
          <div className="bg-slate-900 border border-slate-700/80 p-1 rounded-xl flex items-center gap-1">
            <button
              onClick={() => setActiveTab('visual')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'visual'
                  ? 'bg-brand-accent text-slate-900 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye size={14} />
              Visual Studio
            </button>
            <button
              onClick={() => setActiveTab('json')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'json'
                  ? 'bg-brand-accent text-slate-900 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code size={14} />
              JSON View
            </button>
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/10 disabled:opacity-50"
          >
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {isSaving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="mb-6 bg-red-500/10 border border-red-500/30 p-4 rounded-xl text-red-400 text-sm flex items-center gap-3">
          <AlertCircle size={18} className="flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {saveSuccess && (
        <div className="mb-6 bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-xl text-emerald-400 text-sm flex items-center gap-3 animate-fade-in">
          <CheckCircle2 size={18} className="flex-shrink-0" />
          <span>Profile facts updated successfully! Any newly tailored resumes and matches will reflect these facts.</span>
        </div>
      )}

      {/* Main Tab Content */}
      {activeTab === 'visual' ? (
        <div className="space-y-8">
          {/* 1. Personal & Contact Information */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <User size={18} className="text-brand-accent" />
              Personal & Contact Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  value={profileData.personal_info.name}
                  onChange={(e) =>
                    handleVisualDataChange({
                      ...profileData,
                      personal_info: { ...profileData.personal_info, name: e.target.value },
                    })
                  }
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                  placeholder="e.g. Arjun Sharma"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="email"
                    value={profileData.personal_info.email}
                    onChange={(e) =>
                      handleVisualDataChange({
                        ...profileData,
                        personal_info: { ...profileData.personal_info, email: e.target.value },
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                    placeholder="e.g. arjun@example.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="text"
                    value={profileData.personal_info.phone}
                    onChange={(e) =>
                      handleVisualDataChange({
                        ...profileData,
                        personal_info: { ...profileData.personal_info, phone: e.target.value },
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                    placeholder="e.g. +91 9876543210"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Location
                </label>
                <div className="relative">
                  <MapPin size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="text"
                    value={profileData.personal_info.location}
                    onChange={(e) =>
                      handleVisualDataChange({
                        ...profileData,
                        personal_info: { ...profileData.personal_info, location: e.target.value },
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                    placeholder="e.g. Bengaluru, India"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  LinkedIn URL
                </label>
                <div className="relative">
                  <Linkedin size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="url"
                    value={profileData.personal_info.linkedin}
                    onChange={(e) =>
                      handleVisualDataChange({
                        ...profileData,
                        personal_info: { ...profileData.personal_info, linkedin: e.target.value },
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                    placeholder="https://linkedin.com/in/username"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  GitHub URL
                </label>
                <div className="relative">
                  <Github size={16} className="absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="url"
                    value={profileData.personal_info.github}
                    onChange={(e) =>
                      handleVisualDataChange({
                        ...profileData,
                        personal_info: { ...profileData.personal_info, github: e.target.value },
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
                    placeholder="https://github.com/username"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 2. Technical Skills Badge Studio */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <Wrench size={18} className="text-brand-accent" />
                  Verified Technical Skills ({profileData.skills.length})
                </h2>
                <p className="text-xs text-slate-400">
                  Skills you add here are authorized for keyword matching and resume categorization.
                </p>
              </div>
            </div>

            {/* Badges container */}
            <div className="flex flex-wrap gap-2 mb-4 p-4 bg-slate-950/70 border border-slate-800/80 rounded-xl min-h-[70px] items-center">
              {profileData.skills.length === 0 && (
                <span className="text-xs text-slate-500 italic">No skills listed yet. Add your core languages and frameworks below.</span>
              )}
              {profileData.skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-200 border border-slate-700 hover:border-red-500/50 hover:bg-slate-800/80 transition-all"
                >
                  <span>{skill}</span>
                  <button
                    type="button"
                    onClick={() => removeSkill(skill)}
                    className="text-slate-400 hover:text-red-400 transition-colors ml-0.5"
                    title={`Remove ${skill}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            {/* Quick add bar */}
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                placeholder="Type a skill (e.g. Python, Docker, PostgreSQL) and hit Enter"
                className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-accent transition-colors"
              />
              <button
                type="button"
                onClick={addSkill}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Plus size={14} /> Add Skill
              </button>
            </div>
          </div>

          {/* 3. Work Experience */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <Briefcase size={18} className="text-brand-accent" />
              Work & Internship Experience
            </h2>

            {profileData.experience.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No experience entries found in resume.</p>
            ) : (
              <div className="space-y-6">
                {profileData.experience.map((exp, expIdx) => (
                  <div key={expIdx} className="bg-slate-950/70 border border-slate-800 rounded-xl p-5">
                    <div className="flex flex-col md:flex-row md:items-center justify-between mb-3 gap-1">
                      <div>
                        <h3 className="font-bold text-slate-200 text-sm">{exp.role || 'Role'}</h3>
                        <p className="text-xs text-brand-accent font-medium">{exp.company || 'Company'} • {exp.location || 'Location'}</p>
                      </div>
                      <span className="text-xs text-slate-400 font-mono bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800 self-start md:self-auto">
                        {exp.dates || 'Dates'}
                      </span>
                    </div>

                    {/* Bullets */}
                    <div className="space-y-2.5 mt-3 pt-3 border-t border-slate-800/80">
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Fact Bullets ({exp.bullets?.length || 0})
                      </label>
                      {(exp.bullets || []).map((bullet, bIdx) => (
                        <div key={bIdx} className="flex items-start gap-2">
                          <textarea
                            rows={2}
                            value={bullet}
                            onChange={(e) => updateExperienceBullet(expIdx, bIdx, e.target.value)}
                            className="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-brand-accent leading-relaxed resize-y"
                          />
                          <button
                            type="button"
                            onClick={() => removeExperienceBullet(expIdx, bIdx)}
                            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors mt-1"
                            title="Delete bullet"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => addExperienceBullet(expIdx)}
                        className="text-xs text-brand-accent hover:underline flex items-center gap-1 font-semibold pt-1"
                      >
                        <Plus size={12} /> Add bullet point
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4. Projects */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
              <FolderGit2 size={18} className="text-brand-accent" />
              Technical Projects
            </h2>

            {profileData.projects.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No projects found in resume.</p>
            ) : (
              <div className="space-y-6">
                {profileData.projects.map((proj, pIdx) => (
                  <div key={pIdx} className="bg-slate-950/70 border border-slate-800 rounded-xl p-5">
                    <div className="flex flex-col md:flex-row md:items-center justify-between mb-3 gap-1">
                      <div>
                        <h3 className="font-bold text-slate-200 text-sm">{proj.name || 'Project Name'}</h3>
                        <p className="text-xs text-slate-400 font-mono mt-0.5">
                          Tech: {Array.isArray(proj.technologies) ? proj.technologies.join(', ') : proj.technologies || 'N/A'}
                        </p>
                      </div>
                      <span className="text-xs text-slate-400 font-mono bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800 self-start md:self-auto">
                        {proj.dates || 'Dates'}
                      </span>
                    </div>

                    {/* Bullets */}
                    <div className="space-y-2.5 mt-3 pt-3 border-t border-slate-800/80">
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Fact Bullets ({proj.bullets?.length || 0})
                      </label>
                      {(proj.bullets || []).map((bullet, bIdx) => (
                        <div key={bIdx} className="flex items-start gap-2">
                          <textarea
                            rows={2}
                            value={bullet}
                            onChange={(e) => updateProjectBullet(pIdx, bIdx, e.target.value)}
                            className="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-brand-accent leading-relaxed resize-y"
                          />
                          <button
                            type="button"
                            onClick={() => removeProjectBullet(pIdx, bIdx)}
                            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors mt-1"
                            title="Delete bullet"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => addProjectBullet(pIdx)}
                        className="text-xs text-brand-accent hover:underline flex items-center gap-1 font-semibold pt-1"
                      >
                        <Plus size={12} /> Add project bullet
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 5. Education, Certifications & Achievements */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Certifications */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-3 pb-2 border-b border-slate-800">
                <Award size={16} className="text-brand-accent" />
                Certifications ({profileData.certifications.length})
              </h2>
              <div className="space-y-2 mb-4">
                {profileData.certifications.map((cert, cIdx) => (
                  <div key={cIdx} className="flex items-center justify-between bg-slate-950 px-3 py-2 rounded-lg border border-slate-800 text-xs text-slate-200">
                    <span>{cert}</span>
                    <button type="button" onClick={() => removeCertification(cIdx)} className="text-slate-500 hover:text-red-400 ml-2">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newCertInput}
                  onChange={(e) => setNewCertInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCertification())}
                  placeholder="e.g. AWS Certified Cloud Practitioner"
                  className="flex-1 bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-accent"
                />
                <button type="button" onClick={addCertification} className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold">
                  <Plus size={13} />
                </button>
              </div>
            </div>

            {/* Achievements */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-3 pb-2 border-b border-slate-800">
                <Sparkles size={16} className="text-brand-accent" />
                Achievements ({profileData.achievements.length})
              </h2>
              <div className="space-y-2 mb-4">
                {profileData.achievements.map((ach, aIdx) => (
                  <div key={aIdx} className="flex items-center justify-between bg-slate-950 px-3 py-2 rounded-lg border border-slate-800 text-xs text-slate-200">
                    <span className="truncate">{ach}</span>
                    <button type="button" onClick={() => removeAchievement(aIdx)} className="text-slate-500 hover:text-red-400 ml-2 flex-shrink-0">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newAchInput}
                  onChange={(e) => setNewAchInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAchievement())}
                  placeholder="e.g. Finalist in Hackathon 2024"
                  className="flex-1 bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-accent"
                />
                <button type="button" onClick={addAchievement} className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold">
                  <Plus size={13} />
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Raw JSON Editor Tab (Developer / Power-User Mode) */
        <div className="bg-slate-900 border border-slate-700/80 rounded-2xl overflow-hidden shadow-2xl">
          <div className="bg-slate-800/80 px-4 py-3 flex items-center justify-between border-b border-slate-700">
            <div className="flex items-center text-slate-300 font-mono text-xs">
              <Code size={14} className="mr-2 text-brand-accent" />
              candidate_facts.json
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(jsonString);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="text-xs text-slate-300 hover:text-white px-2.5 py-1 bg-slate-700/60 hover:bg-slate-700 rounded-md transition-colors flex items-center gap-1"
              >
                <Copy size={12} /> {copied ? 'Copied!' : 'Copy'}
              </button>
              <button
                type="button"
                onClick={() => {
                  try {
                    const parsed = JSON.parse(jsonString);
                    setJsonString(JSON.stringify(parsed, null, 2));
                  } catch {}
                }}
                className="text-xs text-slate-300 hover:text-white px-2.5 py-1 bg-slate-700/60 hover:bg-slate-700 rounded-md transition-colors"
              >
                Format JSON
              </button>
            </div>
          </div>

          <textarea
            value={jsonString}
            onChange={(e) => handleJsonChange(e.target.value)}
            className="w-full h-[620px] bg-slate-950 text-slate-200 p-6 font-mono text-xs leading-relaxed focus:outline-none focus:ring-inset focus:ring-1 focus:ring-brand-accent/50 resize-y"
            spellCheck="false"
          />
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
