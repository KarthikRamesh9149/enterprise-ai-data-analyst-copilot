"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  async function submit() {
    await api("/auth/register", { method: "POST", body: JSON.stringify({ email, password, role: "viewer" }) });
    router.push("/");
  }
  return (
    <main className="grid min-h-screen place-items-center">
      <section className="panel w-full max-w-md p-6">
        <h1 className="text-xl font-bold">Create local account</h1>
        <div className="mt-5 space-y-3">
          <input className="field" placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="field" placeholder="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <div className="rounded-md border border-line bg-[#f8fafc] p-3 text-sm text-muted">New accounts start as viewer. Seeded local users provide analyst, reviewer, and admin roles.</div>
          <button className="btn w-full justify-center" onClick={submit}>Register</button>
        </div>
      </section>
    </main>
  );
}
