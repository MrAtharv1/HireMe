import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

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

  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
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

  // On mount or when token changes, refresh user info and their active profile
  useEffect(() => {
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
  }, [token]);

  const handleAuthSuccess = async (data) => {
    const { access_token, user: userData } = data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('hireme_token', access_token);
    localStorage.setItem('hireme_user', JSON.stringify(userData));

    if (userData.active_profile_id) {
      setProfileId(userData.active_profile_id);
    } else if (profileId) {
      // If user had uploaded a resume as a guest before signing in/registering, link it to this account!
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
        login,
        register,
        googleLogin,
        logout,
        isAuthModalOpen,
        setIsAuthModalOpen,
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
