import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';
import { DEMO_PROFILE_ID, DEMO_USER, DEMO_USER_ID } from '../data/demoData';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('hireme_token') || null);
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('hireme_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [profileId, setProfileIdState] = useState(() => {
    return localStorage.getItem('hireme_profile_id') || null;
  });

  const [isDemoMode, setIsDemoMode] = useState(() => {
    try {
      return localStorage.getItem('hireme_demo_mode') === 'true';
    } catch {
      return false;
    }
  });

  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login'); // 'login' | 'register'
  const [authError, setAuthError] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(false);

  // Sync profileId to localStorage whenever it changes
  const setProfileId = (id) => {
    setProfileIdState(id);
    if (id) {
      localStorage.setItem('hireme_profile_id', id);
    } else {
      localStorage.removeItem('hireme_profile_id');
    }
  };

  // Open the auth modal in a specific mode ('login' or 'register')
  const openAuthModal = (mode = 'login') => {
    setAuthModalMode(mode);
    setAuthError(null);
    setIsAuthModalOpen(true);
  };

  // Enter instant client-side demo mode
  const enterDemoMode = () => {
    setIsDemoMode(true);
    localStorage.setItem('hireme_demo_mode', 'true');
    setProfileId(DEMO_PROFILE_ID);
    setUser(DEMO_USER);
    localStorage.setItem('hireme_user', JSON.stringify(DEMO_USER));
    setIsAuthModalOpen(false);
    setAuthError(null);
  };

  // Exit instant demo mode
  const exitDemoMode = () => {
    setIsDemoMode(false);
    localStorage.removeItem('hireme_demo_mode');
    if (profileId === DEMO_PROFILE_ID) {
      setProfileId(null);
    }
    if (user?.id === DEMO_USER_ID || user?.email === DEMO_USER.email) {
      setUser(null);
      localStorage.removeItem('hireme_user');
      localStorage.removeItem('hireme_token');
    }
  };

  // On mount or when token changes, refresh user info and their active profile
  useEffect(() => {
    if (isDemoMode) {
      // In demo mode, preserve demo profile and mock user without remote network trip
      if (!profileId) setProfileId(DEMO_PROFILE_ID);
      if (!user) setUser(DEMO_USER);
      return;
    }

    if (!token) return;

    const fetchMe = async () => {
      try {
        const response = await api.get('/auth/me');
        const userData = response.data;
        setUser(userData);
        localStorage.setItem('hireme_user', JSON.stringify(userData));

        if (userData.active_profile_id && !profileId) {
          setProfileId(userData.active_profile_id);
        }
      } catch (err) {
        console.error('Failed to verify session:', err);
        // If token rejected, clean up
        if (err.response?.status === 401) {
          logout();
        }
      }
    };

    fetchMe();
  }, [token, isDemoMode]);

  const handleAuthSuccess = async (data) => {
    const { access_token, user: userData } = data;
    // Clear demo mode upon real account authentication
    setIsDemoMode(false);
    localStorage.removeItem('hireme_demo_mode');

    setToken(access_token);
    setUser(userData);
    localStorage.setItem('hireme_token', access_token);
    localStorage.setItem('hireme_user', JSON.stringify(userData));

    if (userData.active_profile_id) {
      setProfileId(userData.active_profile_id);
    } else if (profileId && profileId !== DEMO_PROFILE_ID) {
      // Link guest profile to authenticated account
      try {
        await api.post(`/profiles/${profileId}/claim`);
      } catch (err) {
        console.warn('Auto-claiming guest profile failed or already assigned:', err);
      }
    }

    setAuthError(null);
    setIsAuthModalOpen(false);
  };

  const login = async (email, password) => {
    setIsAuthLoading(true);
    setAuthError(null);
    try {
      const response = await api.post('/auth/login', { email, password });
      handleAuthSuccess(response.data);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Invalid email or password.';
      setAuthError(message);
      return { success: false, error: message };
    } finally {
      setIsAuthLoading(false);
    }
  };

  const register = async (email, password, fullName) => {
    setIsAuthLoading(true);
    setAuthError(null);
    try {
      const response = await api.post('/auth/register', {
        email,
        password,
        full_name: fullName,
      });
      handleAuthSuccess(response.data);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create account.';
      setAuthError(message);
      return { success: false, error: message };
    } finally {
      setIsAuthLoading(false);
    }
  };

  const googleLogin = async (credential) => {
    setIsAuthLoading(true);
    setAuthError(null);
    try {
      const response = await api.post('/auth/google', { credential });
      handleAuthSuccess(response.data);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Google sign-in failed.';
      setAuthError(message);
      return { success: false, error: message };
    } finally {
      setIsAuthLoading(false);
    }
  };

  const logout = () => {
    exitDemoMode();
    setToken(null);
    setUser(null);
    localStorage.removeItem('hireme_token');
    localStorage.removeItem('hireme_user');
  };

  return (
    <AppContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!user,
        profileId,
        setProfileId,
        isDemoMode,
        enterDemoMode,
        exitDemoMode,
        login,
        register,
        googleLogin,
        logout,
        isAuthModalOpen,
        setIsAuthModalOpen,
        authModalMode,
        setAuthModalMode,
        openAuthModal,
        authError,
        setAuthError,
        isAuthLoading,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
