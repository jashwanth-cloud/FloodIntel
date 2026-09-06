export type RiskLevel =
  | "LOW"
  | "MODERATE"
  | "MEDIUM"
  | "HIGH"
  | "SEVERE"
  | "CRITICAL"
  | "UNKNOWN";

export interface FloodPrediction {
  flood_pixels?: number;
  total_pixels?: number;
  flood_percentage?: number;
  [key: string]: unknown;
}

export interface FloodRisk {
  level?: string;
  risk_level?: string;
  score?: number;
  [key: string]: unknown;
}

export interface FloodArea {
  flooded_area_km2?: number;
  total_area_km2?: number;
  [key: string]: unknown;
}

export interface FloodValidation {
  iou?: number;
  dice?: number;
  f1?: number;
  accuracy?: number;
  [key: string]: unknown;
}

export interface FloodStatusResponse {
  status: string;
  data: {
    prediction: FloodPrediction;
    risk: FloodRisk;
    area: FloodArea;
  };
  source: string;
}

export interface FloodSummaryResponse {
  status: string;
  data: {
    prediction: FloodPrediction;
    risk: FloodRisk;
    area: FloodArea;
    validation: FloodValidation;
    statistics?: Record<string, unknown>;
    [key: string]: unknown;
  };
  source: string;
}

export interface FloodStatisticsResponse {
  status: string;
  statistics: Record<string, unknown>;
}

export interface FloodValidationResponse {
  status: string;
  validation: FloodValidation;
}

export interface FloodAdvisoryResponse {
  status: string;
  risk_level: string;
  prediction: FloodPrediction;
  advisory: string;
}

export interface FloodExplanationResponse {
  status: string;
  risk_level: string;
  evidence: string[];
  validation: FloodValidation;
  limitations: string[];
  source: string;
}

export interface AssistantResponse {
  status: string;
  answer: string;
  language: string;
  [key: string]: unknown;
}

export interface SystemInfoResponse {
  status: string;
  application: {
    name: string;
    version: string;
  };
  services: {
    flood_data: {
      available: boolean;
    };
    ollama: {
      status: string;
      model?: string;
    };
    model: Record<string, unknown>;
  };
  supported_languages: string[];
  prediction_source: string;
}

export interface LanguageResponse {
  status: string;
  count: number;
  languages: string[];
}
