import { useState, useEffect } from 'react';

export default function HealthPage() {
  const [data, setData] = useState<string>('Loading...');

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1';
        const cleanBase = base.replace(/\/$/, '');
        const url = `${cleanBase}/health`;

        const res = await fetch(url);
        const json = await res.json();
        setData(JSON.stringify(json));
      } catch (err: any) {
        setData(JSON.stringify({ status: 'degraded', error: err.message || 'Failed to fetch health' }));
      }
    };
    fetchHealth();
  }, []);

  return (
    <pre style={{ 
      margin: 0, 
      padding: '20px', 
      fontFamily: 'monospace', 
      backgroundColor: '#0d0d0d', 
      color: '#ffffff', 
      minHeight: '100vh',
      boxSizing: 'border-box',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-all'
    }}>
      {data}
    </pre>
  );
}



