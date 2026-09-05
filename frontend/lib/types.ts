export type RiskLevel =
  | "LOW"
  | "MODERATE"
  | "HIGH"
  | "VERY_HIGH"
  | "SEVERE"
  | "UNKNOWN";

export interface FloodValidation {
  iou?: number;
  dice?: number;
  f1?: number;
  [key: string]: unknown;
}

export interface FloodStatusData {
  risk_level?: string;
  risk_title?: string;
  severity?: string | number;
  flood_percentage?: number;
  flooded_area_km2?: number;
  total_area_km2?: number;
  message?: string;
  actions?: string[];
  study_area?: {
    width?: number;
    height?: number;
    crs?: string;
  };
  validation?: FloodValidation;
  [key: string]: unknown;
}

export interface FloodStatusResponse {
  status: string;
  data: FloodStatusData;
}

export interface AssistantResponse {
  answer?: string;
  response?: string;
  message?: string;
  status?: string;
  [key: string]: unknown;
}