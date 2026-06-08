"use client";

import { useEffect, useState } from "react";
import { Play, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Chart } from "@/components/Chart";
import { DataTable } from "@/components/DataTable";
import { Status } from "@/components/Status";
import { api } from "@/lib/api";
import type { Dataset, Query } from "@/types/api";

export default function AnalyticsPage() {
  const [role, setRole] = useState("viewer");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [question, setQuestion] = useState("Which customer segments have the highest churn rate?");
  const [query, setQuery] = useState<Query | null>(null);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [chart, setChart] = useState<any>(null);
  const [history, setHistory] = useState<Query[]>([]);
  const [message, setMessage] = useState("");
  const refreshHistory = () => api<Query[]>("/analytics/history").then(setHistory).catch(() => {});
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    api<Dataset[]>("/datasets").then((ds) => { setDatasets(ds); if (ds[0]) setDatasetId(ds[0].id); }).catch(() => {});
    refreshHistory();
  }, []);
  async function ask() {
    const response = await api<{ query: Query }>("/analytics/question", { method: "POST", body: JSON.stringify({ dataset_id: datasetId, question }) });
    setQuery(response.query);
    setRows([]);
    setChart(null);
    refreshHistory();
  }
  async function approve() {
    if (!query) return;
    const updated = await api<Query>("/analytics/approve-sql", { method: "POST", body: JSON.stringify({ query_id: query.id, reviewer_notes: "Approved in local demo." }) });
    setQuery(updated);
    setMessage("SQL approved.");
  }
  async function execute() {
    if (!query) return;
    const result = await api<any>("/analytics/execute-sql", { method: "POST", body: JSON.stringify({ query_id: query.id }) });
    setRows(result.result_preview);
    const chartResponse = await api<any>(`/analytics/queries/${query.id}/chart`);
    setChart(chartResponse?.chart_spec);
    refreshHistory();
  }
  return (
    <AppShell role={role}>
      <div className="grid grid-cols-[1fr_360px] gap-5">
        <section className="grid gap-5">
          <div className="panel p-5">
            <h1 className="text-lg font-bold">Natural-language analytics</h1>
            <div className="mt-4 grid gap-3">
              <select className="field" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
                {datasets.map((d) => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
              </select>
              <textarea className="field min-h-24 py-2" value={question} onChange={(e) => setQuestion(e.target.value)} />
              <button className="btn w-fit" onClick={ask}><ShieldCheck size={16} /> Generate governed SQL</button>
            </div>
          </div>
          {query && (
            <div className="panel p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold">SQL approval gate</h2>
                <div className="flex gap-2"><Status value={query.safety_status} /><Status value={query.approval_status} /></div>
              </div>
              <pre className="mt-4 overflow-auto rounded-md bg-[#0f172a] p-4 text-sm text-white">{query.generated_sql}</pre>
              <p className="mt-3 text-sm text-muted">{query.explanation}</p>
              {query.safety_findings?.length > 0 && <div className="mt-3 text-sm text-red-700">{query.safety_findings.join(", ")}</div>}
              <div className="mt-4 flex gap-2">
                <button className="btn secondary" onClick={approve}>Approve</button>
                <button className="btn" onClick={execute}><Play size={16} /> Execute</button>
              </div>
            </div>
          )}
          {message && <div className="panel p-3 text-sm">{message}</div>}
          {chart && <Chart spec={chart} />}
          <DataTable rows={rows} />
        </section>
        <aside className="panel p-5">
          <h2 className="text-base font-bold">Query history</h2>
          <div className="mt-4 space-y-3">
            {history.slice(0, 10).map((item) => (
              <button className="w-full rounded-md border border-line p-3 text-left" key={item.id} onClick={() => setQuery(item)}>
                <div className="mb-2 flex justify-between"><Status value={item.safety_status} /><Status value={item.approval_status} /></div>
                <code className="text-xs text-muted">{item.generated_sql}</code>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
