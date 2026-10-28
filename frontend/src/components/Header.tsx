import React from 'react';

interface HeaderProps {
  latencyMs: number | null;
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({ latencyMs, isDark, onToggleTheme }) => {
  return (
    <header className="glass-card rounded-2xl p-4 sm:p-5 mb-5 shadow-xl flex flex-wrap items-center justify-between gap-4 transition-all">
      <div className="flex items-center gap-3.5">
        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg shadow-red-500/30">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white dark:text-white dark:drop-shadow-sm font-sans">
              SmartTriage AI
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-full">
              H1 Decision Support
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium">
            Emergency OPD Stratification & Priority Decision Engine | Talent AP Hackathon 2026
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
        {/* Clinical Disclaimer Notice */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-xs font-bold tracking-wide">
          <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>DECISION SUPPORT ONLY — CLINICAL NURSE DECIDES</span>
        </div>

        {/* Latency Indicator */}
        <div className="px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>{latencyMs !== null ? `⚡ Latency: ${latencyMs} ms` : '⚡ Ready'}</span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-semibold transition-colors flex items-center gap-1.5"
          title="Toggle Dark/Light Mode"
        >
          <span>{isDark ? '☀️ Light' : '🌙 Dark'}</span>
        </button>
      </div>
    </header>
  );
};
