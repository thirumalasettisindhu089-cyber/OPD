import React from 'react';

interface ClinicalReasoningCardProps {
  clinicalWhy: string[];
}

export const ClinicalReasoningCard: React.FC<ClinicalReasoningCardProps> = ({ clinicalWhy }) => {
  if (!clinicalWhy || clinicalWhy.length === 0) return null;

  return (
    <div className="bg-[#0e1628] border border-slate-700/80 rounded-xl p-3.5 my-3">
      <div className="text-xs font-bold uppercase tracking-wider text-cyan-400 mb-2 flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <span>Clinical Reasoning & Audit Log ("Why"):</span>
      </div>
      <ul className="space-y-1.5 text-xs text-slate-300">
        {clinicalWhy.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="text-cyan-400 font-bold shrink-0 mt-0.5">•</span>
            <span className="leading-relaxed">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
