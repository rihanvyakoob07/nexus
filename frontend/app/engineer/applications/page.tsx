"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMyApplications, hasRole } from "@/lib/api";
import type { Application } from "@/types/api";

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("engineer")) { setError("Engineer access is required."); return; } getMyApplications().then(setApplications).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load applications.")); }, []);
  if (error) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><p className="text-rose-300">{error}</p><Link href="/login" className="mt-4 inline-block text-sky-300">Sign in</Link></main>;
  if (!applications) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading applications...</main>;
  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-5xl"><Link href="/engineer/opportunities" className="text-sm text-sky-300">← Opportunities</Link><div className="mt-8 border-b border-slate-800 pb-6"><p className="text-xs uppercase tracking-[0.3em] text-violet-300">Engineer workspace</p><h1 className="mt-2 text-4xl font-bold text-white">My applications</h1></div><section className="mt-8 space-y-3">{applications.length ? applications.map((application) => <article key={application.id} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">{application.client_name ?? `Opportunity #${application.jd_id}`}</h2><p className="mt-1 text-sm text-slate-400">Applied {application.applied_at.slice(0, 10)}</p></div><span className="rounded-full bg-sky-500/15 px-3 py-1 text-xs uppercase text-sky-200">{application.status.replaceAll("_", " ")}</span></div>{application.admin_notes ? <p className="mt-4 text-sm text-slate-300">{application.admin_notes}</p> : null}</article>) : <div className="rounded-3xl border border-slate-800 p-6 text-slate-400">You haven&apos;t applied to any opportunities yet.</div>}</section></div></main>;
}
