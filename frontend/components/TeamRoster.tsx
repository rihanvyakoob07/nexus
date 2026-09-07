type TeamMember = {
  name: string;
  role: string;
  fit: number;
  skills: string[];
};

type TeamRosterProps = {
  members: TeamMember[];
};

export default function TeamRoster({ members }: TeamRosterProps) {
  return (
    <div className="space-y-4">
      {members.map((member) => (
        <div key={member.name} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
          <div className="mb-2 flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-white">{member.name}</p>
              <p className="text-sm text-slate-400">{member.role}</p>
            </div>
            <span className="rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-medium text-emerald-300">
              {member.fit}% fit
            </span>
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            {member.skills.map((skill) => (
              <span key={skill} className="rounded-full border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200">
                {skill}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
