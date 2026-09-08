'use client';
import { useState } from 'react';

export default function IntelligencePanel({ locationId }: { locationId: number }) {
  const [riskData, setRiskData] = useState<any>(null);
  const [weatherData, setWeatherData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchDetails = async () => {
    setLoading(true);
    const [riskRes, weatherRes] = await Promise.all([
      fetch(`http://127.0.0.1:8000/api/v1/risk/${locationId}`),
      fetch(`http://127.0.0.1:8000/api/v1/weather/${locationId}`)
    ]);
    setRiskData(await riskRes.json());
    setWeatherData(await weatherRes.json());
    setLoading(false);
  };

  return (
    <div className="p-4 border rounded shadow">
      <button onClick={fetchDetails} className="bg-blue-500 text-white p-2 rounded">
        Check Intelligence
      </button>
      {loading && <p>Loading...</p>}
      {riskData && (
        <div className="mt-4">
          <h2 className="font-bold text-xl">Risk: {riskData.risk_level}</h2>
          <p>Score: {riskData.risk_score}</p>
          <p>Model: {riskData.model_version} ({riskData.data_state})</p>
        </div>
      )}
      {weatherData && (
        <div className="mt-4 border-t pt-2">
          <h3 className="font-bold">Weather ({weatherData.data_state})</h3>
          <p>Temp: {weatherData.temperature}°C</p>
          <p>Condition: {weatherData.weather_condition}</p>
          <p>Source: {weatherData.source}</p>
        </div>
      )}
    </div>
  );
}
