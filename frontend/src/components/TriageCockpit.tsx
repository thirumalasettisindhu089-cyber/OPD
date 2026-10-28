import React from 'react';
import { TriageResult } from '../types/triage';
import { RedFlagsCard } from './RedFlagsCard';
import { ClinicalReasoningCard } from './ClinicalReasoningCard';
import { ProbabilityBars } from './ProbabilityBars';

interface TriageCockpitProps {
  result: TriageResult | null;
}

const WAITING_TIME_MAP: Record<number, string> = {
  1: '⏱️ Maximum Safe Waiting Time: IMMEDIATE RESUSCITATION (0 minutes)',
  2: '⏱️ Maximum Safe Waiting Time: < 15 minutes (Direct Physician Attention)',
  3: '⏱️ Maximum Safe Waiting Time: < 60 minutes (Urgent Multi-Resource Workup)',
  4: '⏱️ Maximum Safe Waiting Time: < 120 minutes (Less Urgent / Single Resource)',
  5: '⏱️ Maximum Safe Waiting Time: < 240 minutes (Non-Urgent / Routine Refill)',
  0: '⚠️ ACTION REQUIRED: Cannot Safely Assess Algorithmic Urgency — Send to Nurse Now',
};

export const TriageCockpit: React.FC<TriageCockpitProps> = ({ result }) => {
  if (!result) {
    return (
      <section className="glass-card rounded-2xl p-6 shadow-xl flex flex-col items-center justify-center min-h-[420px] text-center text-slate-400">
        <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-3">
          <svg className="w-8 h-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-base font-bold text-slate-300">Awaiting Patient Assessment</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Select a quick preset above or fill in the patient intake form and click "Run Smart Triage Assessment".
        </p>
      </section>
    );
  }

  const {
    triage_level,
    triage_level_name,
    color_code,
    recommended_department,
    rule_override,
    rule_applied,
    red_flags,
    clinical_why,
    probabilities,
    expected_costs,
    data_warnings,
  } = result;

  const waitGuidance = WAITING_TIME_MAP[triage_level] || `Maximum Safe Waiting Time: Level ${triage_level}`;

  return (
    <section className="glass-card rounded-2xl p-5 shadow-xl transition-all">
      <h2 className="text-base sm:text-lg font-bold text-white mb-3.5 flex items-center gap-2">
        <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <span>Decision Support Cockpit</span>
      </h2>

      {/* Main Color-Coded Triage Banner */}
      <div
        className="rounded-xl p-4 sm:p-5 border-2 transition-all relative overflow-hidden bg-slate-900/90"
        style={{
          borderColor: color_code,
          boxShadow: `0 0 25px ${color_code}33`,
        }}
      >
        <div className="flex flex-wrap items-start justify-between gap-2.5 mb-2">
          <div className="text-xl sm:text-2xl font-black tracking-tight" style={{ color: color_code }}>
            {triage_level_name}
          </div>
          {rule_override && (
            <span className="px-2.5 py-1 rounded-md text-[11px] font-extrabold tracking-wider uppercase bg-red-500/20 text-red-300 border border-red-500/50 animate-pulse">
              RULE OVERRIDE: {rule_applied || 'CRITICAL SAFETY'}
            </span>
          )}
        </div>

        <div className="text-sm text-slate-300 mb-1.5">
          Recommended Routing:{' '}
          <span className="font-bold text-white text-base underline decoration-cyan-500/60 decoration-2 underline-offset-4">
            {recommended_department}
          </span>
        </div>

        <div className="text-xs font-bold tracking-wide" style={{ color: color_code }}>
          {waitGuidance}
        </div>
      </div>

      {/* Red Flags Chips */}
      <RedFlagsCard redFlags={red_flags} />

      {/* Data Sanitization Warnings (0 BP, Fahrenheit auto-converted, etc.) */}
      {data_warnings && data_warnings.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 my-2.5 text-xs text-amber-200">
          <div className="font-bold flex items-center gap-1.5 mb-1 text-amber-300">
            <span>🛡️</span>
            <span>Data Sanitization Alerts:</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5">
            {data_warnings.map((warn, i) => (
              <li key={i}>{warn}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Clinical Reasoning / Why list */}
      <ClinicalReasoningCard clinicalWhy={clinical_why} />

      {/* Probability Bars & Expected Costs */}
      <ProbabilityBars
        probabilities={probabilities}
        expectedCosts={expected_costs}
        selectedLevel={triage_level}
      />
    </section>
  );
};
