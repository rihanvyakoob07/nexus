"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CapabilityBar from "@/components/CapabilityBar";
import DemandRadarChart from "@/components/DemandRadarChart";
import ReadinessGauge from "@/components/ReadinessGauge";
import SkillRadarChart from "@/components/SkillRadarChart";
import { apiFetch, hasRole } from "@/lib/api";
import type { LeadershipDashboard } from "@/types/api";

export default function LeadershipDashboardPage() {
  const [data, setData] = useState<LeadershipDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setData(await apiFetch<LeadershipDashboard>("/dashboard/leadership"));
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load leadership dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!hasRole("leadership", "admin")) {
      setError("Leadership or admin access is required.");
      setLoading(false);
      return;
    }
    void load();
  }, []);

  if (loading) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading leadership data...</main>;
  if (error || !data) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-3xl rounded-3xl border border-rose-500/30 bg-rose-500/10 p-6"><p className="text-rose-200">{error ?? "No leadership data available."}</p><div className="mt-5 flex gap-3"><button onClick={() => void load()} className="rounded-full bg-sky-500 px-4 py-2 text-sm text-slate-950">Retry</button><Link href="/login" className="rounded-full border border-slate-600 px-4 py-2 text-sm">Sign in</Link></div></div></main>;

  const radarSkills = data.capability_coverage.slice(0, 6).map((item) => ({ name: item.skill_name, score: Math.round(item.avg_confidence * 10), category: item.category }));
  const averageCoverage = data.capability_coverage.length ? data.capability_coverage.reduce((sum, item) => sum + item.coverage_pct, 0) / data.capability_coverage.length : 0;

  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-7xl"><div className="flex items-center justify-between"><Link href="/login" className="text-sm text-sky-300 hover:text-white">Sign out</Link><button onClick={() => void load()} className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-sky-500">Refresh data</button></div><div className="mt-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-end"><div><p className="text-xs uppercase tracking-[0.3em] text-sky-300">Leadership workspace</p><h1 className="mt-2 text-4xl font-bold text-white">Portfolio readiness</h1><p className="mt-3 text-slate-400">Live coverage, demand, gaps, and agent cost from SQLite.</p></div><div className="flex gap-3"><Link href="/leadership/whatif" className="rounded-full bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950">Run what-if</Link><Link href="/leadership/observability" className="rounded-full border border-slate-700 px-4 py-2 text-sm">Observability</Link></div></div><section className="mt-8 grid gap-6 md:grid-cols-4">{[["Engineers", data.total_engineers], ["Open JDs", data.total_jds], ["Deployment velocity", data.deployment_velocity], ["Agent cost", `$${data.agent_cost_last_30d.toFixed(4)}`]].map(([label, value]) => <div key={String(label)} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5"><p className="text-sm text-slate-400">{label}</p><p className="mt-3 text-3xl font-semibold text-white">{value}</p></div>)}</section><section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]"><div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6"><h2 className="text-xl font-semibold text-white">Capability coverage</h2><div className="mt-6 space-y-5">{data.capability_coverage.length ? data.capability_coverage.slice(0, 8).map((item) => <CapabilityBar key={item.skill_name} label={item.skill_name} value={Math.round(item.coverage_pct)} subtitle={`${item.engineer_count} engineers · ${item.avg_confidence} average confidence`} tone="emerald" />) : <p className="text-sm text-slate-400">No capability coverage records found.</p>}</div></div><div className="space-y-6"><SkillRadarChart skills={radarSkills} /><ReadinessGauge score={Math.round(averageCoverage)} label="Average capability coverage" /></div></section><section className="mt-6 grid gap-6 lg:grid-cols-2"><DemandRadarChart items={data.demand_radar} /><div className="rounded-3xl border border-amber-500/30 bg-amber-500/10 p-6"><p className="text-xs uppercase tracking-[0.2em] text-amber-300">Gap alerts</p>{data.gap_alerts.length ? <div className="mt-4 space-y-3">{data.gap_alerts.map((gap) => <div key={`${gap.skill_name}-${gap.severity}`} className="rounded-2xl border border-amber-300/20 p-4"><div className="flex items-center justify-between"><p className="font-medium text-white">{gap.skill_name}</p><span className="text-xs uppercase text-amber-200">{gap.severity}</span></div><p className="mt-1 text-sm text-amber-100">{gap.engineer_gap_count} engineer gaps</p></div>)}</div> : <p className="mt-3 text-sm text-slate-300">No active gap alerts.</p>}</div></section></div></main>;
}
