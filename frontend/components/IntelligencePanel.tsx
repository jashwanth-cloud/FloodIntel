'use client';
import { useState } from 'react';

export default function IntelligencePanel({ locationId }: { locationId: number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchRisk = async () => {
    setLoading(true);
    const res = await fetch(`http://127.0.0.1:8000/api/v1/risk/${locationId}`);
    const json = await res.json();
    setData(json);
    setLoading(false);
  };

  return (
    <div className="p-4 border rounded shadow">
      <button onClick={fetchRisk} className="bg-blue-500 text-white p-2 rounded">
        Check Risk
      </button>
      {loading && <p>Loading...</p>}
      {data && (
        <div className="mt-4">
          <h2 className="font-bold">Risk Level: {data.risk_level}</h2>
          <p>Score: {data.risk_score}</p>
          <p>State: {data.data_state}</p>
        </div>
      )}
    </div>
  );
}
