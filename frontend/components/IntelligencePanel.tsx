'use client';
import { useState, useEffect } from 'react';
import { DataStateBadge } from './ui/DataStateBadge';

export default function IntelligencePanel({ locationId }: { locationId: number }) {
  const [data, setData] = useState<any>({ risk: null, weather: null, alert: null });
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [riskRes, weatherRes, alertRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/v1/risk/${locationId}`),
        fetch(`http://127.0.0.1:8000/api/v1/weather/${locationId}`),
        fetch(`http://127.0.0.1:8000/api/v1/alerts/${locationId}`)
      ]);
      setData({
        risk: await riskRes.json(),
        weather: await weatherRes.json(),
        alert: await alertRes.json()
      });
    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="space-y-4">
      <button onClick={fetchData} className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 dark:bg-blue-500">Refresh Data</button>
      {loading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading intelligence...</p>}
      
      {data.alert && (
        <section className="p-4 bg-white dark:bg-gray-800 border border-red-200 dark:border-red-900 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-bold text-red-700 dark:text-red-400">Early Warning</h2>
            <DataStateBadge state={data.alert.data_state} />
          </div>
          <p className="text-2xl font-black text-red-600 dark:text-red-500">{data.alert.alert_level}</p>
          <p className="text-sm mt-1">{data.alert.primary_reason}</p>
          <div className="mt-3 text-sm bg-red-50 dark:bg-red-900/20 p-2 rounded">
            <strong>Action:</strong> {data.alert.recommended_action}
          </div>
          <button onClick={() => toggleExpand('details')} className="mt-2 text-xs text-blue-600 dark:text-blue-400">
            {expanded['details'] ? 'Hide Details' : 'Show Details'}
          </button>
          {expanded['details'] && (
            <div className="mt-2 text-xs space-y-1 border-t pt-2 border-gray-200 dark:border-gray-700">
              <p>Risk Score: {data.alert.risk_score}</p>
              {data.alert.contributing_factors.map((f: any, i: number) => (
                <p key={i}>• {f.name}: {f.source}</p>
              ))}
            </div>
          )}
        </section>
      )}

      {data.risk && (
        <section className="p-4 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold">Flood Risk</h3>
            <DataStateBadge state={data.risk.data_state} />
          </div>
          <p className="text-lg font-bold">{data.risk.risk_level} ({data.risk.risk_score})</p>
        </section>
      )}

      {data.weather && (
        <section className="p-4 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold">Weather</h3>
            <DataStateBadge state={data.weather.data_state} />
          </div>
          <p>{data.weather.temperature}°C, {data.weather.weather_condition}</p>
        </section>
      )}
    </div>
  );
}
