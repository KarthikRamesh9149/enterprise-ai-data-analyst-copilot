"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Status } from "@/components/Status";
import { api } from "@/lib/api";
import type { Approval } from "@/types/api";

export default function ApprovalsPage() {
  const [role, setRole] = useState("viewer");
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const load = () => api<Approval[]>("/approvals").then(setApprovals).catch(() => {});
  useEffect(() => {
    api<any>("/auth/me").then((u) => setRole(u.role)).catch(() => {});
    load();
  }, []);
  async function review(id: string, action: "approve" | "reject") {
    await api(`/approvals/${id}/${action}`, { method: "POST", body: JSON.stringify({ reviewer_notes: `${action} from UI` }) });
    load();
  }
  return (
    <AppShell role={role}>
      <section className="panel p-5">
        <h1 className="text-lg font-bold">Approval queue</h1>
        <table className="table mt-4">
          <thead><tr><th>Action</th><th>Resource</th><th>Reason</th><th>Status</th><th>Review</th></tr></thead>
          <tbody>
            {approvals.map((a) => (
              <tr key={a.id}>
                <td>{a.action_type}</td>
                <td>{a.resource_type}</td>
                <td>{a.request_reason}</td>
                <td><Status value={a.status} /></td>
                <td className="flex gap-2">
                  <button className="btn secondary" onClick={() => review(a.id, "approve")}><Check size={14} /> Approve</button>
                  <button className="btn secondary" onClick={() => review(a.id, "reject")}><X size={14} /> Reject</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}
