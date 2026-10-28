import React from 'react';
import { PatientIntake } from '../types/triage';

interface PatientFormProps {
  intake: PatientIntake;
  onChange: (updated: PatientIntake) => void;
  onSubmit: (e: React.FormEvent) => void;
  onReset: () => void;
  loading: boolean;
}

export const PatientForm: React.FC<PatientFormProps> = ({
  intake,
  onChange,
  onSubmit,
  onReset,
  loading,
}) => {
  const handleChange = (field: keyof PatientIntake, value: any) => {
    onChange({
      ...intake,
      [field]: value,
    });
  };

  const handleNumberChange = (field: keyof PatientIntake, strVal: string) => {
    if (strVal === '') {
      handleChange(field, null);
    } else {
      const num = parseFloat(strVal);
      handleChange(field, isNaN(num) ? null : num);
    }
  };

  return (
    <section className="glass-card rounded-2xl p-5 shadow-xl">
      <h2 className="text-base sm:text-lg font-bold text-white mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        <span>Patient Intake Desk (&le; 60s Nurse Budget)</span>
      </h2>

      <form onSubmit={onSubmit} className="space-y-3.5">
        {/* Row 1: ID, Age, Sex */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Patient Token / ID</label>
            <input
              type="text"
              value={intake.patient_id}
              onChange={(e) => handleChange('patient_id', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-mono"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Age (Years) <span className="text-cyan-400 font-normal">&lt;12 = Pediatric</span>
            </label>
            <input
              type="number"
              min="0"
              max="120"
              value={intake.age}
              onChange={(e) => handleNumberChange('age', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Sex</label>
            <select
              value={intake.sex}
              onChange={(e) => handleChange('sex', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            >
              <option value="M">Male (M)</option>
              <option value="F">Female (F)</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>

        {/* Row 2: Vitals 1 (BP Systolic, BP Diastolic, HR) */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">BP Systolic (mmHg)</label>
            <input
              type="number"
              placeholder="e.g. 120"
              value={intake.bp_systolic ?? ''}
              onChange={(e) => handleNumberChange('bp_systolic', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">BP Diastolic (mmHg)</label>
            <input
              type="number"
              placeholder="e.g. 80"
              value={intake.bp_diastolic ?? ''}
              onChange={(e) => handleNumberChange('bp_diastolic', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Heart Rate (bpm)</label>
            <input
              type="number"
              placeholder="e.g. 75"
              value={intake.heart_rate ?? ''}
              onChange={(e) => handleNumberChange('heart_rate', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
        </div>

        {/* Row 3: Vitals 2 (Resp Rate, Temp with auto-convert hint, SpO2) */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Resp Rate (breaths/m)</label>
            <input
              type="number"
              placeholder="e.g. 16"
              value={intake.respiratory_rate ?? ''}
              onChange={(e) => handleNumberChange('respiratory_rate', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Temp (°C box) <span className="text-cyan-400 font-normal">°F Auto-Detects!</span>
            </label>
            <input
              type="number"
              step="0.1"
              placeholder="e.g. 37.0 or 98.6"
              value={intake.temperature ?? ''}
              onChange={(e) => handleNumberChange('temperature', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              SpO2 (%) <span className="text-amber-400 font-normal">&gt;100 = Error</span>
            </label>
            <input
              type="number"
              placeholder="e.g. 98"
              value={intake.spo2 ?? ''}
              onChange={(e) => handleNumberChange('spo2', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
        </div>

        {/* Medical History */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Known Conditions</label>
            <input
              type="text"
              placeholder="e.g. Hypertension, Diabetes, Asthma"
              value={intake.known_conditions}
              onChange={(e) => handleChange('known_conditions', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Current Medications</label>
            <input
              type="text"
              placeholder="e.g. Amlodipine 5mg, Metformin"
              value={intake.current_medications}
              onChange={(e) => handleChange('current_medications', e.target.value)}
              className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
            />
          </div>
        </div>

        {/* Free-text Chief Complaint */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1">
            Chief Complaint (Free Text)
            <span className="text-cyan-400 font-normal ml-1.5">
              English / Transliterated Telugu / Transliterated Hindi / Mixed
            </span>
          </label>
          <textarea
            rows={3}
            placeholder="Type how patient speaks (e.g., 'gunde noppi ga undi', 'chhati me dard hai', 'severe chest pain', 'fever for 2 days')..."
            value={intake.chief_complaint}
            onChange={(e) => handleChange('chief_complaint', e.target.value)}
            className="w-full bg-[#0e1628] border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all resize-y"
          ></textarea>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-60 text-white font-bold py-2.5 px-4 rounded-xl shadow-lg shadow-blue-600/30 transition-all hover:-translate-y-0.5 flex items-center justify-center gap-2 text-sm"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                Evaluating Triaging Model...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                RUN SMART TRIAGE ASSESSMENT
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-2.5 rounded-xl border border-slate-700/80 hover:bg-slate-800 text-slate-400 hover:text-white text-sm font-semibold transition-colors"
          >
            Reset
          </button>
        </div>
      </form>
    </section>
  );
};
