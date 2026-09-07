"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DemandRadarChart from "@/components/DemandRadarChart";
import { getLeadershipDemand, hasRole } from "@/lib/api";
import type { DemandResponse } from "@/types/api";

export default function DemandPage() {
  const [data, setData] = useState<DemandResponse | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("leadership", "admin")) { setError("Leadership or admin access is required."); return; } getLeadershipDemand().then(setData).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load demand data.")); }, []);
  if (error) return <main className="text-[#F0F4FF]"><p className="text-[#EF4444]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#00B5E2]">Sign in</Link></main>;
  if (!data) return <main className="text-[#8899BB]">Loading demand and supply...</main>;
  return <div><header className="mb-8"><p className="hcl-label">Leadership portal</p><h1 className="mt-2 text-2xl font-semibold">Demand and supply</h1><p className="mt-2 text-[#8899BB]">Active published opportunities and their capability demand.</p></header><div className="grid gap-6 lg:grid-cols-[1fr_1fr]"><DemandRadarChart items={data.demand_radar} /><div className="hcl-card p-6"><h2 className="text-lg font-semibold">Active opportunities</h2><div className="mt-4 space-y-3">{data.opportunities.length ? data.opportunities.map((opportunity) => <Link key={opportunity.id} href={`/admin/jds/${opportunity.id}/matches`} className="block rounded-lg border border-[#1E2D45] p-4 hover:bg-[#1A2235]"><div className="flex justify-between"><span>{opportunity.client_name}</span><span className="text-xs uppercase text-[#00D4AA]">{opportunity.status}</span></div><p className="mt-1 text-xs text-[#8899BB]">JD #{opportunity.id}</p></Link>) : <p className="text-sm text-[#8899BB]">No published opportunities.</p>}</div></div></div></div>;
}
