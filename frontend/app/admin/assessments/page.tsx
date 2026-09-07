"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAdminAssessments, hasRole } from "@/lib/api";
import type { AdminAssessment } from "@/types/api";

export default function AdminAssessmentsPage() {
  const [rows, setRows] = useState<AdminAssessment[] | null>(null); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("admin", "leadership")) { setError("Admin or leadership access is required."); return; } getAdminAssessments().then(setRows).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load assessments.")); }, []);
  if (error) return <main className="text-[#F0F4FF]"><p className="text-[#EF4444]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#00B5E2]">Sign in</Link></main>;
  if (!rows) return <main className="text-[#8899BB]">Loading assessments...</main>;
  return <div><header className="mb-8"><p className="hcl-label">Admin portal</p><h1 className="mt-2 text-2xl font-semibold">Assessment review</h1><p className="mt-2 text-[#8899BB]">Review every JD-specific Arena assessment.</p></header><div className="hcl-table"><table className="w-full text-left text-sm"><thead className="bg-[#1A2235] text-xs uppercase tracking-widest text-[#8899BB]"><tr><th className="p-4">Engineer</th><th className="p-4">Opportunity</th><th className="p-4">Status</th><th className="p-4">Technical</th><th className="p-4">Readiness</th><th className="p-4" /></tr></thead><tbody>{rows.map((row) => <tr key={row.id} className="border-b border-[#1E2D45] hover:bg-[#1A2235]"><td className="p-4">{row.engineer_name}</td><td className="p-4">{row.client_name}</td><td className="p-4 text-[#8899BB]">{row.status}</td><td className="p-4 text-[#00D4AA]">{row.overall_score ?? "-"}</td><td className="p-4 text-[#00B5E2]">{row.readiness_score ?? "-"}</td><td className="p-4"><Link href={`/engineer/assessment/${row.id}`} className="text-[#00B5E2]">Open</Link></td></tr>)}</tbody></table>{!rows.length ? <p className="p-6 text-sm text-[#8899BB]">No assessments recorded.</p> : null}</div></div>;
}
