"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CapabilityBar from "@/components/CapabilityBar";
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
    try { setData(await apiFetch<LeadershipDashboard>("/dashboard/leadership")); setError(null); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load leadership dashboard."); }
    finally { setLoading(false); }
  }

  useEffect(() => { if (!hasRole("leadership", "admin")) { setError("Leadership or admin access is required."); setLoading(false); return; } void load(); }, []);
  if (loading) return <main className="text-[#64748B]">Loading leadership data...</main>;
  if (error || !data) return <main className="hcl-card max-w-3xl p-6"><p className="text-[#B42318]">{error ?? "No leadership data available."}</p><button onClick={() => void load()} className="hcl-button-primary mt-5">Retry</button></main>;

  const radarSkills = data.capability_coverage.slice(0, 6).map((item) => ({ name: item.skill_name, score: Math.round(item.avg_confidence * 10), category: item.category }));
  const averageCoverage = data.capability_coverage.length ? data.capability_coverage.reduce((sum, item) => sum + item.coverage_pct, 0) / data.capability_coverage.length : 0;

  return <div>
    <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="hcl-label">Leadership workspace</p><h1 className="mt-2 text-3xl font-bold tracking-tight">Capability readiness</h1><p className="mt-2 max-w-2xl text-sm text-[#64748B]">Current engineering supply, published demand, capability coverage and delivery signals.</p></div><div className="flex gap-3"><Link href="/leadership/whatif" className="hcl-button-primary">Run capacity scenario</Link><button onClick={() => void load()} className="hcl-button-secondary">Refresh</button></div></header>

    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[["Engineers", data.total_engineers], ["Published JDs", data.total_jds], ["Deployments / 30 days", data.deployment_velocity], ["AI cost / 30 days", `$${data.agent_cost_last_30d.toFixed(4)}`]].map(([label, value]) => <div key={String(label)} className="hcl-card p-5"><p className="hcl-label">{label}</p><p className="mt-3 text-3xl font-bold text-[#172033]">{value}</p></div>)}</section>

    <section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]"><div className="hcl-card p-6"><p className="hcl-label">Supply coverage</p><h2 className="mt-1 text-xl font-semibold">Current capability coverage</h2><div className="mt-6 space-y-5">{data.capability_coverage.length ? data.capability_coverage.slice(0, 8).map((item) => <CapabilityBar key={item.skill_name} label={item.skill_name} value={Math.round(item.coverage_pct)} subtitle={`${item.engineer_count} engineers · ${item.avg_confidence} evidence confidence`} tone="sky" />) : <p className="text-sm text-[#64748B]">No capability records found.</p>}</div></div><div className="space-y-6"><SkillRadarChart skills={radarSkills} /><ReadinessGauge score={Math.round(averageCoverage)} label="Average supply coverage" /></div></section>

    <section className="mt-6 grid gap-6 lg:grid-cols-2"><div className="hcl-card p-6"><p className="hcl-label">Current demand</p><h2 className="mt-1 text-xl font-semibold">Skills requested by published JDs</h2><div className="mt-5 space-y-3">{data.demand_radar.length ? data.demand_radar.slice(0, 10).map((item) => <div key={item.skill_name} className="flex items-center justify-between rounded-xl border border-[#DFE4EC] bg-[#F8FAFC] p-4"><div><p className="text-sm font-semibold text-[#172033]">{item.skill_name}</p><p className="mt-1 text-xs text-[#64748B]">Weighted priority {item.avg_priority_weight}</p></div><span className="rounded-full bg-[#EEF5FF] px-3 py-1 text-xs font-bold text-[#0F5FDC]">{item.demand_count} requirements</span></div>) : <p className="text-sm text-[#64748B]">No published demand yet.</p>}</div></div><div className="rounded-2xl border border-[#F1D7A7] bg-[#FFF9ED] p-6"><p className="hcl-label">Actionable gaps</p><h2 className="mt-1 text-xl font-semibold text-[#172033]">Skills needing attention</h2>{data.gap_alerts.length ? <div className="mt-5 space-y-3">{data.gap_alerts.map((gap) => <div key={`${gap.skill_name}-${gap.severity}`} className="rounded-xl border border-[#F1D7A7] bg-white p-4"><div className="flex items-center justify-between"><p className="font-semibold text-[#172033]">{gap.skill_name}</p><span className="text-xs font-bold uppercase text-[#A15C00]">{gap.severity}</span></div><p className="mt-1 text-sm text-[#64748B]">{gap.engineer_gap_count} engineer gaps</p></div>)}</div> : <p className="mt-4 text-sm text-[#64748B]">No active capability gaps.</p>}</div></section>
  </div>;
}
