"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("analyst@example.com");
  const [password, setPassword] = useState("DemoPassword123!");
  const [error, setError] = useState("");
  async function submit() {
    try {
      const res = await api<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setToken(res.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }
  return (
    <main className="grid min-h-screen place-items-center bg-[#f7f9fc]">
      <section className="panel w-full max-w-md p-6">
        <h1 className="text-xl font-bold">Sign in</h1>
        <p className="mt-1 text-sm text-muted">Use a seeded local demo user.</p>
        <div className="mt-5 space-y-3">
          <input className="field" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="field" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}
          <button className="btn w-full justify-center" onClick={submit}>Sign in</button>
        </div>
      </section>
    </main>
  );
}
