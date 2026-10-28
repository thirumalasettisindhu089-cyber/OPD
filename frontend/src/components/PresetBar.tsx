import React from 'react';
import { PatientIntake } from '../types/triage';

export const PRESETS: Record<string, { label: string; data: PatientIntake }> = {
  chest_pain: {
    label: '🫀 Chest Pain (Telugu Transliterated)',
    data: {
      patient_id: 'PRESET_CARDIAC_01',
      age: 54,
      sex: 'M',
      bp_systolic: 135,
      bp_diastolic: 88,
      heart_rate: 98,
      respiratory_rate: 20,
      temperature: 37.2,
      spo2: 96,
      known_conditions: 'Hypertension',
      current_medications: 'Amlodipine 5mg',
      chief_complaint: 'gunde noppi severe ga undi, eeda thammudu cheyyi laakkuntundi, chematalu paduthunnayi'
    }
  },
  critical_vitals: {
    label: '⚡ Critical Vitals + Vague Text (Rule Override)',
    data: {
      patient_id: 'PRESET_CRIT_SHOCK_02',
      age: 62,
      sex: 'F',
      bp_systolic: 65,  // Critical hypotension (<70)
      bp_diastolic: 38,
      heart_rate: 148,  // Extreme tachycardia
      respiratory_rate: 34,
      temperature: 36.4,
      spo2: 81,         // Severe hypoxia (<85)
      known_conditions: 'Type 2 Diabetes',
      current_medications: 'Metformin 500mg',
      chief_complaint: 'feeling unwell, very weak, unable to stand'
    }
  },
  impossible_vitals: {
    label: '🌡️ Impossible Vitals (Temp 96°C in box, BP 0)',
    data: {
      patient_id: 'PRESET_NOISY_INPUT_03',
      age: 45,
      sex: 'F',
      bp_systolic: 0,    // Sensor disconnect / 0 BP
      bp_diastolic: 0,
      heart_rate: 82,
      respiratory_rate: 16,
      temperature: 96.0, // 96 C typed in Celsius box (actually Fahrenheit!)
      spo2: 104,         // SpO2 > 100% physically impossible
      known_conditions: 'None',
      current_medications: 'None',
      chief_complaint: 'mild shivering and cold for 2 days, feeling tired'
    }
  },
  telugu_dyspnea: {
    label: '🗣️ Severe Dyspnea (Telugu Transliterated)',
    data: {
      patient_id: 'PRESET_TELUGU_RESP_04',
      age: 48,
      sex: 'M',
      bp_systolic: 128,
      bp_diastolic: 84,
      heart_rate: 122,
      respiratory_rate: 32,
      temperature: 37.4,
      spo2: 88,
      known_conditions: 'Asthma',
      current_medications: 'Salbutamol Inhaler',
      chief_complaint: 'saas aaguthondi, aayasam ekkuva undi, kallu thiruguthunnayi, inhaler pani cheyyatledu'
    }
  },
  mild_fever: {
    label: '🩺 Mild Fever & Cold (Hindi Transliterated)',
    data: {
      patient_id: 'PRESET_HINDI_MILD_05',
      age: 26,
      sex: 'F',
      bp_systolic: 118,
      bp_diastolic: 78,
      heart_rate: 74,
      respiratory_rate: 16,
      temperature: 37.8,
      spo2: 99,
      known_conditions: 'None',
      current_medications: 'None',
      chief_complaint: 'halka bukhar aur sardi hai do din se, bukhar nahi hai zyada'
    }
  },
  pediatric_alert: {
    label: '👶 Pediatric Patient (Adult Rules Bypassed)',
    data: {
      patient_id: 'PRESET_PEDIATRIC_06',
      age: 4,            // Age < 12 -> Pediatric bypass
      sex: 'M',
      bp_systolic: 85,   // Normal for child, would trigger adult hypotension rule if not bypassed
      bp_diastolic: 54,
      heart_rate: 115,   // Normal pediatric HR
      respiratory_rate: 24,
      temperature: 38.3,
      spo2: 98,
      known_conditions: 'None',
      current_medications: 'None',
      chief_complaint: 'child has mild ear ache and crying since yesterday, eating food normally'
    }
  },
  negation_case: {
    label: '🛡️ Negation Safety ("Denies Chest Pain")',
    data: {
      patient_id: 'PRESET_NEGATION_07',
      age: 38,
      sex: 'M',
      bp_systolic: 122,
      bp_diastolic: 80,
      heart_rate: 76,
      respiratory_rate: 16,
      temperature: 36.8,
      spo2: 99,
      known_conditions: 'None',
      current_medications: 'None',
      chief_complaint: 'twisted ankle while jogging, swollen knee, denies chest pain, no shortness of breath, chhati dard nahi hai'
    }
  }
};

interface PresetBarProps {
  onSelectPreset: (presetKey: string) => void;
}

export const PresetBar: React.FC<PresetBarProps> = ({ onSelectPreset }) => {
  return (
    <section className="glass-card rounded-2xl p-4 mb-5 shadow-lg">
      <div className="flex items-center gap-2 mb-2.5 text-xs font-bold uppercase tracking-wider text-slate-400">
        <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        <span>One-Click Clinical Demo Presets (Jury Testing):</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {Object.entries(PRESETS).map(([key, item]) => (
          <button
            key={key}
            onClick={() => onSelectPreset(key)}
            className="px-3 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/60 text-slate-200 text-xs font-semibold transition-all hover:-translate-y-0.5 shadow-sm active:translate-y-0"
          >
            {item.label}
          </button>
        ))}
      </div>
    </section>
  );
};
