'use client';
import { useState, useEffect } from 'react';
import { DataStateBadge } from './ui/DataStateBadge';

export default function IntelligencePanel({ locationId }: { locationId: number }) {
  const [data, setData] = useState<any>({ risk: null, weather: null, alert: null, intel: null });
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [riskRes, weatherRes, alertRes, intelRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/v1/risk/${locationId}`),
        fetch(`http://127.0.0.1:8000/api/v1/weather/${locationId}`),
        fetch(`http://127.0.0.1:8000/api/v1/alerts/${locationId}`),
        fetch(`http://127.0.0.1:8000/api/v1/intelligence/${locationId}`)
      ]);
      setData({
        risk: await riskRes.json(),
        weather: await weatherRes.json(),
        alert: await alertRes.json(),
        intel: await intelRes.json()
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
      
      {data.intel && (
        <section className="p-4 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-bold text-gray-800 dark:text-gray-200">FloodIntel AI</h2>
            <DataStateBadge state={data.intel.data_state} />
          </div>
          <p className="text-sm">{data.intel.summary}</p>
          <button onClick={() => toggleExpand('intel')} className="mt-2 text-xs text-blue-600 dark:text-blue-400">
            {expanded['intel'] ? 'Hide Details' : 'Show Details'}
          </button>
          {expanded['intel'] && (
            <div className="mt-2 text-xs space-y-1 border-t pt-2 border-gray-200 dark:border-gray-700">
              <p><strong>Severity:</strong> {data.intel.severity}</p>
              <p><strong>Recommended Actions:</strong> {data.intel.recommended_actions.join(', ')}</p>
            </div>
          )}
        </section>
      )}

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
        </section>
      )}
      {/* ... other sections ... */}
    </div>
  );
}
