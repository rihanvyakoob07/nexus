"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAdminTeams, hasRole } from "@/lib/api";
import type { AdminTeam } from "@/types/api";

export default function AdminTeamsPage() {
  const [teams, setTeams] = useState<AdminTeam[] | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("admin", "leadership")) { setError("Admin or leadership access is required."); return; } getAdminTeams().then(setTeams).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load teams.")); }, []);
  if (error) return <main className="text-[#F0F4FF]"><p className="text-[#EF4444]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#00B5E2]">Sign in</Link></main>;
  if (!teams) return <main className="text-[#8899BB]">Loading teams...</main>;
  return <div><header className="mb-8 flex items-end justify-between"><div><p className="hcl-label">Admin portal</p><h1 className="mt-2 text-2xl font-semibold">Teams</h1><p className="mt-2 text-[#8899BB]">Persisted team compositions and engagement scores.</p></div><Link href="/admin/teams/compose" className="hcl-button-primary">Compose team</Link></header><section className="grid gap-4 lg:grid-cols-2">{teams.length ? teams.map((team) => <article key={team.id} className="hcl-card p-6"><div className="flex items-start justify-between"><div><p className="hcl-label">{team.client_name}</p><h2 className="mt-2 text-lg font-semibold">Team #{team.id}</h2></div><span className="rounded-full bg-[#00D4AA]/10 px-2 py-1 text-xs text-[#00D4AA]">{team.risk_level} risk</span></div><div className="mt-5 grid grid-cols-2 gap-4"><div><p className="hcl-label">Team capability</p><p className="mt-2 text-2xl font-semibold text-[#00B5E2]">{team.team_capability_score ?? "-"}</p></div><div><p className="hcl-label">Engagement score</p><p className="mt-2 text-2xl font-semibold text-[#00D4AA]">{team.engagement_capability_score ?? "-"}</p></div></div><p className="mt-5 text-sm text-[#8899BB]">{team.composition.length} members persisted in this roster.</p></article>) : <div className="hcl-card p-8 text-sm text-[#8899BB]">No teams composed yet.</div>}</section></div>;
}
