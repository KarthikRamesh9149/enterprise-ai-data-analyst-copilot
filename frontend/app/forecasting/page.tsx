"use client";

import { useEffect, useState } from "react";
import { Chart } from "@/components/Chart";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Dataset, ForecastRun } from "@/types/api";

export default function ForecastingPage() {
  const [role, setRole] = useState("viewer");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [runs, setRuns] = useState<ForecastRun[]>([]);
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    api<Dataset[]>("/datasets").then((ds) => { setDatasets(ds); if (ds[0]) setDatasetId(ds[0].id); });
    api<ForecastRun[]>("/forecasting/runs").then(setRuns).catch(() => {});
  }, []);
  async function run() {
    const forecast = await api<ForecastRun>("/forecasting/revenue/run", { method: "POST", body: JSON.stringify({ dataset_id: datasetId, forecast_target: "total_revenue", horizon_months: 3 }) });
    setRuns([forecast, ...runs]);
  }
  return (
    <AppShell role={role}>
      <section className="panel p-5">
        <h1 className="text-lg font-bold">Revenue forecasting</h1>
        <div className="mt-4 flex gap-3">
          <select className="field max-w-lg" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
            {datasets.map((d) => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
          </select>
          <button className="btn" onClick={run}>Run 3-month forecast</button>
        </div>
      </section>
      <div className="mt-5 grid gap-5">{runs[0] && <Chart spec={runs[0].chart_spec} />}</div>
    </AppShell>
  );
}
