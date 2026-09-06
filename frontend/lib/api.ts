import type {
  AssistantResponse,
  FloodAdvisoryResponse,
  FloodExplanationResponse,
  FloodStatisticsResponse,
  FloodStatusResponse,
  FloodSummaryResponse,
  FloodValidationResponse,
  LanguageResponse,
  SystemInfoResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";

async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(options?.headers || {}),
      },
      cache: "no-store",
    });

    if (!response.ok) {
      // Try to parse error detail from backend
      let errorDetail = response.statusText;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorDetail;
      } catch {
        // Fallback to statusText if JSON parsing fails
      }
      
      throw new Error(
        `API request failed: ${response.status} - ${errorDetail}`,
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new Error("Cannot connect to FloodIntel backend. Please check if the server is running.");
    }
    throw error;
  }
}

// Flood Intelligence Endpoints
export async function getFloodStatus(): Promise<FloodStatusResponse> {
  return apiRequest<FloodStatusResponse>("/api/flood/status");
}

export async function getFloodSummary(): Promise<FloodSummaryResponse> {
  return apiRequest<FloodSummaryResponse>("/api/flood/summary");
}

export async function getFloodStatistics(): Promise<FloodStatisticsResponse> {
  return apiRequest<FloodStatisticsResponse>("/api/flood/statistics");
}

export async function getFloodValidation(): Promise<FloodValidationResponse> {
  return apiRequest<FloodValidationResponse>("/api/flood/validation");
}

export async function getFloodAdvisory(): Promise<FloodAdvisoryResponse> {
  return apiRequest<FloodAdvisoryResponse>("/api/flood/advisory");
}

export async function getFloodExplain(): Promise<FloodExplanationResponse> {
  return apiRequest<FloodExplanationResponse>("/api/flood/explain");
}

// Assistant Endpoints
export async function askAssistant(
  message: string,
  language: string = "en",
): Promise<AssistantResponse> {
  return apiRequest<AssistantResponse>("/api/assistant/", {
    method: "POST",
    body: JSON.stringify({ message, language }),
  });
}

// System Endpoints
export async function getSystemInfo(): Promise<SystemInfoResponse> {
  return apiRequest<SystemInfoResponse>("/api/system/info");
}

export async function getSupportedLanguages(): Promise<LanguageResponse> {
  return apiRequest<LanguageResponse>("/api/languages");
}

export async function checkHealth(): Promise<{ status: string; flood_data_available: boolean }> {
  return apiRequest<{ status: string; flood_data_available: boolean }>("/health");
}
