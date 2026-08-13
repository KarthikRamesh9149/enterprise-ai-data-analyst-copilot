"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Upload, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Status } from "@/components/Status";
import { api, API_BASE } from "@/lib/api";
import type { Dataset } from "@/types/api";

export default function DatasetsPage() {
  const [role, setRole] = useState("viewer");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [message, setMessage] = useState("");
  const load = () => api<Dataset[]>("/datasets").then(setDatasets).catch((e) => setMessage(e.message));
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    load();
  }, []);
  async function upload(file?: File) {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${API_BASE}/datasets/upload`, { method: "POST", body: form, credentials: "include" });
    setMessage(response.ok ? "Dataset uploaded." : await response.text());
    load();
  }
  async function action(id: string, path: string) {
    await api(`/datasets/${id}/${path}`, { method: "POST" });
    load();
  }
  return (
    <AppShell role={role}>
      <section className="panel p-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold">Datasets</h1>
            <p className="text-sm text-muted">Upload, validate, profile, inspect schema, and load CSVs into DuckDB.</p>
          </div>
          <label className="btn cursor-pointer">
            <Upload size={16} /> Upload CSV
            <input className="hidden" type="file" accept=".csv" onChange={(e) => upload(e.target.files?.[0])} />
          </label>
        </div>
        {message && <div className="mt-4 rounded-md border border-line bg-[#f8fafc] p-3 text-sm">{message}</div>}
        <table className="table mt-5">
          <thead><tr><th>Dataset</th><th>Rows</th><th>Quality</th><th>Status</th><th>Validation</th><th>Actions</th></tr></thead>
          <tbody>
            {datasets.map((d) => (
              <tr key={d.id}>
                <td><Link className="font-bold text-teal" href={`/datasets/${d.id}`}>{d.original_filename}</Link></td>
                <td>{d.row_count}</td>
                <td>{Math.round(d.quality_score)}%</td>
                <td><Status value={d.status} /></td>
                <td><Status value={d.validation_status} /></td>
                <td className="flex gap-2">
                  <button className="btn secondary" onClick={() => action(d.id, "validate")}><RefreshCw size={14} /> Validate</button>
                  <button className="btn secondary" onClick={() => action(d.id, "load-to-duckdb")}>Load</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}
