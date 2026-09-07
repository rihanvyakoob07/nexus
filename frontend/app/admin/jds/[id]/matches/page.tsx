"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, hasRole } from "@/lib/api";

type Matches = { jd_id: number; client_name: string; candidates: Array<{ engineer_id: number; engineer_name: string; jd_match_score: number; explanation?: string; breakdown?: Record<string, unknown> }> };

export default function MatchesPage() {
  const params = useParams<{ id: string }>();
  const [data, setData] = useState<Matches | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("admin", "leadership")) { setError("Admin or leadership access is required."); return; } apiFetch<Matches>(`/jds/${params.id}/matches`).then(setData).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load matches")); }, [params.id]);
  if (error) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><p className="text-rose-300">{error}</p><Link href="/login" className="mt-4 inline-block text-sky-300">Sign in</Link></main>;
  if (!data) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading matches...</main>;
  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-5xl"><Link href="/admin/jds" className="text-sm text-sky-300">← Admin opportunities</Link><div className="mt-8 border-b border-slate-800 pb-6"><p className="text-xs uppercase tracking-[0.3em] text-emerald-300">Match intelligence</p><h1 className="mt-2 text-4xl font-bold text-white">{data.client_name}</h1><p className="mt-3 text-slate-400">Ranked candidates returned by the Match Agent.</p></div><section className="mt-8 space-y-4">{data.candidates.length ? data.candidates.map((candidate) => <article key={candidate.engineer_id} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex items-center justify-between gap-4"><div><h2 className="text-xl font-semibold text-white">{candidate.engineer_name}</h2><p className="mt-2 text-sm text-slate-400">{candidate.explanation ?? "No explanation provided."}</p></div><span className="rounded-full bg-emerald-500/15 px-3 py-1 text-sm text-emerald-300">{Math.round(candidate.jd_match_score)}% fit</span></div></article>) : <div className="rounded-3xl border border-slate-800 p-6 text-slate-400">No candidates have been matched yet.</div>}</section><Link href="/admin/teams/compose" className="mt-6 inline-block rounded-full bg-emerald-500 px-5 py-3 text-sm text-slate-950">Compose a team</Link></div></main>;
}
