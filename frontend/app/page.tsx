import MapComponent from '../components/MapComponent';
import IntelligencePanel from '../components/IntelligencePanel';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold mb-4">FloodIntel Dashboard</h1>
      <MapComponent />
      <IntelligencePanel locationId={1} />
    </main>
  );
}
