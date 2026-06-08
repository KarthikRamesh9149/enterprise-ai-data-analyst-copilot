"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Dataset, Query } from "@/types/api";
import { Status } from "@/components/Status";

export default function Dashboard() {
  const [role, setRole] = useState("viewer");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [queries, setQueries] = useState<Query[]>([]);
  const [admin, setAdmin] = useState<any>(null);
  useEffect(() => {
    api<any>("/auth/me")
      .then((u) => {
        setRole(u.role);
        if (u.role === "admin") {
          api<any>("/admin/analytics").then(setAdmin).catch(() => {});
        }
      })
      .catch(() => {});
    api<Dataset[]>("/datasets").then(setDatasets).catch(() => {});
    api<Query[]>("/analytics/history").then(setQueries).catch(() => {});
  }, []);
  return (
    <AppShell role={role}>
      <div className="grid gap-5">
        <section className="grid grid-cols-4 gap-4">
          {[
            ["Datasets", datasets.length],
            ["Queries", queries.length],
            ["Blocked SQL", admin?.blocked_sql ?? 0],
            ["Models", admin?.models ?? 0],
          ].map(([label, value]) => (
            <div className="panel p-4" key={label}>
              <div className="text-xs font-bold uppercase text-muted">{label}</div>
              <div className="mt-2 text-2xl font-bold">{value}</div>
            </div>
          ))}
        </section>
        <section className="grid grid-cols-[1.2fr_0.8fr] gap-5">
          <div className="panel p-5">
            <h1 className="text-lg font-bold">Question workspace</h1>
            <p className="mt-1 text-sm text-muted">Ask churn, customer risk, and revenue questions with SQL governance and traceability.</p>
            <div className="mt-4 grid gap-3">
              {queries.slice(0, 5).map((q) => (
                <div key={q.id} className="rounded-md border border-line p-3">
                  <div className="flex items-center justify-between">
                    <code className="text-xs text-muted">{q.generated_sql}</code>
                    <Status value={q.approval_status} />
                  </div>
                </div>
              ))}
              {!queries.length && <div className="text-sm text-muted">No questions yet.</div>}
            </div>
          </div>
          <div className="panel p-5">
            <h2 className="text-base font-bold">Data quality</h2>
            <div className="mt-4 space-y-3">
              {datasets.slice(0, 5).map((d) => (
                <div key={d.id} className="flex items-center justify-between rounded-md border border-line p-3">
                  <span className="text-sm font-semibold">{d.original_filename}</span>
                  <span className="text-sm font-bold text-teal">{Math.round(d.quality_score)}%</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
