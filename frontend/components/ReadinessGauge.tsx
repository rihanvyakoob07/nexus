type ReadinessGaugeProps = {
  score: number;
  label: string;
};

export default function ReadinessGauge({ score, label }: ReadinessGaugeProps) {
  const value = Math.max(0, Math.min(100, score));
  const rotation = value * 3.6;

  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-[#DFE4EC] bg-white p-6 shadow-sm">
      <div className="relative flex h-32 w-32 items-center justify-center rounded-full">
        <div className="absolute inset-0 rounded-full" style={{ background: `conic-gradient(#0F5FDC ${rotation}deg, #E8EDF4 0deg)` }} />
        <div className="absolute inset-[10px] rounded-full bg-white" />
        <div className="relative text-center"><div className="text-3xl font-bold text-[#172033]">{value}%</div><div className="mt-1 text-[10px] font-semibold uppercase tracking-widest text-[#64748B]">Readiness</div></div>
      </div>
      <p className="text-sm font-semibold text-[#334155]">{label}</p>
    </div>
  );
}
