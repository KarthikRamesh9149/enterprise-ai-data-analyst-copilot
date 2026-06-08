"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import { AppShell } from "@/components/AppShell";
import { DataTable } from "@/components/DataTable";
import { api } from "@/lib/api";

export default function DatasetDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [role, setRole] = useState("viewer");
  const [schema, setSchema] = useState<Record<string, unknown>[]>([]);
  const [sample, setSample] = useState<Record<string, unknown>[]>([]);
  const [profile, setProfile] = useState<any>(null);
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    api<any[]>(`/datasets/${id}/schema`).then(setSchema);
    api<any[]>(`/datasets/${id}/sample`).then(setSample);
    api<any>(`/datasets/${id}/profile`).then(setProfile);
  }, [id]);
  return (
    <AppShell role={role}>
      <div className="grid gap-5">
        <section className="panel p-5">
          <h1 className="text-lg font-bold">Schema and data quality</h1>
          <div className="mt-3 grid grid-cols-4 gap-3 text-sm">
            <div>Rows: <b>{profile?.row_count ?? "-"}</b></div>
            <div>Columns: <b>{profile?.column_count ?? "-"}</b></div>
            <div>Missing cells: <b>{profile?.missing_cells ?? "-"}</b></div>
            <div>Duplicate rows: <b>{profile?.duplicate_rows ?? "-"}</b></div>
          </div>
        </section>
        <DataTable rows={schema} />
        <DataTable rows={sample} />
      </div>
    </AppShell>
  );
}
