"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getLeadershipAnalytics, hasRole } from "@/lib/api";
import type { LeadershipAnalytics } from "@/types/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<LeadershipAnalytics | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("leadership", "admin")) { setError("Leadership or admin access is required."); return; } getLeadershipAnalytics().then(setData).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load analytics.")); }, []);
  if (error) return <main className="text-[#F0F4FF]"><p className="text-[#EF4444]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#00B5E2]">Sign in</Link></main>;
  if (!data) return <main className="text-[#8899BB]">Loading analytics...</main>;
  return <div><header className="mb-8"><p className="hcl-label">Leadership portal</p><h1 className="mt-2 text-2xl font-semibold">Delivery analytics</h1><p className="mt-2 text-[#8899BB]">Assessment and deployment outcomes from the backend data store.</p></header><section className="grid gap-4 md:grid-cols-3">{[["Assessment completion", `${data.assessment_completion_rate}%`], ["Average readiness", data.average_readiness], ["Deployments", data.deployment_count]].map(([label, value]) => <div key={String(label)} className="hcl-card p-5"><p className="hcl-label">{label}</p><p className="mt-3 text-3xl font-semibold text-[#00B5E2]">{value}</p></div>)}</section><section className="mt-6 hcl-card p-6"><h2 className="text-lg font-semibold">Assessment throughput</h2><p className="mt-3 text-[#8899BB]">{data.completed_assessments} of {data.assessment_count} assessments have completed.</p><div className="mt-4 h-3 overflow-hidden rounded-full bg-[#1E2D45]"><div className="h-full bg-gradient-to-r from-[#00B5E2] to-[#7B2D8B]" style={{ width: `${data.assessment_completion_rate}%` }} /></div></section></div>;
}
