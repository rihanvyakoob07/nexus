"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, hasRole } from "@/lib/api";
import type { Engineer } from "@/types/api";

export default function AdminEngineersPage() {
  const [engineers, setEngineers] = useState<Engineer[] | null>(null); const [query, setQuery] = useState(""); const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!hasRole("admin", "leadership")) { setError("Admin or leadership access is required."); return; } apiFetch<Engineer[]>("/engineers/").then(setEngineers).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load engineers.")); }, []);
  if (error) return <main className="text-[#F0F4FF]"><p className="text-[#EF4444]">{error}</p><Link href="/login" className="mt-4 inline-block text-[#00B5E2]">Sign in</Link></main>;
  if (!engineers) return <main className="text-[#8899BB]">Loading engineers...</main>;
  const filtered = engineers.filter((engineer) => `${engineer.name} ${engineer.email} ${engineer.seniority ?? ""}`.toLowerCase().includes(query.toLowerCase()));
  return <div><header className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="hcl-label">Admin portal</p><h1 className="mt-2 text-2xl font-semibold">Engineers</h1><p className="mt-2 text-[#8899BB]">Browse the engineer capability graph.</p></div><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search engineers" className="hcl-input w-full sm:w-72" /></header><div className="hcl-table"><table className="w-full text-left text-sm"><thead className="bg-[#1A2235] text-xs uppercase tracking-widest text-[#8899BB]"><tr><th className="p-4">Name</th><th className="p-4">Email</th><th className="p-4">Seniority</th><th className="p-4">Role</th><th className="p-4" /></tr></thead><tbody>{filtered.map((engineer) => <tr key={engineer.id} className="border-b border-[#1E2D45] hover:bg-[#1A2235]"><td className="p-4 font-medium">{engineer.name}</td><td className="p-4 text-[#8899BB]">{engineer.email}</td><td className="p-4">{engineer.seniority ?? "-"}</td><td className="p-4 text-[#8899BB]">{engineer.role}</td><td className="p-4"><Link href={`/engineer/passport?engineer_id=${engineer.id}`} className="text-[#00B5E2]">Passport</Link></td></tr>)}</tbody></table>{!filtered.length ? <p className="p-6 text-sm text-[#8899BB]">No engineers found.</p> : null}</div></div>;
}
