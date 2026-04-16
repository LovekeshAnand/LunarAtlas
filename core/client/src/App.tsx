import { type ReactNode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import HomePage from './pages/HomePage';
import GraphPage from './pages/GraphPage';
import DocsPage from './pages/DocsPage';
import PaperPage from './pages/PaperPage';

// ─────────────────────────────────────────────────────────────────
// App.tsx  (updated)
// Defines the client-side route tree.
// /graph is protected — unauthenticated users are sent to /.
// ─────────────────────────────────────────────────────────────────

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      <Route
        path="/graph"
        element={
          <ProtectedRoute>
            <GraphPage />
          </ProtectedRoute>
        }
      />

      <Route path="/docs" element={<DocsPage />} />

      <Route path="/paper" element={<PaperPage />} />

      {/* Catch-all → home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;