"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, hasRole } from "@/lib/api";
import type { Assessment, EngineerDashboard } from "@/types/api";

export default function AssessmentsPage() {
  const [assessments, setAssessments] = useState<Assessment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("engineer")) { setError("Engineer access is required."); return; } apiFetch<EngineerDashboard>("/dashboard/engineer").then((dashboard) => apiFetch<Assessment[]>(`/engineers/${dashboard.engineer_id}/assessments`)).then(setAssessments).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load assessments.")); }, []);
  if (error) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><p className="text-rose-300">{error}</p><Link href="/login" className="mt-4 inline-block text-sky-300">Sign in</Link></main>;
  if (!assessments) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading assessments...</main>;
  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-5xl"><Link href="/engineer/passport" className="text-sm text-sky-300">← Capability passport</Link><div className="mt-8 border-b border-slate-800 pb-6"><p className="text-xs uppercase tracking-[0.3em] text-violet-300">Engineer workspace</p><h1 className="mt-2 text-4xl font-bold text-white">JD-specific assessments</h1><p className="mt-3 text-slate-400">Every Arena session is tied to a concrete opportunity and its capabilities.</p></div><section className="mt-8 space-y-3">{assessments.length ? assessments.map((assessment) => <article key={assessment.id} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">Assessment #{assessment.id} · JD #{assessment.jd_id}</h2><p className="mt-1 text-sm text-slate-400">{assessment.turns.length} turns · {assessment.status}</p></div>{assessment.status === "pending" || assessment.status === "in_progress" ? <Link href={`/engineer/assessment/${assessment.id}`} className="rounded-full bg-sky-500 px-4 py-2 text-sm text-slate-950">Open Arena</Link> : <Link href={`/engineer/assessment/${assessment.id}`} className="rounded-full border border-slate-700 px-4 py-2 text-sm">View result</Link>}</div></article>) : <div className="rounded-3xl border border-slate-800 p-6 text-slate-400">No assessment history yet.</div>}</section></div></main>;
}
