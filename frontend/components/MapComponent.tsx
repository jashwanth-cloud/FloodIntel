'use client';
import { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export default function MapComponent() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (map.current || !mapContainer.current) return; // initialize map only once
    
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [78.9629, 20.5937],
      zoom: 4
    });

    map.current.on('load', async () => {
      // Fetch historical flood data
      try {
        const response = await fetch('/api/v1/satellite/flood/default');
        const data = await response.json();
        
        // Add flood extent as a source and layer
        map.current?.addSource('historical-flood', {
          'type': 'geojson',
          'data': {
            'type': 'Feature',
            'properties': { 'description': 'Historical Flood Extent (2024-09-01)' },
            'geometry': {
              'type': 'Polygon',
              'coordinates': [[
                [data.bounds[0], data.bounds[1]],
                [data.bounds[2], data.bounds[1]],
                [data.bounds[2], data.bounds[3]],
                [data.bounds[0], data.bounds[3]],
                [data.bounds[0], data.bounds[1]]
              ]]
            }
          }
        });
        
        map.current?.addLayer({
          'id': 'historical-flood-layer',
          'type': 'fill',
          'source': 'historical-flood',
          'layout': {},
          'paint': {
            'fill-color': '#088',
            'fill-opacity': 0.5
          }
        });
      } catch (error) {
        console.error('Failed to load historical flood layer:', error);
      }
    });
  }, []);

  return <div ref={mapContainer} style={{ height: '500px', width: '100%' }} />;
}
