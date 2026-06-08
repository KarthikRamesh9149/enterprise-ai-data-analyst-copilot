"use client";

import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { Dataset, Report } from "@/types/api";

export default function ReportsPage() {
  const [role, setRole] = useState("viewer");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [reports, setReports] = useState<Report[]>([]);
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    api<Dataset[]>("/datasets").then((ds) => { setDatasets(ds); if (ds[0]) setDatasetId(ds[0].id); }).catch(() => {});
    api<Report[]>("/reports").then(setReports).catch(() => {});
  }, []);
  async function generate() {
    const report = await api<Report>("/reports/generate", { method: "POST", body: JSON.stringify({ dataset_id: datasetId, title: "Executive Churn and Revenue Report" }) });
    setReports([report, ...reports]);
  }
  return (
    <AppShell role={role}>
      <div className="grid grid-cols-[360px_1fr] gap-5">
        <section className="panel p-5">
          <h1 className="text-lg font-bold">Executive reports</h1>
          <div className="mt-4 grid gap-3">
            <select className="field" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
              {datasets.map((d) => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
            </select>
            <button className="btn" onClick={generate}><FileText size={16} /> Generate report</button>
          </div>
        </section>
        <section className="grid gap-4">
          {reports.map((r) => (
            <article className="panel p-5" key={r.id}>
              <h2 className="font-bold">{r.title}</h2>
              <pre className="mt-3 whitespace-pre-wrap text-sm leading-6">{r.markdown_content}</pre>
            </article>
          ))}
        </section>
      </div>
    </AppShell>
  );
}
