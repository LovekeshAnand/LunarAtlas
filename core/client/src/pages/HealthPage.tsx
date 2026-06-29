import { useState, useEffect } from 'react';

export default function HealthPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

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
        setData(json);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch health');
      }
    };
    fetchHealth();
  }, []);

  if (error) return <div style={{ padding: '20px', fontFamily: 'monospace' }}>Error: {error}</div>;
  if (!data) return <div style={{ padding: '20px', fontFamily: 'monospace' }}>Loading...</div>;

  return (
    <pre style={{ padding: '20px', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
