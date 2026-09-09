import MapComponent from '../components/MapComponent';
import IntelligencePanel from '../components/IntelligencePanel';

export default function Home() {
  return (
    <main className="flex h-screen w-screen overflow-hidden">
      <div className="flex-grow h-full">
        <MapComponent />
      </div>
      <aside className="w-96 h-full border-l bg-gray-50 overflow-y-auto">
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-4">FloodIntel Dashboard</h1>
          <IntelligencePanel locationId={1} />
        </div>
      </aside>
    </main>
  );
}
