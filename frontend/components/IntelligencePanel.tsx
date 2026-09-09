'use client';
import { useState, useEffect } from 'react';

const DataStateBadge = ({ state }: { state: string }) => {
  const colors: Record<string, string> = {
    LIVE: 'bg-green-100 text-green-800',
    HISTORICAL: 'bg-blue-100 text-blue-800',
    DEMO: 'bg-yellow-100 text-yellow-800',
    PARTIAL: 'bg-orange-100 text-orange-800',
    UNAVAILABLE: 'bg-gray-100 text-gray-800',
    ERROR: 'bg-red-100 text-red-800',
  };
  return <span className={`px-2 py-1 rounded text-xs font-semibold ${colors[state] || 'bg-gray-100'}`}>{state}</span>;
};

export default function IntelligencePanel({ locationId }: { locationId: number }) {
  const [data, setData] = useState<any>({ risk: null, weather: null, alert: null });
  const [loading, setLoading] = useState(false);

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
      <button onClick={fetchData} className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700">Refresh Data</button>
      {loading && <p className="text-sm text-gray-500">Loading intelligence...</p>}
      
      {data.alert && (
        <section className="p-4 bg-white border border-red-200 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-bold text-red-700">Early Warning</h2>
            <DataStateBadge state={data.alert.data_state} />
          </div>
          <p className="text-2xl font-black text-red-600">{data.alert.alert_level}</p>
          <p className="text-sm mt-1">{data.alert.primary_reason}</p>
          <div className="mt-3 text-sm bg-red-50 p-2 rounded">
            <strong>Action:</strong> {data.alert.recommended_action}
          </div>
        </section>
      )}

      {data.risk && (
        <section className="p-4 bg-white border rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold">Flood Risk</h3>
            <DataStateBadge state={data.risk.data_state} />
          </div>
          <p className="text-lg font-bold">{data.risk.risk_level} ({data.risk.risk_score})</p>
        </section>
      )}

      {data.weather && (
        <section className="p-4 bg-white border rounded-lg shadow-sm">
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
