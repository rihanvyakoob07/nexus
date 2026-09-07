"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { getRole, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      const role = getRole();
      router.push(role === "leadership" ? "/leadership/dashboard" : role === "admin" ? "/admin/dashboard" : "/engineer/dashboard");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#F7F8FB] px-6 py-12 text-[#172033]">
      <div className="mx-auto grid min-h-[75vh] max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="hidden lg:block">
          <div className="mb-8 h-1 w-24 bg-gradient-to-r from-[#0F5FDC] to-[#6B2FB5]" />
          <p className="text-sm font-bold uppercase tracking-[0.28em] text-[#0F5FDC]">NEXUS</p>
          <h1 className="mt-5 max-w-2xl text-5xl font-bold leading-tight tracking-tight text-[#172033]">Capability intelligence for <span className="bg-gradient-to-r from-[#0F5FDC] to-[#6B2FB5] bg-clip-text text-transparent">better decisions.</span></h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-[#64748B]">Turn engineering capability, evidence and delivery outcomes into a practical view of readiness, gaps and deployment options.</p>
          <div className="mt-10 flex gap-3 text-sm font-medium text-[#475569]"><span className="rounded-full border border-[#DFE4EC] bg-white px-4 py-2">Capability</span><span className="rounded-full border border-[#DFE4EC] bg-white px-4 py-2">Evidence</span><span className="rounded-full border border-[#DFE4EC] bg-white px-4 py-2">Readiness</span></div>
        </section>

        <form onSubmit={handleSubmit} className="hcl-card mx-auto w-full max-w-md p-8 sm:p-10">
          <div className="h-1 w-16 bg-gradient-to-r from-[#0F5FDC] to-[#6B2FB5]" />
          <p className="mt-6 text-xs font-bold uppercase tracking-[0.25em] text-[#0F5FDC]">NEXUS</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight">Sign in</h2>
          <p className="mt-2 text-sm leading-6 text-[#64748B]">Access your capability workspace.</p>
          <label className="mt-8 block text-sm font-semibold text-[#334155]">Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" className="hcl-input mt-2 w-full" required /></label>
          <label className="mt-4 block text-sm font-semibold text-[#334155]">Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" className="hcl-input mt-2 w-full" required /></label>
          {error ? <p role="alert" className="mt-4 rounded-lg border border-[#F1C7C4] bg-[#FEF3F2] p-3 text-sm text-[#B42318]">{error}</p> : null}
          <button disabled={loading} className="hcl-button-primary mt-6 w-full py-3">{loading ? "Signing in…" : "Sign in"}</button>
        </form>
      </div>
    </main>
  );
}
