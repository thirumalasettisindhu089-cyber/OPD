import React from 'react';

interface RedFlagsCardProps {
  redFlags: string[];
}

export const RedFlagsCard: React.FC<RedFlagsCardProps> = ({ redFlags }) => {
  if (!redFlags || redFlags.length === 0) return null;

  return (
    <div className="mt-3">
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse"></span>
        <span>Detected Clinical Red-Flag Symptoms:</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {redFlags.map((rf, idx) => (
          <span
            key={idx}
            className="px-2.5 py-1 rounded-md bg-red-500/20 border border-red-500/40 text-red-200 text-xs font-bold flex items-center gap-1 shadow-sm"
          >
            <span>⚠️</span>
            <span>{rf}</span>
          </span>
        ))}
      </div>
    </div>
  );
};
