"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { DataTable } from "@/components/DataTable";
import { api } from "@/lib/api";

export default function AdminPage() {
  const [role, setRole] = useState("viewer");
  const [analytics, setAnalytics] = useState<any>({});
  const [observability, setObservability] = useState<any>({});
  const [audits, setAudits] = useState<Record<string, unknown>[]>([]);
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    api<any>("/admin/analytics").then(setAnalytics).catch(() => {});
    api<any>("/admin/observability").then(setObservability).catch(() => {});
    api<Record<string, unknown>[]>("/admin/audit-logs").then(setAudits).catch(() => {});
  }, []);
  return (
    <AppShell role={role}>
      <section className="grid grid-cols-5 gap-4">
        {Object.entries(analytics).map(([k, v]) => (
          <div className="panel p-4" key={k}><div className="text-xs font-bold uppercase text-muted">{k}</div><div className="mt-2 text-2xl font-bold">{String(v)}</div></div>
        ))}
      </section>
      <section className="panel mt-5 p-5">
        <h1 className="text-lg font-bold">Observability</h1>
        <pre className="mt-3 rounded-md bg-[#0f172a] p-4 text-sm text-white">{JSON.stringify(observability, null, 2)}</pre>
      </section>
      <section className="mt-5">
        <h2 className="mb-3 text-base font-bold">Audit logs</h2>
        <DataTable rows={audits} />
      </section>
    </AppShell>
  );
}
