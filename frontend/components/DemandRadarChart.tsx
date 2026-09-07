"use client";

import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DemandRadarItem } from "@/types/api";

export default function DemandRadarChart({ items }: { items: DemandRadarItem[] }) {
  if (!items.length) return <div className="flex h-72 items-center justify-center rounded-3xl border border-slate-800 bg-slate-900/80 p-5 text-sm text-slate-400">No demand data available.</div>;
  return <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5"><div className="mb-3 flex items-center justify-between"><h2 className="text-xl font-semibold text-white">Future demand radar</h2><span className="text-xs uppercase tracking-[0.2em] text-slate-400">From active JDs</span></div><div className="h-72"><ResponsiveContainer width="100%" height="100%"><RadarChart data={items.slice(0, 8)}><PolarGrid stroke="#29425d" /><PolarAngleAxis dataKey="skill_name" tick={{ fill: "#cbd5e1", fontSize: 11 }} /><PolarRadiusAxis tick={{ fill: "#94a3b8", fontSize: 10 }} /><Radar name="Demand" dataKey="demand_count" stroke="#e31b23" fill="#e31b23" fillOpacity={0.35} /><Tooltip contentStyle={{ background: "#071a33", border: "1px solid #29425d", color: "#fff" }} /></RadarChart></ResponsiveContainer></div></div>;
}
