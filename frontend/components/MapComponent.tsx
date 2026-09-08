'use client';
import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export default function MapComponent() {
  const mapContainer = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (map.current) return; // initialize map only once
    
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://demotiles.maplibre.org/style.json', // Use a free style
      center: [78.9629, 20.5937], // India center
      zoom: 4
    });
  }, []);

  return <div ref={mapContainer} style={{ height: '500px', width: '100%' }} />;
}
