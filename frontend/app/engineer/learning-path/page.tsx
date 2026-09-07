"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, hasRole } from "@/lib/api";
import type { EngineerDashboard, LearningPath } from "@/types/api";

function planEntries(plan: Record<string, unknown>) {
  return Object.entries(plan);
}

export default function LearningPathPage() {
  const [engineerId, setEngineerId] = useState<number | null>(null);
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [missing, setMissing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  async function load() {
    const dashboard = await apiFetch<EngineerDashboard>("/dashboard/engineer");
    setEngineerId(dashboard.engineer_id);
    try { setLearningPath(await apiFetch<LearningPath>(`/engineers/${dashboard.engineer_id}/learning-path`)); setMissing(false); } catch (requestError) { if (requestError instanceof Error && requestError.message === "Learning path not found") setMissing(true); else throw requestError; }
  }
  useEffect(() => { if (!hasRole("engineer")) { setError("Engineer access is required."); return; } load().catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load learning path.")); }, []);
  async function generate() { if (!engineerId) return; setGenerating(true); setError(null); try { await apiFetch(`/engineers/${engineerId}/learning-path`, { method: "POST", body: JSON.stringify({ engineer_id: engineerId }) }); await load(); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to generate learning path."); } finally { setGenerating(false); } }
  if (error && !learningPath && !missing) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><p className="text-rose-300">{error}</p><Link href="/login" className="mt-4 inline-block text-sky-300">Sign in</Link></main>;
  if (!engineerId && !error) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading learning path...</main>;
  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-5xl"><Link href="/engineer/passport" className="text-sm text-sky-300">← Capability passport</Link><div className="mt-8 border-b border-slate-800 pb-6"><p className="text-xs uppercase tracking-[0.3em] text-violet-300">Capability development</p><h1 className="mt-2 text-4xl font-bold text-white">Personalized learning path</h1><p className="mt-3 text-slate-400">Generated and persisted by the Learning Agent.</p></div>{missing ? <section className="mt-8 rounded-3xl border border-slate-800 bg-slate-900/80 p-6"><h2 className="text-xl font-semibold text-white">No learning path yet</h2><p className="mt-2 text-slate-400">Generate one from your current backend skill gaps.</p><button onClick={() => void generate()} disabled={generating} className="mt-5 rounded-full bg-sky-500 px-5 py-3 text-sm text-slate-950 disabled:opacity-60">{generating ? "Generating..." : "Generate learning path"}</button></section> : learningPath ? <section className="mt-8 rounded-3xl border border-slate-800 bg-slate-900/80 p-6"><div className="grid gap-4 md:grid-cols-3"><div><p className="text-xs uppercase tracking-[0.2em] text-slate-400">Status</p><p className="mt-2 text-2xl font-semibold text-white">{learningPath.plan.status ? String(learningPath.plan.status) : "Active"}</p></div><div><p className="text-xs uppercase tracking-[0.2em] text-slate-400">Projected score</p><p className="mt-2 text-2xl font-semibold text-emerald-400">{learningPath.projected_readiness_score ?? "Not provided"}</p></div><div><p className="text-xs uppercase tracking-[0.2em] text-slate-400">Readiness date</p><p className="mt-2 text-2xl font-semibold text-white">{learningPath.projected_readiness_date?.slice(0, 10) ?? "Not provided"}</p></div></div><div className="mt-8 space-y-3">{planEntries(learningPath.plan).map(([key, value]) => <article key={key} className="rounded-2xl border border-slate-800 p-4"><h2 className="font-medium capitalize text-white">{key.replaceAll("_", " ")}</h2><pre className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre></article>)}</div></section> : null}{error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}</div></main>;
}
