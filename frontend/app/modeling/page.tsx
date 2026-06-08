"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { DataTable } from "@/components/DataTable";
import { api } from "@/lib/api";
import type { Dataset, Model } from "@/types/api";

export default function ModelingPage() {
  const [role, setRole] = useState("viewer");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [models, setModels] = useState<Model[]>([]);
  const [risk, setRisk] = useState<Record<string, unknown>[]>([]);
  const [message, setMessage] = useState("");
  const loadModels = () => api<Model[]>("/modeling/models").then(setModels).catch(() => {});
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    api<Dataset[]>("/datasets").then((ds) => { setDatasets(ds); if (ds[0]) setDatasetId(ds[0].id); });
    loadModels();
  }, []);
  async function train() {
    const model = await api<Model>("/modeling/churn/train", { method: "POST", body: JSON.stringify({ dataset_id: datasetId, target_column: "churned" }) });
    setMessage(`Model trained: F1 ${model.metrics.f1?.toFixed?.(3) ?? model.metrics.f1}`);
    loadModels();
    const scores = await api<Record<string, unknown>[]>(`/modeling/models/${model.id}/risk-scores`);
    setRisk(scores);
  }
  return (
    <AppShell role={role}>
      <div className="grid gap-5">
        <section className="panel p-5">
          <h1 className="text-lg font-bold">Churn modeling and risk scoring</h1>
          <div className="mt-4 flex gap-3">
            <select className="field max-w-lg" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
              {datasets.map((d) => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
            </select>
            <button className="btn" onClick={train}><Sparkles size={16} /> Train model</button>
          </div>
          {message && <p className="mt-3 text-sm text-teal">{message}</p>}
        </section>
        <section className="grid grid-cols-3 gap-4">
          {models[0] && Object.entries(models[0].metrics).map(([k, v]) => (
            <div className="panel p-4" key={k}><div className="text-xs font-bold uppercase text-muted">{k}</div><div className="mt-2 text-2xl font-bold">{Number(v).toFixed(3)}</div></div>
          ))}
        </section>
        <DataTable rows={(models[0]?.feature_importance ?? []) as any[]} />
        <DataTable rows={risk} />
      </div>
    </AppShell>
  );
}
