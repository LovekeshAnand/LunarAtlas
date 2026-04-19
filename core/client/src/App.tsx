import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Header from './components/header/Header';
import Footer from './components/footer/Footer';
import HomePage from './pages/HomePage';
import DocsPage from './pages/DocsPage';
import GraphPage from './pages/GraphPage';

// Guards /docs and /graph — redirects to home if not logged in
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <>{children}</> : <Navigate to="/" replace />;
}

function AppRoutes() {
  return (
    <div className="min-h-screen bg-canvas dark:bg-[#0d0d0d] font-sans flex flex-col transition-colors duration-200">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/"      element={<HomePage />} />
          <Route path="/docs"  element={<RequireAuth><DocsPage /></RequireAuth>} />
          <Route path="/graph" element={<RequireAuth><GraphPage /></RequireAuth>} />
          <Route path="*"      element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

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