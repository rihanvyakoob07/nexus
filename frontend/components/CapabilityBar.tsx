type CapabilityBarProps = {
  label: string;
  value: number;
  subtitle?: string;
  tone?: "emerald" | "sky" | "violet" | "amber";
};

const toneClasses: Record<NonNullable<CapabilityBarProps["tone"]>, string> = {
  emerald: "bg-[#147D64]",
  sky: "bg-[#0F5FDC]",
  violet: "bg-[#6B2FB5]",
  amber: "bg-[#A15C00]",
};

export default function CapabilityBar({ label, value, subtitle, tone = "emerald" }: CapabilityBarProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3 text-sm text-[#475569]"><span>{label}</span><span className="font-semibold text-[#172033]">{value}%</span></div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#E8EDF4]"><div className={`h-full rounded-full ${toneClasses[tone]}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>
      {subtitle ? <p className="text-xs leading-5 text-[#64748B]">{subtitle}</p> : null}
    </div>
  );
}
