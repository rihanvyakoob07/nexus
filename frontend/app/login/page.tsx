"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { getRole, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@nexus.ai");
  const [password, setPassword] = useState("nexus123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      const role = getRole();
      router.push(role === "leadership" ? "/leadership/dashboard" : role === "admin" ? "/admin/jds" : "/engineer/passport");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-50">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900/80 p-8">
        <p className="text-xs uppercase tracking-[0.3em] text-sky-300">NEXUS V3</p>
        <h1 className="mt-3 text-3xl font-bold text-white">Sign in</h1>
        <p className="mt-2 text-sm text-slate-400">Use your NEXUS account to access live capability data.</p>
        <label className="mt-8 block text-sm text-slate-300">Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-white outline-none focus:border-sky-500" required /></label>
        <label className="mt-4 block text-sm text-slate-300">Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-white outline-none focus:border-sky-500" required /></label>
        {error ? <p className="mt-4 rounded-xl bg-rose-500/10 p-3 text-sm text-rose-300">{error}</p> : null}
        <button disabled={loading} className="mt-6 w-full rounded-full bg-sky-500 px-4 py-3 text-sm font-medium text-slate-950 disabled:cursor-wait disabled:opacity-60">{loading ? "Signing in..." : "Sign in"}</button>
      </form>
    </main>
  );
}
