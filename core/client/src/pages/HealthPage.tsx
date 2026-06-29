import { useState, useEffect } from 'react';

export default function HealthPage() {
  const [data, setData] = useState<string>('Loading...');

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
        const cleanBase = base.replace(/\/$/, '');
        const url = cleanBase.endsWith('/api/v1') 
          ? cleanBase.substring(0, cleanBase.length - 7) + '/health'
          : cleanBase + '/health';

        const res = await fetch(url);
        const json = await res.json();
        setData(JSON.stringify(json, null, 2));
      } catch (err: any) {
        setData(JSON.stringify({ status: 'degraded', error: err.message || 'Failed to fetch health' }, null, 2));
      }
    };
    fetchHealth();
  }, []);

  return <pre>{data}</pre>;
}
