"use client";

import { useState } from "react";

type RiskLevel = "Low" | "Moderate" | "High" | "Severe";

const navItems = [
  "Overview",
  "Risk Map",
  "Alerts",
  "History",
  "Reports",
];

const languages = [
  "English",
  "తెలుగు",
  "हिन्दी",
  "தமிழ்",
  "ಕನ್ನಡ",
];

const riskFactors = [
  { name: "Rainfall", value: 78, level: "High" },
  { name: "Water proximity", value: 55, level: "Medium" },
  { name: "Terrain / elevation", value: 32, level: "Low" },
  { name: "Historical flooding", value: 61, level: "Medium" },
];

const alerts = [
  {
    title: "Heavy rainfall watch",
    location: "Selected region",
    time: "Monitoring",
    severity: "High",
  },
  {
    title: "Water level observation",
    location: "Nearby waterbody",
    time: "Monitoring",
    severity: "Moderate",
  },
  {
    title: "Flood preparedness advisory",
    location: "Local area",
    time: "Active",
    severity: "Info",
  },
];

const historicalEvents = [
  { year: "2025", event: "Major rainfall event", impact: "High" },
  { year: "2024", event: "Urban inundation", impact: "Moderate" },
  { year: "2023", event: "River flooding", impact: "High" },
];

export default function Home() {
  const [location, setLocation] = useState("");
  const [language, setLanguage] = useState("English");
  const [riskLevel] = useState<RiskLevel>("Moderate");
  const [showLanguages, setShowLanguages] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);

  const riskStyles = {
    Low: {
      badge: "bg-emerald-400/10 text-emerald-300 border-emerald-400/20",
      text: "text-emerald-400",
    },
    Moderate: {
      badge: "bg-amber-400/10 text-amber-300 border-amber-400/20",
      text: "text-amber-400",
    },
    High: {
      badge: "bg-orange-400/10 text-orange-300 border-orange-400/20",
      text: "text-orange-400",
    },
    Severe: {
      badge: "bg-red-400/10 text-red-300 border-red-400/20",
      text: "text-red-400",
    },
  };

  const currentRisk = riskStyles[riskLevel];

  return (
    <main className="min-h-screen bg-[#06111f] text-white selection:bg-cyan-400/30">
      {/* ========================================================= */}
      {/* HEADER */}
      {/* ========================================================= */}

      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#06111f]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 sm:px-6">
          {/* Brand */}
          <a href="#" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400 font-black text-lg text-[#06111f] shadow-lg shadow-cyan-400/20">
              F
            </div>

            <div>
              <div className="text-lg font-bold tracking-tight">
                FloodIntel
              </div>
              <div className="hidden text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500 sm:block">
                Flood Intelligence Platform
              </div>
            </div>
          </a>

          {/* Desktop navigation */}
          <nav className="hidden items-center gap-7 lg:flex">
            {navItems.map((item, index) => (
              <a
                key={item}
                href={`#${item.toLowerCase().replaceAll(" ", "-")}`}
                className={`text-sm transition ${
                  index === 0
                    ? "font-semibold text-cyan-300"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {item}
              </a>
            ))}

            <a
              href="#municipality"
              className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:border-cyan-400/30 hover:bg-cyan-400/10 hover:text-cyan-300"
            >
              Municipality
            </a>
          </nav>

          {/* Header actions */}
          <div className="flex items-center gap-2">
            <div className="relative hidden sm:block">
              <button
                onClick={() => setShowLanguages(!showLanguages)}
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10"
              >
                🌐 {language}
              </button>

              {showLanguages && (
                <div className="absolute right-0 mt-2 w-40 overflow-hidden rounded-xl border border-white/10 bg-[#0b1a2b] p-1 shadow-2xl">
                  {languages.map((item) => (
                    <button
                      key={item}
                      onClick={() => {
                        setLanguage(item);
                        setShowLanguages(false);
                      }}
                      className="block w-full rounded-lg px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/10 hover:text-white"
                    >
                      {item}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={() => setMobileMenu(!mobileMenu)}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-lg lg:hidden"
              aria-label="Open menu"
            >
              ☰
            </button>

            <button className="hidden rounded-lg bg-white px-4 py-2 text-sm font-semibold text-[#06111f] transition hover:bg-cyan-300 sm:block">
              Sign in
            </button>
          </div>
        </div>

        {/* Mobile navigation */}
        {mobileMenu && (
          <div className="border-t border-white/10 bg-[#071525] px-5 py-4 lg:hidden">
            <div className="space-y-1">
              {navItems.map((item) => (
                <a
                  key={item}
                  href={`#${item.toLowerCase().replaceAll(" ", "-")}`}
                  onClick={() => setMobileMenu(false)}
                  className="block rounded-lg px-3 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-cyan-300"
                >
                  {item}
                </a>
              ))}

              <a
                href="#municipality"
                className="block rounded-lg px-3 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-cyan-300"
              >
                Municipality Dashboard
              </a>
            </div>
          </div>
        )}
      </header>

      {/* ========================================================= */}
      {/* HERO */}
      {/* ========================================================= */}

      <section className="relative overflow-hidden border-b border-white/10">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/4 top-0 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />
          <div className="absolute right-0 top-32 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="absolute bottom-0 left-1/2 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-7xl px-5 pb-16 pt-16 sm:px-6 lg:pb-20 lg:pt-24">
          <div className="max-w-4xl">
            {/* Status */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-xs font-medium text-cyan-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
              Flood intelligence platform
              <span className="text-slate-500">•</span>
              India
            </div>

            <h1 className="text-4xl font-black leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">
              Know the risk.
              <br />
              <span className="bg-gradient-to-r from-cyan-300 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
                Act before the flood.
              </span>
            </h1>

            <p className="mt-7 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">
              FloodIntel brings together rainfall, satellite observations,
              terrain, water bodies and historical flood information to help
              communities understand flood risk and respond earlier.
            </p>

            {/* Location search */}
            <div className="mt-9 max-w-3xl">
              <div className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-white/[0.06] p-2 shadow-2xl shadow-black/20 backdrop-blur sm:flex-row">
                <div className="flex flex-1 items-center gap-3 px-3">
                  <span className="text-lg text-slate-500">⌖</span>

                  <input
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Search city, district, ward or use your location"
                    className="w-full bg-transparent py-3 text-sm text-white outline-none placeholder:text-slate-500"
                  />
                </div>

                <button className="rounded-xl bg-cyan-400 px-6 py-3 text-sm font-bold text-[#06111f] transition hover:bg-cyan-300">
                  Check flood risk
                </button>
              </div>

              <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
                <button className="hover:text-cyan-300">
                  ◎ Use my current location
                </button>
                <span>•</span>
                <span>India-wide intelligence</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* OVERVIEW */}
      {/* ========================================================= */}

      <section
        id="overview"
        className="mx-auto max-w-7xl px-5 py-12 sm:px-6 lg:py-16"
      >
        <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
              Risk overview
            </p>

            <h2 className="mt-2 text-2xl font-bold sm:text-3xl">
              Flood conditions at a glance
            </h2>
          </div>

          <div className="text-xs text-slate-500">
            Data connection will appear here
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Risk */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 transition hover:border-cyan-400/20">
            <div className="flex items-start justify-between">
              <p className="text-sm text-slate-400">Current risk</p>

              <span
                className={`rounded-full border px-2.5 py-1 text-[11px] ${currentRisk.badge}`}
              >
                {riskLevel}
              </span>
            </div>

            <p className={`mt-6 text-3xl font-bold ${currentRisk.text}`}>
              {riskLevel}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Awaiting location-specific data
            </p>
          </div>

          {/* Rainfall */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 transition hover:border-cyan-400/20">
            <p className="text-sm text-slate-400">Recent rainfall</p>

            <p className="mt-6 text-3xl font-bold">
              —
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Connect IMD rainfall data
            </p>
          </div>

          {/* Flood zones */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 transition hover:border-cyan-400/20">
            <p className="text-sm text-slate-400">Flood-prone zones</p>

            <p className="mt-6 text-3xl font-bold">
              —
            </p>

            <p className="mt-2 text-xs text-slate-500">
              GIS intelligence
            </p>
          </div>

          {/* Alerts */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 transition hover:border-cyan-400/20">
            <p className="text-sm text-slate-400">Active alerts</p>

            <p className="mt-6 text-3xl font-bold text-red-400">
              —
            </p>

            <p className="mt-2 text-xs text-slate-500">
              No live connection yet
            </p>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* RISK MAP */}
      {/* ========================================================= */}

      <section
        id="risk-map"
        className="mx-auto max-w-7xl px-5 pb-12 sm:px-6 lg:pb-16"
      >
        <div className="grid gap-5 lg:grid-cols-3">
          {/* Map */}
          <div className="relative min-h-[480px] overflow-hidden rounded-3xl border border-white/10 bg-[#091827] lg:col-span-2">
            {/* Map grid */}
            <div
              className="absolute inset-0 opacity-30"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(148,163,184,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.08) 1px, transparent 1px)",
                backgroundSize: "48px 48px",
              }}
            />

            {/* Simulated map shapes */}
            <div className="absolute left-[15%] top-[28%] h-28 w-40 rounded-[55%] border border-cyan-400/20 bg-cyan-400/5 blur-[1px]" />
            <div className="absolute right-[18%] top-[20%] h-32 w-48 rounded-[50%] border border-blue-400/20 bg-blue-400/5" />
            <div className="absolute bottom-[20%] left-[35%] h-24 w-56 rounded-[50%] border border-indigo-400/20 bg-indigo-400/5" />

            {/* Map content */}
            <div className="relative z-10 flex min-h-[480px] flex-col justify-between p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-cyan-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                      Interactive risk map
                    </span>
                  </div>

                  <h3 className="mt-2 text-xl font-bold">
                    India Flood Intelligence
                  </h3>
                </div>

                <button className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-xs text-slate-300 backdrop-blur hover:bg-white/10">
                  Layers
                </button>
              </div>

              <div className="mx-auto max-w-md text-center">
                <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-3xl border border-cyan-400/20 bg-cyan-400/10 text-4xl">
                  🌊
                </div>

                <h3 className="text-2xl font-bold">
                  Your map will live here
                </h3>

                <p className="mt-3 text-sm leading-6 text-slate-400">
                  This map component will connect to our real GIS layers,
                  flood-risk predictions, rivers, water bodies, administrative
                  boundaries and satellite-derived information.
                </p>

                <button className="mt-6 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-[#06111f] hover:bg-cyan-300">
                  Explore map
                </button>
              </div>

              <div className="flex flex-wrap gap-2">
                {["Risk", "Rainfall", "Water bodies", "Rivers", "History"].map(
                  (layer) => (
                    <button
                      key={layer}
                      className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-400 backdrop-blur hover:border-cyan-400/20 hover:text-cyan-300"
                    >
                      {layer}
                    </button>
                  ),
                )}
              </div>
            </div>
          </div>

          {/* Risk explanation */}
          <div className="rounded-3xl border border-white/10 bg-white/[0.045] p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  AI analysis
                </p>

                <h3 className="mt-1 text-xl font-bold">
                  Why this risk?
                </h3>
              </div>

              <span
                className={`rounded-full border px-3 py-1 text-xs ${currentRisk.badge}`}
              >
                {riskLevel}
              </span>
            </div>

            <p className="mt-4 text-sm leading-6 text-slate-400">
              FloodIntel will explain the major factors contributing to the
              risk level instead of showing only a score.
            </p>

            <div className="mt-7 space-y-6">
              {riskFactors.map((factor) => (
                <div key={factor.name}>
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="text-slate-300">{factor.name}</span>
                    <span className="text-slate-500">{factor.level}</span>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-cyan-400 transition-all"
                      style={{ width: `${factor.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <button className="mt-8 w-full rounded-xl border border-white/10 bg-white/5 py-3 text-sm font-medium text-slate-200 hover:bg-white/10">
              View detailed analysis
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* ALERTS + RAINFALL */}
      {/* ========================================================= */}

      <section
        id="alerts"
        className="mx-auto max-w-7xl px-5 py-12 sm:px-6 lg:py-16"
      >
        <div className="grid gap-5 lg:grid-cols-5">
          {/* Alerts */}
          <div className="rounded-3xl border border-white/10 bg-white/[0.045] p-6 lg:col-span-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-red-400">
                  Safety
                </p>

                <h2 className="mt-1 text-xl font-bold">
                  Flood alerts & advisories
                </h2>
              </div>

              <button className="text-xs text-cyan-300 hover:text-cyan-200">
                View all →
              </button>
            </div>

            <div className="mt-6 space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.title}
                  className="flex items-center gap-4 rounded-2xl border border-white/10 bg-black/10 p-4"
                >
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                      alert.severity === "High"
                        ? "bg-red-400/10 text-red-400"
                        : alert.severity === "Moderate"
                          ? "bg-amber-400/10 text-amber-400"
                          : "bg-cyan-400/10 text-cyan-400"
                    }`}
                  >
                    {alert.severity === "High" ? "!" : "i"}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-slate-200">
                      {alert.title}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {alert.location} • {alert.time}
                    </p>
                  </div>

                  <span className="hidden rounded-full border border-white/10 px-2 py-1 text-[10px] text-slate-500 sm:block">
                    {alert.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Rainfall */}
          <div className="rounded-3xl border border-white/10 bg-white/[0.045] p-6 lg:col-span-2">
            <p className="text-xs uppercase tracking-wider text-cyan-400">
              Weather intelligence
            </p>

            <h2 className="mt-1 text-xl font-bold">
              Rainfall monitoring
            </h2>

            <div className="mt-7 flex items-end justify-between">
              <div>
                <p className="text-4xl font-black">—</p>
                <p className="mt-1 text-xs text-slate-500">
                  Recent rainfall
                </p>
              </div>

              <div className="rounded-xl bg-cyan-400/10 px-3 py-2 text-xs text-cyan-300">
                IMD data
              </div>
            </div>

            {/* Chart placeholder */}
            <div className="mt-8 flex h-32 items-end gap-2">
              {[35, 52, 42, 68, 45, 80, 58, 72, 50, 65, 42, 74].map(
                (height, index) => (
                  <div
                    key={index}
                    className="flex-1 rounded-t-md bg-cyan-400/20"
                    style={{ height: `${height}%` }}
                  />
                ),
              )}
            </div>

            <div className="mt-3 flex justify-between text-[10px] text-slate-600">
              <span>Past</span>
              <span>Today</span>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* HISTORY */}
      {/* ========================================================= */}

      <section
        id="history"
        className="border-y border-white/10 bg-[#071525]"
      >
        <div className="mx-auto max-w-7xl px-5 py-12 sm:px-6 lg:py-16">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
              Historical intelligence
            </p>

            <h2 className="mt-2 text-2xl font-bold sm:text-3xl">
              Understand what happened before
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Explore previous flood events and compare historical conditions
              with current observations.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {historicalEvents.map((event) => (
              <div
                key={event.year}
                className="rounded-2xl border border-white/10 bg-white/[0.035] p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-black text-cyan-400">
                    {event.year}
                  </span>

                  <span className="rounded-full bg-white/5 px-2.5 py-1 text-[10px] text-slate-400">
                    {event.impact} impact
                  </span>
                </div>

                <h3 className="mt-6 font-semibold">
                  {event.event}
                </h3>

                <p className="mt-2 text-xs leading-5 text-slate-500">
                  Historical event details will be loaded from the FloodIntel
                  database and verified data sources.
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* CITIZEN REPORTING */}
      {/* ========================================================= */}

      <section
        id="reports"
        className="mx-auto max-w-7xl px-5 py-12 sm:px-6 lg:py-16"
      >
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-cyan-400/10 bg-cyan-400/[0.04] p-7">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400/10 text-2xl">
              📸
            </div>

            <h2 className="mt-6 text-2xl font-bold">
              Report flooding in your area
            </h2>

            <p className="mt-3 max-w-lg text-sm leading-6 text-slate-400">
              Help authorities understand ground conditions by submitting a
              flood report with a photo, location and description.
            </p>

            <button className="mt-7 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-bold text-[#06111f] hover:bg-cyan-300">
              Report a flood
            </button>
          </div>

          <div
            id="municipality"
            className="rounded-3xl border border-white/10 bg-white/[0.045] p-7"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-400/10 text-2xl">
              📊
            </div>

            <h2 className="mt-6 text-2xl font-bold">
              Municipality intelligence
            </h2>

            <p className="mt-3 max-w-lg text-sm leading-6 text-slate-400">
              Monitor high-risk wards, rainfall, citizen reports, flood
              history and emerging risk from one operational dashboard.
            </p>

            <button className="mt-7 rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10">
              Open authority dashboard
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* AI ASSISTANT */}
      {/* ========================================================= */}

      <section className="mx-auto max-w-7xl px-5 pb-12 sm:px-6 lg:pb-16">
        <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/[0.08] via-white/[0.03] to-blue-500/[0.08] p-7 sm:p-10">
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-cyan-400/10 blur-3xl" />

          <div className="relative max-w-3xl">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-400 text-xl text-[#06111f]">
                ✦
              </div>

              <div>
                <p className="text-xs uppercase tracking-wider text-cyan-300">
                  FloodIntel AI
                </p>
                <h2 className="text-xl font-bold">
                  Ask about flood risk
                </h2>
              </div>
            </div>

            <p className="mt-5 text-sm leading-6 text-slate-400 sm:text-base">
              Ask questions about your local flood risk, rainfall, alerts,
              historical events and preparedness. The assistant will be
              connected to FloodIntel data instead of relying only on generic
              AI answers.
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              {[
                "What is my flood risk?",
                "Why is the risk high?",
                "What should I do now?",
              ].map((question) => (
                <button
                  key={question}
                  onClick={() => setAssistantOpen(true)}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300 hover:border-cyan-400/20 hover:text-cyan-300"
                >
                  {question}
                </button>
              ))}
            </div>

            <button
              onClick={() => setAssistantOpen(true)}
              className="mt-6 rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#06111f] hover:bg-cyan-300"
            >
              Open AI assistant
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* OFFLINE + EMERGENCY */}
      {/* ========================================================= */}

      <section className="border-y border-white/10 bg-[#071525]">
        <div className="mx-auto grid max-w-7xl gap-5 px-5 py-10 sm:px-6 md:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-400/10 text-emerald-400">
                ◉
              </div>

              <div>
                <h3 className="font-semibold">
                  Offline-ready intelligence
                </h3>

                <p className="mt-1 text-xs text-slate-500">
                  Essential alerts, saved locations and emergency information
                  can remain available when connectivity is limited.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-red-400/10 bg-red-400/[0.04] p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-400/10 text-red-400">
                !
              </div>

              <div>
                <h3 className="font-semibold">
                  Emergency preparedness
                </h3>

                <p className="mt-1 text-xs text-slate-500">
                  Emergency contacts, safety guidance and evacuation
                  information will be available from the platform.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* FOOTER */}
      {/* ========================================================= */}

      <footer className="mx-auto max-w-7xl px-5 py-10 sm:px-6">
        <div className="flex flex-col justify-between gap-6 border-b border-white/10 pb-8 md:flex-row">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-400 font-black text-[#06111f]">
                F
              </div>

              <span className="font-bold">
                FloodIntel
              </span>
            </div>

            <p className="mt-3 max-w-sm text-xs leading-5 text-slate-500">
              AI-powered flood intelligence and early-warning platform for
              safer communities and smarter disaster management.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-x-12 gap-y-3 text-xs text-slate-500 sm:grid-cols-3">
            <a href="#overview" className="hover:text-cyan-300">
              Overview
            </a>
            <a href="#risk-map" className="hover:text-cyan-300">
              Risk Map
            </a>
            <a href="#alerts" className="hover:text-cyan-300">
              Alerts
            </a>
            <a href="#history" className="hover:text-cyan-300">
              History
            </a>
            <a href="#reports" className="hover:text-cyan-300">
              Reports
            </a>
            <a href="#municipality" className="hover:text-cyan-300">
              Municipality
            </a>
          </div>
        </div>

        <div className="flex flex-col justify-between gap-3 pt-6 text-[11px] text-slate-600 sm:flex-row">
          <p>© 2026 FloodIntel. Built for safer communities.</p>
          <p>Data-driven • AI-assisted • Disaster-focused</p>
        </div>
      </footer>

      {/* ========================================================= */}
      {/* FLOATING AI BUTTON */}
      {/* ========================================================= */}

      <button
        onClick={() => setAssistantOpen(true)}
        className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-cyan-400 text-xl text-[#06111f] shadow-2xl shadow-cyan-400/20 transition hover:scale-105 hover:bg-cyan-300"
        aria-label="Open FloodIntel AI assistant"
      >
        ✦
      </button>

      {/* ========================================================= */}
      {/* AI ASSISTANT PANEL */}
      {/* ========================================================= */}

      {assistantOpen && (
        <div className="fixed inset-0 z-[60] flex items-end justify-center bg-black/60 p-3 backdrop-blur-sm sm:items-center">
          <div className="w-full max-w-lg overflow-hidden rounded-3xl border border-white/10 bg-[#0a1828] shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400 text-[#06111f]">
                  ✦
                </div>

                <div>
                  <h3 className="font-bold">
                    FloodIntel AI
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Data-connected assistant
                  </p>
                </div>
              </div>

              <button
                onClick={() => setAssistantOpen(false)}
                className="rounded-lg px-3 py-2 text-slate-400 hover:bg-white/5 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-5">
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-sm leading-6 text-slate-300">
                  The FloodIntel AI assistant is ready for integration with
                  the FastAPI backend, risk engine, rainfall data and
                  Supabase.
                </p>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <button className="rounded-full border border-white/10 px-3 py-2 text-xs text-slate-400 hover:border-cyan-400/20 hover:text-cyan-300">
                  Check local risk
                </button>

                <button className="rounded-full border border-white/10 px-3 py-2 text-xs text-slate-400 hover:border-cyan-400/20 hover:text-cyan-300">
                  Explain risk
                </button>

                <button className="rounded-full border border-white/10 px-3 py-2 text-xs text-slate-400 hover:border-cyan-400/20 hover:text-cyan-300">
                  Safety guidance
                </button>
              </div>

              <div className="mt-5 flex gap-2 rounded-xl border border-white/10 bg-black/20 p-2">
                <input
                  placeholder="Ask FloodIntel..."
                  className="min-w-0 flex-1 bg-transparent px-3 text-sm outline-none placeholder:text-slate-600"
                />

                <button className="rounded-lg bg-cyan-400 px-4 py-2 text-sm font-bold text-[#06111f]">
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}