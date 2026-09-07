"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CapabilityBar } from "@/components/CapabilityBar";
import ReadinessGauge from "@/components/ReadinessGauge";
import { apiFetch, getMyApplications, hasRole } from "@/lib/api";
import type { Application, EngineerDashboard } from "@/types/api";

export default function EngineerDashboardPage() {
  const [data, setData] = useState<EngineerDashboard | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!hasRole("engineer")) { setError("Engineer access is required."); return; }
    Promise.all([apiFetch<EngineerDashboard>("/dashboard/engineer"), getMyApplications()])
      .then(([dashboard, apps]) => { setData(dashboard); setApplications(apps); })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load engineer dashboard."));
  }, []);

  if (error) return <main className="text-[#172033]"><p className="text-[#B42318]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#0F5FDC]">Sign in</Link></main>;
  if (!data) return <main className="text-[#64748B]">Loading engineer dashboard...</main>;

  const readiness = Math.round(data.readiness_score * 10);
  const evidence = Math.round(data.evidence_confidence * 10);
  const assessment = data.assessment_score == null ? null : Math.round(data.assessment_score * 10);

  return <div>
    <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div><p className="hcl-label">Engineer workspace</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-[#172033]">Your capability readiness</h1><p className="mt-2 max-w-2xl text-sm text-[#64748B]">A transparent view of your current evidence, validated capability, skill gaps and relevant opportunities.</p></div>
      <Link href="/engineer/profile" className="hcl-button-secondary">Update profile</Link>
    </header>

    <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="hcl-card p-5"><p className="hcl-label">Readiness</p><p className="mt-3 text-3xl font-bold text-[#0F5FDC]">{readiness}%</p><p className="mt-1 text-xs text-[#64748B]">Evidence + latest assessment</p></div>
      <div className="hcl-card p-5"><p className="hcl-label">Evidence confidence</p><p className="mt-3 text-3xl font-bold text-[#172033]">{evidence}%</p><p className="mt-1 text-xs text-[#64748B]">Current skill evidence</p></div>
      <div className="hcl-card p-5"><p className="hcl-label">Critical gaps</p><p className="mt-3 text-3xl font-bold text-[#A15C00]">{data.critical_gaps}</p><p className="mt-1 text-xs text-[#64748B]">High or critical priority</p></div>
      <div className="hcl-card p-5"><p className="hcl-label">Applications</p><p className="mt-3 text-3xl font-bold text-[#172033]">{applications.length}</p><p className="mt-1 text-xs text-[#64748B]">Submitted opportunities</p></div>
    </section>

    <section className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
      <div className="hcl-card p-6"><ReadinessGauge score={readiness} label="Readiness score" /><div className="mt-6 rounded-xl bg-[#F2F5FA] p-4"><p className="text-xs font-semibold uppercase tracking-widest text-[#64748B]">How this is calculated</p><p className="mt-2 text-sm leading-6 text-[#475569]">Readiness combines current evidence confidence with the latest completed technical assessment when available. No assessment means no invented assessment signal.</p>{assessment !== null && <p className="mt-3 text-sm font-semibold text-[#172033]">Latest assessment: {assessment}%</p>}</div></div>
      <div className="hcl-card p-6"><div className="mb-5 flex items-center justify-between"><div><p className="hcl-label">Opportunity matching</p><h2 className="mt-1 text-lg font-semibold text-[#172033]">Recommended opportunities</h2></div><Link href="/engineer/opportunities" className="text-sm font-semibold text-[#0F5FDC]">View all</Link></div>{data.matched_opportunities.length ? <div className="space-y-5">{data.matched_opportunities.slice(0, 3).map((item) => <div key={item.jd_id}><div className="flex justify-between text-sm font-medium"><span>{item.client}</span><span className="text-[#147D64]">{Math.round(item.match_score)}% match</span></div><CapabilityBar label="Capability match" value={Math.round(item.match_score)} subtitle={item.explanation ?? "Match explanation unavailable."} tone="sky" /></div>)}</div> : <p className="text-sm text-[#64748B]">No matched opportunities yet.</p>}</div>
    </section>

    <section className="mt-6 hcl-card p-6"><div className="mb-4 flex items-center justify-between"><div><p className="hcl-label">Next actions</p><h2 className="mt-1 text-lg font-semibold">Close your highest-value gaps</h2></div><Link href="/engineer/gaps" className="text-sm font-semibold text-[#0F5FDC]">View gaps</Link></div><div className="grid gap-3 md:grid-cols-3"><div className="rounded-xl border border-[#DFE4EC] bg-[#F8FAFC] p-4"><p className="text-sm font-semibold">Review evidence</p><p className="mt-1 text-xs leading-5 text-[#64748B]">Keep recent project and delivery evidence attached to your skills.</p></div><div className="rounded-xl border border-[#DFE4EC] bg-[#F8FAFC] p-4"><p className="text-sm font-semibold">Complete assessment</p><p className="mt-1 text-xs leading-5 text-[#64748B]">A validated assessment makes your readiness signal stronger.</p></div><div className="rounded-xl border border-[#DFE4EC] bg-[#F8FAFC] p-4"><p className="text-sm font-semibold">Follow the learning path</p><p className="mt-1 text-xs leading-5 text-[#64748B]">Prioritize learning tied directly to a measurable target skill.</p></div></div></section>

    <section className="mt-6 hcl-card p-6"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">Active applications</h2><Link href="/engineer/applications" className="text-sm font-semibold text-[#0F5FDC]">Open applications</Link></div>{applications.length ? <div className="grid gap-3 md:grid-cols-2">{applications.slice(0, 4).map((application) => <div key={application.id} className="rounded-xl border border-[#DFE4EC] bg-[#F8FAFC] p-4"><p className="font-medium text-[#172033]">{application.client_name ?? `JD #${application.jd_id}`}</p><span className="mt-2 inline-block rounded-full bg-[#EEF5FF] px-2.5 py-1 text-xs font-semibold uppercase text-[#0F5FDC]">{application.status.replaceAll("_", " ")}</span></div>)}</div> : <p className="text-sm text-[#64748B]">You haven&apos;t applied to any opportunities yet.</p>}</section>
  </div>;
}
