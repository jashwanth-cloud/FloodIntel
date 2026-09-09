export const DataStateBadge = ({ state }: { state: string }) => {
  const colors: Record<string, string> = {
    LIVE: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    HISTORICAL: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    DEMO: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    PARTIAL: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    UNAVAILABLE: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
    ERROR: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };
  return <span className={`px-2 py-0.5 rounded text-xs font-semibold ${colors[state] || 'bg-gray-100'}`}>{state}</span>;
};
