type Skill = {
  name: string;
  score: number;
  category: string;
};

type SkillRadarChartProps = {
  skills: Skill[];
};

export default function SkillRadarChart({ skills }: SkillRadarChartProps) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Capability radar</h3>
        <span className="text-xs uppercase tracking-[0.2em] text-slate-400">Live</span>
      </div>
      <div className="space-y-3">
        {skills.map((skill) => (
          <div key={skill.name}>
            <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
              <span>{skill.name}</span>
              <span>{skill.score}%</span>
            </div>
            <div className="h-2.5 rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-500 via-cyan-400 to-emerald-400"
                style={{ width: `${skill.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
