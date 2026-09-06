"use client";

import { useCallback, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowLeft, Layers3, MapPinned } from "lucide-react";
import LocationControl, {
  type UserLocation,
} from "@/components/LocationControl";

const FloodMap = dynamic(() => import("@/components/FloodMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[520px] items-center justify-center bg-slate-100 text-sm text-slate-500 dark:bg-slate-900 dark:text-slate-400">
      Loading FloodIntel map...
    </div>
  ),
});

export default function MapPage() {
  const [location, setLocation] = useState<UserLocation | null>(null);

  const handleLocationChange = useCallback(
    (nextLocation: UserLocation) => {
      setLocation(nextLocation);
    },
    [],
  );

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-white">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link
              href="/"
              className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to FloodIntel
            </Link>

            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                <MapPinned className="h-5 w-5" />
              </div>

              <div>
                <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
                  Live Flood Map
                </h1>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  Explore locations and set your current position.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
            <Layers3 className="h-4 w-4" />
            OpenStreetMap base layer
          </div>
        </div>

        <section className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-lg font-semibold">Your location</h2>

            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Use your device location to center the map. You can also click
              anywhere on the map to select coordinates.
            </p>

            <div className="mt-5">
              <LocationControl
                location={location}
                onLocationChange={handleLocationChange}
              />
            </div>

            <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Map data
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                FloodIntel currently shows the verified map base and your
                selected location. Flood-specific GIS overlays will only be
                displayed after a verified data source is integrated.
              </p>
            </div>
          </aside>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="h-[520px] sm:h-[620px]">
              <FloodMap
                location={location}
                onLocationChange={handleLocationChange}
              />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
