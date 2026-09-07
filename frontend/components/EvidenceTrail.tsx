type EvidenceItem = {
  title: string;
  detail: string;
  date: string;
  type: "project" | "cert" | "assessment" | "client";
};

type EvidenceTrailProps = {
  items: EvidenceItem[];
};

const typeBadgeClasses: Record<EvidenceItem["type"], string> = {
  project: "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30",
  cert: "bg-violet-500/15 text-violet-300 ring-1 ring-violet-500/30",
  assessment: "bg-sky-500/15 text-sky-300 ring-1 ring-sky-500/30",
  client: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30",
};

export default function EvidenceTrail({ items }: EvidenceTrailProps) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={`${item.title}-${item.date}`} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2 py-1 text-[10px] uppercase tracking-[0.18em] ${typeBadgeClasses[item.type]}`}>
                {item.type}
              </span>
              <p className="font-medium text-slate-100">{item.title}</p>
            </div>
            <span className="text-xs text-slate-400">{item.date}</span>
          </div>
          <p className="text-sm text-slate-300">{item.detail}</p>
        </div>
      ))}
    </div>
  );
}
