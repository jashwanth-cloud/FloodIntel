'use client';
import { useState, useEffect } from 'react';

export default function AppHeader() {
  const [lang, setLang] = useState('en');
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="flex justify-between items-center p-4 border-b bg-white dark:bg-gray-900 dark:border-gray-800">
      <div className="font-bold text-lg">FloodIntel</div>
      <div className="flex gap-4 items-center">
        <select value={lang} onChange={(e) => setLang(e.target.value)} className="text-sm bg-transparent border rounded p-1">
          <option value="en">English</option>
          <option value="te">తెలుగు</option>
        </select>
        <button onClick={toggleTheme} className="text-sm border p-1 rounded">
          {isDark ? 'Light' : 'Dark'}
        </button>
      </div>
    </header>
  );
}
