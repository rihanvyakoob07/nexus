type CapabilityBarProps = {
  label: string;
  value: number;
  subtitle?: string;
  tone?: "emerald" | "sky" | "violet" | "amber";
};

const toneClasses: Record<NonNullable<CapabilityBarProps["tone"]>, string> = {
  emerald: "bg-emerald-500",
  sky: "bg-sky-500",
  violet: "bg-violet-500",
  amber: "bg-amber-500",
};

export default function CapabilityBar({
  label,
  value,
  subtitle,
  tone = "emerald",
}: CapabilityBarProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3 text-sm text-slate-300">
        <span>{label}</span>
        <span className="font-medium text-slate-100">{value}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${toneClasses[tone]}`}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
      {subtitle ? <p className="text-xs text-slate-400">{subtitle}</p> : null}
    </div>
  );
}
