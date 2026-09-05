import { AssistantResponse, FloodStatusResponse } from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function apiRequest<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, { headers: { Accept: "application/json" }, cache: "no-store" });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const getFloodStatus = () => apiRequest<FloodStatusResponse>("/api/flood/status");
export const getFloodAdvisory = () => apiRequest<{ status: string; advisory?: string; risk_level?: string }>("/flood/advisory");
export const getFloodValidation = () => apiRequest<{ status: string; validation?: Record<string, unknown> }>("/flood/validation");
export const askFloodIntel = (message: string, language = "en") => apiRequest<AssistantResponse>(`/assistant?${new URLSearchParams({ message, language })}`);
