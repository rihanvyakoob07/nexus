type Skill = { name: string; score: number; category: string };
type SkillRadarChartProps = { skills: Skill[] };

export default function SkillRadarChart({ skills }: SkillRadarChartProps) {
  return (
    <div className="hcl-card p-5">
      <div className="mb-5 flex items-center justify-between"><div><p className="hcl-label">Capability profile</p><h3 className="mt-1 text-lg font-semibold text-[#172033]">Evidence confidence by skill</h3></div><span className="rounded-full bg-[#EEF5FF] px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[#0F5FDC]">Current</span></div>
      <div className="space-y-4">{skills.map((skill) => <div key={skill.name}><div className="mb-1 flex items-center justify-between text-xs font-medium text-[#475569]"><span>{skill.name}</span><span className="text-[#172033]">{skill.score}%</span></div><div className="h-2.5 rounded-full bg-[#E8EDF4]"><div className="h-full rounded-full bg-gradient-to-r from-[#0F5FDC] to-[#6B2FB5]" style={{ width: `${Math.max(0, Math.min(100, skill.score))}%` }} /></div></div>)}</div>
    </div>
  );
}
