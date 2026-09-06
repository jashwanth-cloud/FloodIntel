"use client";

import { useEffect } from "react";
import {
  CircleMarker,
  MapContainer,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";

type Coordinates = {
  latitude: number;
  longitude: number;
  accuracy?: number;
};

type FloodMapProps = {
  location?: Coordinates | null;
  onLocationChange?: (location: Coordinates) => void;
};

const INDIA_CENTER: [number, number] = [20.5937, 78.9629];

function MapController({
  location,
}: {
  location: Coordinates | null | undefined;
}) {
  const map = useMap();

  useEffect(() => {
    if (!location) return;

    map.flyTo(
      [location.latitude, location.longitude],
      Math.max(map.getZoom(), 13),
      {
        duration: 1.2,
      },
    );
  }, [location, map]);

  return null;
}

function MapInteraction({
  onLocationChange,
}: {
  onLocationChange?: (location: Coordinates) => void;
}) {
  useMapEvents({
    click(event) {
      onLocationChange?.({
        latitude: event.latlng.lat,
        longitude: event.latlng.lng,
      });
    },
  });

  return null;
}

export default function FloodMap({
  location,
  onLocationChange,
}: FloodMapProps) {
  return (
    <MapContainer
      center={
        location
          ? [location.latitude, location.longitude]
          : INDIA_CENTER
      }
      zoom={location ? 13 : 5}
      scrollWheelZoom
      className="h-full min-h-[420px] w-full"
      attributionControl
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapController location={location} />

      <MapInteraction onLocationChange={onLocationChange} />

      {location && (
        <CircleMarker
          center={[location.latitude, location.longitude]}
          radius={9}
          pathOptions={{
            color: "#0f766e",
            fillColor: "#14b8a6",
            fillOpacity: 0.9,
            weight: 3,
          }}
        />
      )}
    </MapContainer>
  );
}
