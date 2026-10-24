import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, setAccessToken, clearAuthSession, refreshAuthToken } from '../api/client';

export interface User {
  id: string | number;
  email: string;
  fullName?: string;
  firstName?: string;
  lastName?: string;
  role: 'PASSENGER' | 'ADMIN' | 'OPERATOR' | 'AUDITOR' | string;
  phone?: string;
  status?: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: {
    email: string;
    password: string;
    fullName?: string;
    firstName: string;
    lastName: string;
    phone?: string;
  }) => Promise<User>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = useCallback(async (): Promise<User | null> => {
    try {
      // First try /auth/me, fallback to /users/me
      const data = await apiClient<User>('/auth/me');
      setUser(data);
      return data;
    } catch {
      try {
        const data = await apiClient<User>('/users/me');
        setUser(data);
        return data;
      } catch {
        clearAuthSession();
        setUser(null);
        return null;
      }
    }
  }, []);

  // On app startup, try silent token refresh from HttpOnly cookie
  useEffect(() => {
    let mounted = true;

    async function initSession() {
      try {
        const token = await refreshAuthToken();
        if (token && mounted) {
          await fetchProfile();
        }
      } catch {
        if (mounted) {
          clearAuthSession();
          setUser(null);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    initSession();

    return () => {
      mounted = false;
    };
  }, [fetchProfile]);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      const resp = await apiClient<{ accessToken: string; user?: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      setAccessToken(resp.accessToken);

      let currentUser: User | null = resp.user || null;
      if (!currentUser) {
        currentUser = await fetchProfile();
      } else {
        setUser(currentUser);
      }

      if (!currentUser) {
        throw new Error('Unable to retrieve user profile after login.');
      }

      return currentUser;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: {
    email: string;
    password: string;
    fullName?: string;
    firstName: string;
    lastName: string;
    phone?: string;
  }): Promise<User> => {
    setIsLoading(true);
    try {
      const resp = await apiClient<{ accessToken: string; user?: User }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      setAccessToken(resp.accessToken);

      let currentUser: User | null = resp.user || null;
      if (!currentUser) {
        currentUser = await fetchProfile();
      } else {
        setUser(currentUser);
      }

      if (!currentUser) {
        throw new Error('Unable to retrieve user profile after registration.');
      }

      return currentUser;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient('/auth/logout', { method: 'POST' });
    } catch {
      // ignore network errors on logout
    } finally {
      clearAuthSession();
      setUser(null);
    }
  };

  const refreshProfile = async () => {
    await fetchProfile();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
