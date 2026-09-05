import type {
  AssistantResponse,
  FloodStatusResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}

export async function getFloodStatus(): Promise<FloodStatusResponse> {
  return apiRequest<FloodStatusResponse>("/api/flood/status");
}

export async function getLegacyFloodStatus(): Promise<FloodStatusResponse> {
  return apiRequest<FloodStatusResponse>("/flood/status");
}

export async function getFloodStatusSafe(): Promise<FloodStatusResponse> {
  try {
    return await getFloodStatus();
  } catch {
    return getLegacyFloodStatus();
  }
}

export async function askFloodIntel(
  message: string,
  language = "en",
): Promise<AssistantResponse> {
  const params = new URLSearchParams({
    message,
    language,
  });

  return apiRequest<AssistantResponse>(
    `/assistant?${params.toString()}`,
  );
}