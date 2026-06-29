import { useState, useEffect } from 'react';

export default function HealthPage() {
  const [data, setData] = useState<string>('Loading...');

  useEffect(() => {
    const fetchHealth = async () => {
      const startedAt = Date.now();
      try {
        const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
        const cleanBase = base.replace(/\/$/, '');
        const url = `${cleanBase}/health`;

        const res = await fetch(url);
        const backend = await res.json();
        
        setData(JSON.stringify({
          status: res.ok ? 'healthy' : 'degraded',
          frontend: 'ok',
          backend,
          backendStatus: res.status,
          latencyMs: Date.now() - startedAt,
        }));
      } catch (err: any) {
        setData(JSON.stringify({
          status: 'down',
          frontend: 'ok',
          backend: null,
          error: err.message || 'Backend health check failed',
          latencyMs: Date.now() - startedAt,
        }));
      }
    };
    fetchHealth();
  }, []);

  return <pre>{data}</pre>;
}





