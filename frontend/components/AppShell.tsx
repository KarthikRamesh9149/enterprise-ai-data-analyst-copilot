"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, BarChart3, ClipboardCheck, Database, FileText, Gauge, LineChart, LogOut, ShieldCheck, Sparkles, Users } from "lucide-react";
import { clearSession } from "@/lib/api";

const nav = [
  { href: "/", label: "Dashboard", icon: Gauge, roles: ["admin", "analyst", "reviewer", "viewer"] },
  { href: "/datasets", label: "Datasets", icon: Database, roles: ["admin", "analyst"] },
  { href: "/analytics", label: "Analytics", icon: BarChart3, roles: ["admin", "analyst", "reviewer", "viewer"] },
  { href: "/modeling", label: "Modeling", icon: Sparkles, roles: ["admin", "analyst"] },
  { href: "/forecasting", label: "Forecasting", icon: LineChart, roles: ["admin", "analyst"] },
  { href: "/reports", label: "Reports", icon: FileText, roles: ["admin", "analyst", "reviewer", "viewer"] },
  { href: "/approvals", label: "Approvals", icon: ClipboardCheck, roles: ["admin", "reviewer"] },
  { href: "/evals", label: "Evaluations", icon: ShieldCheck, roles: ["admin"] },
  { href: "/admin", label: "Admin", icon: Users, roles: ["admin"] },
];

export function AppShell({ children, role = "viewer" }: { children: React.ReactNode; role?: string }) {
  const pathname = usePathname();
  const router = useRouter();
  return (
    <div className="grid min-h-screen grid-cols-[244px_1fr] bg-[#f7f9fc]">
      <aside className="border-r border-line bg-white">
        <div className="flex h-16 items-center gap-3 border-b border-line px-5">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-[#12312f] text-white">
            <Activity size={18} />
          </div>
          <div>
            <div className="text-sm font-bold leading-5">AI Data Copilot</div>
            <div className="text-xs text-muted">Local enterprise demo</div>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {nav
            .filter((item) => item.roles.includes(role))
            .map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-semibold ${
                    active ? "bg-[#e8f3f1] text-[#0f766e]" : "text-[#334155] hover:bg-[#f1f5f9]"
                  }`}
                >
                  <Icon size={17} />
                  {item.label}
                </Link>
              );
            })}
        </nav>
      </aside>
      <main>
        <header className="flex h-16 items-center justify-between border-b border-line bg-white px-6">
          <div>
            <div className="text-sm font-bold">Enterprise AI Data Analyst & Forecasting Copilot</div>
            <div className="text-xs text-muted">SQL governance, ML, forecasting, reports, evals, observability</div>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-md border border-line bg-[#f8fafc] px-2 py-1 text-xs font-bold uppercase text-muted">{role}</span>
            <button
              className="btn secondary"
              onClick={async () => {
                await clearSession();
                router.push("/login");
              }}
              title="Log out"
            >
              <LogOut size={15} /> Log out
            </button>
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
