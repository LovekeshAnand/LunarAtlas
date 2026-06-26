import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { apiService } from '../services/apiService';

export interface AuthUser {
  id: number;
  email: string;
  username?: string;
  institution: string;
  interest: string;
  role: string;
  created_at: string;
  api_key_count: number;
}

interface AuthContextValue {
  isLoggedIn: boolean;
  user: AuthUser | null;
  setUser: (user: AuthUser | null) => void;
  login: (access_token: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  isLoggedIn: false,
  user: null,
  setUser: () => {},
  login: async () => {},
  logout: () => {},
  loading: true
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const u = await apiService.fetchMe();
          setUser(u);
        } catch (e) {
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (access_token: string) => {
    localStorage.setItem('access_token', access_token);
    try {
      const u = await apiService.fetchMe();
      setUser(u);
    } catch {
      localStorage.removeItem('access_token');
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isLoggedIn: !!user, user, setUser, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
