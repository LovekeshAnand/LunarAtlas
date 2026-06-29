import { useEffect } from 'react';

export default function HealthPage() {
  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
    const cleanBase = base.replace(/\/$/, '');
    // If the base URL ends with /api/v1, replace it to target /health at root.
    // Otherwise fallback to root health.
    const url = cleanBase.endsWith('/api/v1') 
      ? cleanBase.substring(0, cleanBase.length - 7) + '/health'
      : cleanBase + '/health';

    window.location.replace(url);
  }, []);

  return null;
}


