import React from 'react';

interface ProbabilityBarsProps {
  probabilities: Record<string, number>;
  expectedCosts: Record<string, number>;
  selectedLevel: number;
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#ef4444',
  2: '#f97316',
  3: '#eab308',
  4: '#10b981',
  5: '#3b82f6',
};

export const ProbabilityBars: React.FC<ProbabilityBarsProps> = ({
  probabilities,
  expectedCosts,
  selectedLevel,
}) => {
  return (
    <div className="bg-[#0e1628] border border-slate-700/80 rounded-xl p-3.5 mt-3">
      <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
        Calibrated Posterior Probabilities & Expected Asymmetric Cost:
      </div>
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((lvl) => {
          const key = `Level ${lvl}`;
          const prob = probabilities[key] ?? 0.0;
          const cost = expectedCosts[key] !== undefined ? expectedCosts[key] : null;
          const pct = Math.round(prob * 100);
          const color = LEVEL_COLORS[lvl];
          const isSelected = selectedLevel === lvl;

          return (
            <div key={lvl} className="flex items-center gap-3 text-xs">
              <span className="w-14 font-semibold" style={{ color }}>
                {key}
              </span>
              <div className="flex-1 h-2.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: color,
                  }}
                ></div>
              </div>
              <span className="w-12 text-right font-mono font-bold text-white">{pct}%</span>
              <span className="w-24 text-right text-[11px] font-mono">
                {cost !== null ? (
                  <span className={isSelected ? 'font-bold' : 'text-slate-400'} style={{ color: isSelected ? color : undefined }}>
                    E[Cost]: {cost.toFixed(1)} {isSelected ? '(Min)' : ''}
                  </span>
                ) : (
                  '--'
                )}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
