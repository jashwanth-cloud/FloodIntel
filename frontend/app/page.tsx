import MapComponent from '../components/MapComponent';
import IntelligencePanel from '../components/IntelligencePanel';

export default function Home() {
  return (
    <main className="flex flex-col md:flex-row h-screen w-screen overflow-hidden">
      <div className="flex-grow h-1/2 md:h-full">
        <MapComponent />
      </div>
      <aside className="w-full md:w-96 h-1/2 md:h-full border-t md:border-t-0 md:border-l bg-gray-50 dark:bg-gray-950 overflow-y-auto">
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-4">FloodIntel Dashboard</h1>
          <IntelligencePanel locationId={1} />
        </div>
      </aside>
    </main>
  );
}
