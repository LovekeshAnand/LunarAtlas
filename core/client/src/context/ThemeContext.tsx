import { createContext, useContext, useEffect, type ReactNode } from 'react';

interface ThemeContextValue {
  isDark: boolean;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  isDark: false,
  toggle: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const isDark = false;
  const toggle = () => {};

  useEffect(() => {
    try {
      localStorage.removeItem('luna-theme');
      document.documentElement.classList.remove('dark');
    } catch { /* ignore in restricted environments */ }
  }, []);

  return (
    <ThemeContext.Provider value={{ isDark, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  return useContext(ThemeContext);
}
