import axios from 'axios';
import {
  DEMO_PROFILE_ID,
  DEMO_USER_ID,
  DEMO_VERSION_ID,
  DEMO_USER,
  DEMO_CANDIDATE_PROFILE,
  DEMO_JOBS_LIST,
  DEMO_TAILORED_RESULT,
  DEMO_LATEX_SOURCE,
  DEMO_APPLICATIONS_LIST,
} from '../data/demoData';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create an Axios instance locked to your FastAPI backend
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Checks whether the user is currently exploring Instant Demo Mode.
 */
export const isDemoModeActive = () => {
  try {
    return localStorage.getItem('hireme_demo_mode') === 'true';
  } catch {
    return false;
  }
};

/**
 * High-fidelity client-side adapter for Instant Demo Mode.
 * Intercepts requests and simulates sub-100ms realistic backend responses
 * with zero network calls, zero LLM cost, and zero authentication gating.
 */
const demoModeAdapter = async (config) => {
  // Simulate an ultra-responsive native transition (60-90ms)
  await new Promise((resolve) => setTimeout(resolve, 75));

  let cleanUrl = config.url || '';
  if (config.baseURL && cleanUrl.startsWith(config.baseURL)) {
    cleanUrl = cleanUrl.slice(config.baseURL.length);
  }
  const [pathname] = cleanUrl.split('?');
  const path = pathname.startsWith('/') ? pathname : `/${pathname}`;
  const method = (config.method || 'get').toLowerCase();

  // Helper response wrapper matching Axios standard shape
  const makeResponse = (data, status = 200, extraHeaders = {}) => ({
    data,
    status,
    statusText: status === 200 || status === 201 ? 'OK' : 'Error',
    headers: { 'content-type': 'application/json', ...extraHeaders },
    config,
  });

  // 1. Job Recommendations & Feed
  if (path.startsWith('/jobs/recommended') || path.startsWith('/jobs/recommendations')) {
    return makeResponse(DEMO_JOBS_LIST);
  }

  // 2. Job Ingest / Refresh Feed
  if (path.startsWith('/jobs/ingest')) {
    return makeResponse({
      message: 'Synced 15 verified fresher jobs (Instant Demo)',
      added: 15,
      skipped: 0,
      total: 15,
    });
  }

  // 3. Single Job Detail
  if (path.startsWith('/jobs/')) {
    const requestedId = path.replace('/jobs/', '');
    const foundJob = DEMO_JOBS_LIST.find((j) => j.id === requestedId) || DEMO_JOBS_LIST[0];
    return makeResponse({
      ...foundJob,
      match_score: foundJob.match_percent,
      match_reasons: [
        `Strong overlap in ${foundJob.matched_skills.slice(0, 3).join(', ')}`,
        'Verified early-career 0-2 years experience requirement',
        'Direct ATS board integration',
      ],
      requirements: foundJob.description,
    });
  }

  // 4. Resume Upload
  if (path.startsWith('/resume/upload')) {
    return makeResponse(
      {
        profile_id: DEMO_PROFILE_ID,
        parsed_resume: DEMO_CANDIDATE_PROFILE,
        raw_text_length: 1850,
        extraction_method: 'demo_instant',
      },
      201
    );
  }

  // 5. Tailor Resume (Minimal-Edit LLM Funnel Simulation)
  if (path.startsWith('/resume/tailor')) {
    return makeResponse(DEMO_TAILORED_RESULT);
  }

  // 6. Recompile Resume (Bullet Accept/Revert Toggle)
  if (path.includes('/recompile')) {
    return makeResponse({
      version_id: DEMO_VERSION_ID,
      ats_score: 91,
      fidelity_score: 100,
      message: 'Recompiled tailored resume successfully (Demo Mode)',
    });
  }

  // 7. Download or Preview Tailored PDF
  if (path.includes('/pdf')) {
    try {
      const response = await fetch('/demo_tailored_resume.pdf');
      const blob = await response.blob();
      return makeResponse(blob, 200, { 'content-type': 'application/pdf' });
    } catch {
      // Fallback in case of fetch environment issues
      const fallbackBlob = new Blob(['%PDF-1.4 demo tailored resume'], { type: 'application/pdf' });
      return makeResponse(fallbackBlob, 200, { 'content-type': 'application/pdf' });
    }
  }

  // 8. Download or View LaTeX Source
  if (path.includes('/tex')) {
    return makeResponse(DEMO_LATEX_SOURCE, 200, { 'content-type': 'text/plain' });
  }

  // 9. Profile Retrieval and Updates
  if (path.startsWith('/resume/profile') || path.startsWith('/profiles')) {
    if (path.includes('/claim')) {
      return makeResponse({ success: true, message: 'Profile claimed (Demo Mode)' });
    }
    if (method === 'put') {
      return makeResponse({
        success: true,
        message: 'Profile facts saved successfully (Demo Mode)',
        data: {
          id: DEMO_PROFILE_ID,
          user_id: DEMO_USER_ID,
          parsed_json: DEMO_CANDIDATE_PROFILE,
        },
      });
    }
    return makeResponse({
      success: true,
      message: 'OK',
      data: {
        id: DEMO_PROFILE_ID,
        user_id: DEMO_USER_ID,
        parsed_json: DEMO_CANDIDATE_PROFILE,
      },
      parsed_json: DEMO_CANDIDATE_PROFILE,
    });
  }

  // 10. Application Tracking
  if (path.startsWith('/applications/apply')) {
    return makeResponse({
      success: true,
      message: 'Job application saved to tracker (Demo Mode)',
      application_id: 'demo-app-new',
    });
  }

  if (path.startsWith('/applications')) {
    return makeResponse(DEMO_APPLICATIONS_LIST);
  }

  // 11. Auth Session Check in Demo Mode
  if (path.startsWith('/auth/me')) {
    return makeResponse(DEMO_USER);
  }

  // Default fallback mock
  return makeResponse({ success: true, message: 'OK (Demo Mode)' });
};

// Request interceptor: attaches demo adapter or JWT Bearer token
api.interceptors.request.use(
  (config) => {
    if (isDemoModeActive()) {
      // Direct all demo requests through our client-side zero-latency mock adapter
      config.adapter = demoModeAdapter;
      return config;
    }

    const token = localStorage.getItem('hireme_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: automatically handles expired session tokens
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (localStorage.getItem('hireme_token')) {
        console.warn('Session expired. Clearing stored token.');
        localStorage.removeItem('hireme_token');
        localStorage.removeItem('hireme_user');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
