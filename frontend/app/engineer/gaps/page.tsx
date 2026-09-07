"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, hasRole } from "@/lib/api";
import type { EngineerDashboard, SkillGap } from "@/types/api";

export default function EngineerGapsPage() {
  const [gaps, setGaps] = useState<SkillGap[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("engineer")) { setError("Engineer access is required."); return; } apiFetch<EngineerDashboard>("/dashboard/engineer").then((dashboard) => apiFetch<SkillGap[]>(`/engineers/${dashboard.engineer_id}/gaps`)).then(setGaps).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load skill gaps.")); }, []);
  if (error) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><p className="text-rose-300">{error}</p><Link href="/login" className="mt-4 inline-block text-sky-300">Sign in</Link></main>;
  if (!gaps) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading skill gaps...</main>;
  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-5xl"><Link href="/engineer/passport" className="text-sm text-sky-300">← Capability passport</Link><div className="mt-8 border-b border-slate-800 pb-6"><p className="text-xs uppercase tracking-[0.3em] text-violet-300">Capability development</p><h1 className="mt-2 text-4xl font-bold text-white">Active skill gaps</h1><p className="mt-3 text-slate-400">Current and target scores calculated by the Gap Agent.</p></div><section className="mt-8 space-y-3">{gaps.length ? gaps.map((gap) => <article key={gap.skill_id} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">{gap.skill_name}</h2><p className="mt-1 text-sm text-slate-400">{gap.severity} priority</p></div><div className="text-right"><p className="text-sm text-slate-400">Current → target</p><p className="text-xl font-semibold text-amber-300">{gap.current_score} → {gap.target_score}</p></div></div></article>) : <div className="rounded-3xl border border-slate-800 p-6 text-slate-400">No active skill gaps.</div>}</section><Link href="/engineer/learning-path" className="mt-6 inline-block rounded-full bg-sky-500 px-5 py-3 text-sm text-slate-950">Open learning path</Link></div></main>;
}
