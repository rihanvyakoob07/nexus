"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ArenaChat from "@/components/ArenaChat";
import EvidenceTrail from "@/components/EvidenceTrail";
import ReadinessGauge from "@/components/ReadinessGauge";
import SkillRadarChart from "@/components/SkillRadarChart";
import { apiFetch, hasRole } from "@/lib/api";
import type { Assessment, Deployment } from "@/types/api";

type Dashboard = { engineer_id: number; overall_capability_score: number; active_gaps: number; matched_opportunities: Array<{ jd_id: number; client: string; match_score: number; explanation?: string }> };
type Passport = { name: string; seniority?: string; skills: Array<{ skill: { name: string }; confidence_score: number; source: string }>; evidence: Array<{ id: number; type: string; description?: string; date?: string }>; certifications: Array<{ id: number; name: string; issuer?: string; date?: string }> };

export default function EngineerPassportPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [passport, setPassport] = useState<Passport | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasRole("engineer")) { setError("Engineer access is required."); return; }
    apiFetch<Dashboard>("/dashboard/engineer").then(async (data) => { setDashboard(data); const [profile, history, delivery] = await Promise.all([apiFetch<Passport>(`/engineers/${data.engineer_id}`), apiFetch<Assessment[]>(`/engineers/${data.engineer_id}/assessments`), apiFetch<Deployment[]>(`/engineers/${data.engineer_id}/deployments`)]); setAssessments(history); setDeployments(delivery); return profile; }).then(setPassport).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load passport"));
  }, []);

  if (error) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-3xl rounded-3xl border border-rose-500/30 bg-rose-500/10 p-6"><p className="text-rose-200">{error}</p><Link href="/login" className="mt-5 inline-block rounded-full bg-sky-500 px-4 py-2 text-sm text-slate-950">Sign in</Link></div></main>;
  if (!dashboard || !passport) return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-400">Loading capability passport...</main>;

  const skills = passport.skills.map((item) => ({ name: item.skill.name, score: Math.round(item.confidence_score * 10), category: item.source }));
  const evidence = passport.evidence.map((item) => ({ title: item.type, detail: item.description ?? "Verified evidence", date: item.date?.slice(0, 10) ?? "Undated", type: item.type === "certification" ? "cert" as const : item.type === "assessment" ? "assessment" as const : item.type === "client_delivery" ? "client" as const : "project" as const }));

  return <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50"><div className="mx-auto max-w-7xl"><Link href="/" className="text-sm text-sky-300 hover:text-white">← NEXUS overview</Link><div className="mt-8 flex flex-col gap-5 border-b border-slate-800 pb-6 md:flex-row md:items-end md:justify-between"><div><p className="text-xs uppercase tracking-[0.3em] text-violet-300">Engineer workspace</p><h1 className="mt-2 text-4xl font-bold text-white">{passport.name}</h1><p className="mt-3 text-slate-400">{passport.seniority ?? "Engineer"} · Capability passport</p></div><Link href="/engineer/opportunities" className="rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200 hover:border-sky-500">View opportunities</Link></div><section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]"><SkillRadarChart skills={skills} /><ReadinessGauge score={Math.round(dashboard.overall_capability_score * 10)} label={`${dashboard.active_gaps} active skill gaps`} /></section><section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]"><div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6"><div className="mb-5 flex items-center justify-between"><h2 className="text-xl font-semibold text-white">Evidence trail</h2><span className="text-xs text-slate-400">{passport.evidence.length} verified signals</span></div><EvidenceTrail items={evidence} /></div><ArenaChat messages={dashboard.matched_opportunities.length ? [{ role: "assistant", text: `You have ${dashboard.matched_opportunities.length} matched opportunities in the capability graph.` }] : [{ role: "assistant", text: "No matched opportunities are available yet." }]} /></section><section className="mt-6 grid gap-6 md:grid-cols-2"><div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6"><h2 className="text-xl font-semibold text-white">Assessment history</h2>{assessments.length ? <div className="mt-4 space-y-3">{assessments.map((assessment) => <div key={assessment.id} className="rounded-2xl border border-slate-800 p-4"><div className="flex justify-between"><span className="text-white">Assessment #{assessment.id}</span><span className="text-sm text-slate-400">{assessment.status}</span></div><p className="mt-2 text-sm text-slate-400">{assessment.turns.length} turns · {assessment.started_at?.slice(0, 10) ?? "Not dated"}</p></div>)}</div> : <p className="mt-4 text-sm text-slate-400">No assessment history yet.</p>}</div><div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6"><h2 className="text-xl font-semibold text-white">Deployments</h2>{deployments.length ? <div className="mt-4 space-y-3">{deployments.map((deployment) => <div key={deployment.id} className="rounded-2xl border border-slate-800 p-4"><span className="text-white">Deployment #{deployment.id}</span><p className="mt-2 text-sm text-slate-400">JD #{deployment.jd_id} · {deployment.start_date?.slice(0, 10) ?? "Not started"}</p></div>)}</div> : <p className="mt-4 text-sm text-slate-400">No deployments recorded.</p>}</div></section></div></main>;
}
