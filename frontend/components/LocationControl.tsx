"use client";

import { useCallback, useState } from "react";
import { Crosshair, Loader2, MapPin, ShieldAlert } from "lucide-react";

export type UserLocation = {
  latitude: number;
  longitude: number;
  accuracy?: number;
};

type LocationControlProps = {
  location: UserLocation | null;
  onLocationChange: (location: UserLocation) => void;
};

export default function LocationControl({
  location,
  onLocationChange,
}: LocationControlProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const locateUser = useCallback(() => {
    setError(null);

    if (!navigator.geolocation) {
      setError("Location services are not supported by this browser.");
      return;
    }

    setLoading(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        onLocationChange({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });

        setLoading(false);
      },
      (locationError) => {
        setLoading(false);

        if (locationError.code === 1) {
          setError(
            "Location permission was denied. Allow location access in your browser settings.",
          );
        } else if (locationError.code === 2) {
          setError("Your location is currently unavailable.");
        } else if (locationError.code === 3) {
          setError("Location request timed out. Please try again.");
        } else {
          setError("Unable to determine your location.");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000,
      },
    );
  }, [onLocationChange]);

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={locateUser}
        disabled={loading}
        className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Crosshair className="h-4 w-4" />
        )}

        {loading ? "Finding you..." : "Use my location"}
      </button>

      {location && (
        <div className="flex items-start gap-3 rounded-xl border border-teal-200 bg-teal-50 p-3 text-sm text-teal-900 dark:border-teal-900/60 dark:bg-teal-950/30 dark:text-teal-200">
          <MapPin className="mt-0.5 h-4 w-4 shrink-0" />

          <div>
            <p className="font-semibold">Location detected</p>

            <p className="mt-0.5 text-xs opacity-80">
              <span>
                {location.latitude.toFixed(5)},{" "}
                {location.longitude.toFixed(5)}
              </span>

              {location.accuracy !== undefined && (
                <span>
                  {" "}({Math.round(location.accuracy)} m accuracy)
                </span>
              )}
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />

          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
