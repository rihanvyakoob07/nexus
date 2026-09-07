type ReadinessGaugeProps = {
  score: number;
  label: string;
};

export default function ReadinessGauge({ score, label }: ReadinessGaugeProps) {
  const value = Math.max(0, Math.min(100, score));
  const rotation = value * 3.6;

  return (
    <div className="flex flex-col items-center gap-3 rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <div className="relative flex h-28 w-28 items-center justify-center rounded-full bg-slate-950">
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `conic-gradient(#22c55e ${rotation}deg, rgba(148, 163, 184, 0.18) 0deg)`,
          }}
        />
        <div className="absolute inset-[12px] rounded-full bg-slate-950" />
        <div className="relative text-center">
          <div className="text-2xl font-semibold text-white">{value}%</div>
        </div>
      </div>
      <p className="text-sm text-slate-300">{label}</p>
    </div>
  );
}
