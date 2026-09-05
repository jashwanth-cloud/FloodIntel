export interface FloodValidation { iou?: number; dice?: number; f1?: number; [key: string]: unknown }
export interface FloodStatusData {
  dataset?: { width?: number; height?: number; crs?: string };
  prediction?: { status?: string; label?: string; total_pixels?: number; flood_pixels?: number; flood_percentage?: number };
  area?: { total_area_km2?: number; flooded_area_km2?: number; pixel_area_m2?: number };
  risk?: { level?: string; risk_level?: string; [key: string]: unknown };
  validation?: FloodValidation;
  [key: string]: unknown;
}
export interface FloodStatusResponse { status: string; data: FloodStatusData }
export interface AssistantResponse { answer?: string; response?: string; message?: string; status?: string; language?: string }
