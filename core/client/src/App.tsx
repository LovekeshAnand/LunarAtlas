import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Header from './components/header/Header';
import Footer from './components/footer/Footer';
import HomePage from './pages/HomePage';
import DocsPage from './pages/DocsPage';
import GraphPage from './pages/GraphPage';
import './App.css';

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

// Guards /docs and /graph — redirects to home if not logged in
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <>{children}</> : <Navigate to="/" replace />;
}

function AppRoutes() {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#ffffff',
        fontFamily: F,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Header />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/docs" element={<RequireAuth><DocsPage /></RequireAuth>} />
          <Route path="/graph" element={<RequireAuth><GraphPage /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;