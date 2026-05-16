import { createContext, useContext, useState, useEffect } from 'react';
import { setAuthToken, getAuthToken, login, register, getProfile } from '../api';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          const profile = await getProfile();
          setUser(profile);
        } catch (e) {
          setAuthToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const handleLogin = async (username, password) => {
    const result = await login(username, password);
    setAuthToken(result.access_token);
    setUser(result.user);
    return result;
  };

  const handleRegister = async (username, email, password) => {
    const result = await register(username, email, password);
    setAuthToken(result.access_token);
    setUser(result.user);
    return result;
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
  };

  const refreshProfile = async () => {
    if (getAuthToken()) {
      const profile = await getProfile();
      setUser(profile);
    }
  };

  const hasRole = (role) => {
    return user?.roles?.includes(role) || false;
  };

  const isTrial = () => {
    return user?.is_trial_active || false;
  };

  const value = {
    user,
    loading,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshProfile,
    hasRole,
    isTrial,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
