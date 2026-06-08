export type User = { id: string; email: string; role: "admin" | "analyst" | "reviewer" | "viewer"; created_at: string };
export type Dataset = {
  id: string;
  original_filename: string;
  duckdb_table_name: string | null;
  row_count: number;
  column_count: number;
  status: string;
  validation_status: string;
  quality_score: number;
  validation_summary: Record<string, unknown>;
};
export type Query = {
  id: string;
  generated_sql: string;
  explanation: string;
  safety_status: string;
  safety_findings: string[];
  approval_status: string;
  execution_status: string;
};
export type Approval = { id: string; action_type: string; resource_type: string; resource_id: string; status: string; request_reason: string };
export type Model = { id: string; model_type: string; metrics: Record<string, number>; feature_importance: Array<{ feature: string; importance: number }> };
export type ForecastRun = { id: string; forecast_target: string; metrics: Record<string, number>; forecast_values: Array<{ period: string; forecast: number }>; chart_spec: any };
export type Report = { id: string; title: string; markdown_content: string; created_at: string };
