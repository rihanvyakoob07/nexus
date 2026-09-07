"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CapabilityBar from "@/components/CapabilityBar";
import { apiFetch, hasRole } from "@/lib/api";

type Capability = { skill_name: string; category: string; engineer_count: number; avg_confidence: number };

export default function CapabilitiesPage() {
  const [rows, setRows] = useState<Capability[] | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("leadership", "admin")) { setError("Leadership or admin access is required."); return; } apiFetch<Capability[]>("/dashboard/capabilities").then(setRows).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load capabilities.")); }, []);
  if (error) return <main className="text-[#F0F4FF]"><p className="text-[#EF4444]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#00B5E2]">Sign in</Link></main>;
  if (!rows) return <main className="text-[#8899BB]">Loading capabilities...</main>;
  return <div><header className="mb-8"><p className="hcl-label">Leadership portal</p><h1 className="mt-2 text-2xl font-semibold">Organisation capabilities</h1><p className="mt-2 text-[#8899BB]">Supply-side coverage calculated from engineer skills in SQLite.</p></header><div className="grid gap-4 md:grid-cols-2">{rows.length ? rows.map((row) => <article key={row.skill_name} className="hcl-card p-5"><div className="mb-3 flex items-center justify-between"><div><p className="font-medium">{row.skill_name}</p><p className="text-xs text-[#8899BB]">{row.category} · {row.engineer_count} engineers</p></div><span className="text-sm text-[#00B5E2]">{row.avg_confidence}/10</span></div><CapabilityBar label="Average confidence" value={Math.round(row.avg_confidence * 10)} tone="sky" /></article>) : <div className="hcl-card p-8 text-sm text-[#8899BB]">No capability records found.</div>}</div></div>;
}
