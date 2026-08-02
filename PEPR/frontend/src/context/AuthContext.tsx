import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE } from '../api/client';

export type UserRole = 'RESEARCHER' | 'MANAGEMENT' | 'ICT' | 'ADMIN';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, full_name: string, role: UserRole) => Promise<void>;
  forgotPassword: (email: string) => Promise<{ message: string; reset_token?: string }>;
  resetPassword: (token: string, newPassword: string, code?: string) => Promise<{ message: string }>;
  logout: () => void;
  canRunIngestion: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('pepr_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('pepr_token') || null;
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('pepr_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('pepr_user');
    }
  }, [user]);

  useEffect(() => {
    if (token) {
      localStorage.setItem('pepr_token', token);
    } else {
      localStorage.removeItem('pepr_token');
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Invalid institutional email address or password.');
    }

    const data = await response.json();
    setUser(data.user);
    setToken(data.access_token);
    localStorage.setItem('pepr_user', JSON.stringify(data.user));
    localStorage.setItem('pepr_token', data.access_token);
  };

  const signup = async (email: string, password: string, full_name: string, role: UserRole = 'RESEARCHER') => {
    const response = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name, role }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Registration failed.');
    }

    const data = await response.json();
    setUser(data.user);
    setToken(data.access_token);
    localStorage.setItem('pepr_user', JSON.stringify(data.user));
    localStorage.setItem('pepr_token', data.access_token);
  };

  const forgotPassword = async (email: string) => {
    const response = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to dispatch reset email.');
    }
    return await response.json();
  };

  const resetPassword = async (tokenStr: string, newPassword: string, code?: string) => {
    const response = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: tokenStr, new_password: newPassword, code }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to reset password.');
    }
    return await response.json();
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('pepr_user');
    localStorage.removeItem('pepr_token');
  };

  const canRunIngestion = Boolean(user && (user.role === 'ICT' || user.role === 'ADMIN'));

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(user),
        login,
        signup,
        forgotPassword,
        resetPassword,
        logout,
        canRunIngestion,
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
