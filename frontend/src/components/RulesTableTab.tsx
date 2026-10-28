import React, { useState } from 'react';
import { RuleItem } from '../types/triage';

interface RulesTableTabProps {
  rules: RuleItem[];
}

export const RulesTableTab: React.FC<RulesTableTabProps> = ({ rules }) => {
  const [filterText, setFilterText] = useState('');

  const filtered = rules.filter(
    (r) =>
      r.id.toLowerCase().includes(filterText.toLowerCase()) ||
      r.category.toLowerCase().includes(filterText.toLowerCase()) ||
      r.condition.toLowerCase().includes(filterText.toLowerCase()) ||
      r.urgency_level.toLowerCase().includes(filterText.toLowerCase()) ||
      r.rationale.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white">
            Transparent Deterministic Rule Engine ({rules.length} Audited Clinical Rules)
          </h3>
          <p className="text-xs text-slate-400">
            Rules execute prior to ML models and strictly override predictions when pointing to higher urgency.
          </p>
        </div>
        <input
          type="text"
          placeholder="🔍 Filter rules (e.g. cardiac, bp, pediatric)..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 w-full sm:w-64"
        />
      </div>

      <div className="glass-card rounded-xl overflow-hidden border border-slate-700/80">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/80 border-b border-slate-700/80 text-slate-400 uppercase text-[11px] font-bold">
                <th className="py-2.5 px-3">Rule ID</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Clinical Trigger Condition</th>
                <th className="py-2.5 px-3">Assigned Urgency</th>
                <th className="py-2.5 px-3">Action & Routing</th>
                <th className="py-2.5 px-3">Medical Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {filtered.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40">
                  <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">{r.id}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-300">{r.category}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-200 bg-slate-900/30">{r.condition}</td>
                  <td className="py-2.5 px-3 font-bold text-white">{r.urgency_level}</td>
                  <td className="py-2.5 px-3 text-slate-300">{r.action}</td>
                  <td className="py-2.5 px-3 text-slate-400">{r.rationale}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    No clinical rules match '{filterText}'.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
