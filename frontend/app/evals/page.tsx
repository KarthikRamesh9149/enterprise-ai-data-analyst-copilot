"use client";

import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { DataTable } from "@/components/DataTable";
import { api } from "@/lib/api";

export default function EvalsPage() {
  const [role, setRole] = useState("viewer");
  const [runs, setRuns] = useState<Record<string, unknown>[]>([]);
  const [summary, setSummary] = useState<any>({});
  const load = () => {
    api<Record<string, unknown>[]>("/evals/runs").then(setRuns).catch(() => {});
    api<any>("/evals/summary").then(setSummary).catch(() => {});
  };
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    load();
  }, []);
  async function run() {
    await api("/evals/run", { method: "POST", body: JSON.stringify({ name: "ui-mock-eval", dataset_name: "demo-churn" }) });
    load();
  }
  return (
    <AppShell role={role}>
      <section className="grid grid-cols-3 gap-4">
        <div className="panel p-4"><div className="text-xs font-bold uppercase text-muted">Cases</div><div className="mt-2 text-2xl font-bold">{summary.cases ?? 0}</div></div>
        <div className="panel p-4"><div className="text-xs font-bold uppercase text-muted">Passed</div><div className="mt-2 text-2xl font-bold">{summary.passed ?? 0}</div></div>
        <div className="panel p-4"><div className="text-xs font-bold uppercase text-muted">Pass rate</div><div className="mt-2 text-2xl font-bold">{Math.round((summary.pass_rate ?? 0) * 100)}%</div></div>
      </section>
      <section className="panel mt-5 p-5">
        <div className="flex justify-between">
          <h1 className="text-lg font-bold">Evaluation runner</h1>
          <button className="btn" onClick={run}><ShieldCheck size={16} /> Run evals</button>
        </div>
      </section>
      <div className="mt-5"><DataTable rows={runs} /></div>
    </AppShell>
  );
}
