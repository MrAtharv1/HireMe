import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Calendar, Clock, CheckCircle, XCircle, Briefcase, Loader2, AlertCircle } from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../api/client';

const ApplicationsPage = () => {
  const { profileId } = useApp();
  const navigate = useNavigate();

  const [applications, setApplications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const statuses = [
    { id: 'saved', label: 'Saved / Tailored', icon: <Clock size={16} className="mr-2 text-slate-400" /> },
    { id: 'applied', label: 'Applied', icon: <CheckCircle size={16} className="mr-2 text-brand-accent" /> },
    { id: 'interviewing', label: 'Interviewing', icon: <Briefcase size={16} className="mr-2 text-yellow-400" /> },
    { id: 'rejected', label: 'Rejected', icon: <XCircle size={16} className="mr-2 text-red-400" /> },
  ];

  useEffect(() => {
    if (!profileId) {
      navigate('/');
      return;
    }

    const fetchApplications = async () => {
      try {
        // Adjust this endpoint based on your FastAPI routes
        const response = await api.get(`/applications/${profileId}`);
        setApplications(response.data);
      } catch (err) {
        console.error(err);
        // Fallback gracefully if the endpoint isn't built yet
        if (err.response?.status === 404) {
           setApplications([]);
        } else {
           setError('Failed to load applications. Make sure your backend endpoint exists.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchApplications();
  }, [profileId, navigate]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="animate-spin text-brand-accent mb-4" size={48} />
        <p className="text-slate-400 text-lg">Loading your application pipeline...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-20 p-6 bg-red-500/10 border border-red-500/50 rounded-xl text-center">
        <AlertCircle size={48} className="mx-auto text-red-400 mb-4" />
        <p className="text-slate-400">{error}</p>
      </div>
    );
  }

  // Helper to group applications by status
  const getAppsByStatus = (statusId) => {
    return applications.filter(app => app.status === statusId);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-100 mb-2">Application Tracker</h1>
        <p className="text-slate-400">Keep tabs on every job you've tailored a resume for and applied to.</p>
      </div>

      {applications.length === 0 ? (
        <div className="text-center p-12 border-2 border-dashed border-slate-700 rounded-xl bg-brand-card">
          <Briefcase size={48} className="mx-auto text-slate-500 mb-4" />
          <h3 className="text-xl font-bold text-slate-200 mb-2">Your pipeline is empty</h3>
          <p className="text-slate-400 mb-6">You haven't saved any jobs or tailored any resumes yet.</p>
          <button 
            onClick={() => navigate('/jobs')}
            className="px-6 py-3 bg-brand-accent text-white rounded-lg font-medium hover:bg-blue-500 transition-colors"
          >
            Go Find Jobs
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statuses.map(status => (
            <div key={status.id} className="flex flex-col h-full bg-slate-900/50 rounded-xl border border-slate-800 p-4">
              {/* Column Header */}
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-700">
                <h3 className="font-bold text-slate-200 flex items-center">
                  {status.icon}
                  {status.label}
                </h3>
                <span className="bg-slate-800 text-slate-300 text-xs py-1 px-2 rounded-full font-medium">
                  {getAppsByStatus(status.id).length}
                </span>
              </div>

              {/* Application Cards */}
              <div className="space-y-4 flex-grow overflow-y-auto">
                {getAppsByStatus(status.id).map(app => (
                  <div key={app.id} className="bg-brand-card border border-slate-700 p-4 rounded-lg hover:border-brand-accent/50 cursor-pointer transition-colors" onClick={() => navigate(`/jobs/${app.job_id}`)}>
                    <h4 className="font-bold text-slate-100 mb-1">{app.job_title}</h4>
                    <p className="text-sm text-slate-400 flex items-center mb-3">
                      <Building2 size={14} className="mr-1" /> {app.company}
                    </p>
                    <div className="flex justify-between items-center text-xs text-slate-500">
                      <span className="flex items-center">
                        <Calendar size={12} className="mr-1" />
                        {new Date(app.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
                
                {getAppsByStatus(status.id).length === 0 && (
                  <div className="text-center py-8 text-slate-600 text-sm italic">
                    No applications here
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ApplicationsPage;