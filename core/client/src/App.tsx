import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Header from './components/header/Header';
import Footer from './components/footer/Footer';
import HomePage from './pages/HomePage';
import DocsPage from './pages/DocsPage';
import SpectralAnalyzerPage from './pages/SpectralAnalyzerPage';
import HealthPage from './pages/HealthPage';

import DashboardPage from './pages/DashboardPage';
import DeveloperApiPage from './pages/DeveloperApiPage';

/**
 * @fileoverview Root Application Component for LunarAtlas.
 * Entry point for theme, authentication, and routing logic.
 */

/**
 * Higher-Order Component to guard protected routes (Docs, Graph, Dashboard).
 * Intercepts unauthenticated access and redirects to the landing page.
 */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <>{children}</> : <Navigate to="/" replace />;
}

/**
 * Main Routing Engine.
 * Implements a single-page application (SPA) layout with persistent Header and Footer.
 */
function AppRoutes() {
  return (
    <div className="min-h-screen bg-canvas dark:bg-[#0d0d0d] font-sans flex flex-col transition-colors duration-200">
      <Header />
      <main className="flex-1">
        <Routes>
          {/* Landing / Introduction Page */}
          <Route path="/"      element={<HomePage />} />
          
          {/* Scientific Documentation & Context */}
          <Route path="/docs"  element={<DocsPage />} />
          

          
          {/* Primary Spectral Analysis Dashboard */}
          <Route path="/analyzer" element={<RequireAuth><SpectralAnalyzerPage /></RequireAuth>} />

          {/* Standalone Developer API Portal */}
          <Route path="/developers" element={<DeveloperApiPage />} />

          {/* User Dashboard & API Key Portal */}
          <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
          
          {/* System Status Dashboard (Ping Monitor-able) */}
          <Route path="/health" element={<HealthPage />} />

          {/* Catch-all redirect to Landing */}
          <Route path="*"      element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}

/**
 * Root Application Shell.
 * Provides global contexts for theming and ISRO-compliant authentication simulation.
 */
function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;