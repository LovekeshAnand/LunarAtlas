import { createContext, useContext, useState, type ReactNode } from 'react';

// ─────────────────────────────────────────────────────────────────
// AuthContext.tsx
// Global authentication state — mocked (no backend).
// isAuthenticated flips to true on Sign Up form submission.
// ─────────────────────────────────────────────────────────────────

interface AuthContextType {
  isAuthenticated: boolean;
  userEmail: string;
  userInstitution: string;
  login: (email: string, institution: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [userInstitution, setUserInstitution] = useState('');

  const login = (email: string, institution: string) => {
    setIsAuthenticated(true);
    setUserEmail(email);
    setUserInstitution(institution);
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUserEmail('');
    setUserInstitution('');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userEmail, userInstitution, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
