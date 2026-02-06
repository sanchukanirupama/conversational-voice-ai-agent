"use client";
import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    token: null,
  });

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('admin_token');
    
    if (!token) {
      setAuthState({ isAuthenticated: false, isLoading: false, token: null });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/admin/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setAuthState({ isAuthenticated: true, isLoading: false, token });
      } else {
        localStorage.removeItem('admin_token');
        setAuthState({ isAuthenticated: false, isLoading: false, token: null });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('admin_token');
      setAuthState({ isAuthenticated: false, isLoading: false, token: null });
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('admin_token', data.access_token);
        setAuthState({ isAuthenticated: true, isLoading: false, token: data.access_token });
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('admin_token');
    setAuthState({ isAuthenticated: false, isLoading: false, token: null });
  };

  return {
    ...authState,
    login,
    logout,
    checkAuth,
  };
}
