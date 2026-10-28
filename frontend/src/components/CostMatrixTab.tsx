import React from 'react';

export const CostMatrixTab: React.FC = () => {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-bold text-white mb-1">
          Asymmetric Clinical Penalty Matrix: C(True Level, Predicted Level)
        </h3>
        <p className="text-xs text-slate-400">
          In clinical medicine, error consequences are fundamentally asymmetric. Under-triaging a true emergency is penalized up to 150 points (~50x more than over-triaging a mild case).
        </p>
      </div>

      <div className="glass-card rounded-xl overflow-hidden border border-slate-700/80">
        <div className="overflow-x-auto">
          <table className="w-full text-center text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/80 border-b border-slate-700/80 text-slate-400 uppercase text-[11px] font-bold">
                <th className="py-2.5 px-3 text-left">True Urgency \ Predicted</th>
                <th className="py-2.5 px-3">Pred Level 1</th>
                <th className="py-2.5 px-3">Pred Level 2</th>
                <th className="py-2.5 px-3">Pred Level 3</th>
                <th className="py-2.5 px-3">Pred Level 4</th>
                <th className="py-2.5 px-3">Pred Level 5</th>
                <th className="py-2.5 px-3 text-purple-400 font-bold">Abstain Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              <tr className="bg-red-500/10 hover:bg-red-500/15">
                <td className="py-2.5 px-3 text-left font-bold text-red-400">True Level 1 (Resuscitation)</td>
                <td className="py-2.5 px-3 font-bold text-white">0</td>
                <td className="py-2.5 px-3 text-red-300">10</td>
                <td className="py-2.5 px-3 text-red-400 font-bold">35</td>
                <td className="py-2.5 px-3 text-red-500 font-bold">80</td>
                <td className="py-2.5 px-3 bg-red-600/30 text-red-200 font-black">150 (Catastrophic)</td>
                <td className="py-2.5 px-3 text-purple-400 font-bold bg-purple-500/10">5.0 (Safe)</td>
              </tr>
              <tr className="bg-orange-500/10 hover:bg-orange-500/15">
                <td className="py-2.5 px-3 text-left font-bold text-orange-400">True Level 2 (Emergent)</td>
                <td className="py-2.5 px-3 text-slate-400">2</td>
                <td className="py-2.5 px-3 font-bold text-white">0</td>
                <td className="py-2.5 px-3 text-orange-300">15</td>
                <td className="py-2.5 px-3 text-orange-400 font-bold">45</td>
                <td className="py-2.5 px-3 text-orange-500 font-bold">95</td>
                <td className="py-2.5 px-3 text-purple-400 font-bold bg-purple-500/10">4.0</td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 text-left font-bold text-yellow-400">True Level 3 (Urgent)</td>
                <td className="py-2.5 px-3 text-slate-400">5</td>
                <td className="py-2.5 px-3 text-slate-400">2</td>
                <td className="py-2.5 px-3 font-bold text-white">0</td>
                <td className="py-2.5 px-3 text-slate-300">10</td>
                <td className="py-2.5 px-3 text-slate-300">30</td>
                <td className="py-2.5 px-3 text-purple-400 bg-purple-500/10">3.0</td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 text-left font-bold text-emerald-400">True Level 4 (Less Urgent)</td>
                <td className="py-2.5 px-3 text-slate-400">8</td>
                <td className="py-2.5 px-3 text-slate-400">3</td>
                <td className="py-2.5 px-3 text-slate-400">1</td>
                <td className="py-2.5 px-3 font-bold text-white">0</td>
                <td className="py-2.5 px-3 text-slate-300">5</td>
                <td className="py-2.5 px-3 text-purple-400 bg-purple-500/10">2.0</td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="py-2.5 px-3 text-left font-bold text-blue-400">True Level 5 (Non-Urgent)</td>
                <td className="py-2.5 px-3 text-slate-400">10</td>
                <td className="py-2.5 px-3 text-slate-400">5</td>
                <td className="py-2.5 px-3 text-slate-400">2</td>
                <td className="py-2.5 px-3 text-slate-400">1</td>
                <td className="py-2.5 px-3 font-bold text-white">0</td>
                <td className="py-2.5 px-3 text-purple-400 bg-purple-500/10">1.0</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
