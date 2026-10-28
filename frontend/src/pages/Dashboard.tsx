import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { PresetBar, PRESETS } from '../components/PresetBar';
import { PatientForm } from '../components/PatientForm';
import { TriageCockpit } from '../components/TriageCockpit';
import { MetricsTab } from '../components/MetricsTab';
import { QueueSimulationTab } from '../components/QueueSimulationTab';
import { RulesTableTab } from '../components/RulesTableTab';
import { CostMatrixTab } from '../components/CostMatrixTab';
import { PatientIntake, TriageResult, RuleItem, BenchmarkMetrics } from '../types/triage';
import { triagePatient, fetchRules, fetchMetrics } from '../services/api';

const DEFAULT_INTAKE: PatientIntake = {
  patient_id: 'WALK-8042',
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
  chief_complaint: 'gunde noppi severe ga undi, eeda thammudu cheyyi laakkuntundi',
};

export const Dashboard: React.FC = () => {
  const [intake, setIntake] = useState<PatientIntake>(DEFAULT_INTAKE);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [metrics, setMetrics] = useState<BenchmarkMetrics | null>(null);
  const [activeTab, setActiveTab] = useState<'metrics' | 'simulation' | 'cost_matrix' | 'rules'>('metrics');
  const [isDark, setIsDark] = useState<boolean>(true);

  useEffect(() => {
    // Initial fetch of background clinical data
    fetchRules()
      .then((res) => setRules(res.rules || []))
      .catch((err) => console.error('Error fetching rules:', err));

    fetchMetrics()
      .then((res) => setMetrics(res))
      .catch((err) => console.error('Error fetching metrics:', err));

    // Run initial assessment on default values
    runTriage(DEFAULT_INTAKE);
  }, []);

  const runTriage = async (dataToSubmit: PatientIntake) => {
    try {
      setLoading(true);
      const res = await triagePatient(dataToSubmit);
      setResult(res);
      setLatencyMs(res.latency_ms);
    } catch (err: any) {
      console.error('Triage error:', err);
      alert('Triage assessment failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (presetKey: string) => {
    const selected = PRESETS[presetKey];
    if (selected) {
      setIntake(selected.data);
      runTriage(selected.data);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runTriage(intake);
  };

  const handleReset = () => {
    const fresh: PatientIntake = {
      patient_id: 'WALK-' + Math.floor(1000 + Math.random() * 9000),
      age: 35,
      sex: 'M',
      bp_systolic: null,
      bp_diastolic: null,
      heart_rate: null,
      respiratory_rate: null,
      temperature: null,
      spo2: null,
      known_conditions: 'None',
      current_medications: 'None',
      chief_complaint: '',
    };
    setIntake(fresh);
  };

  const toggleTheme = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <div className="max-w-[1440px] mx-auto p-3 sm:p-5">
      {/* Top Header */}
      <Header latencyMs={latencyMs} isDark={isDark} onToggleTheme={toggleTheme} />

      {/* Demo Presets Toolbar */}
      <PresetBar onSelectPreset={handlePresetSelect} />

      {/* Main 2-Column Clinical Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mb-6">
        <div className="lg:col-span-6 xl:col-span-6">
          <PatientForm
            intake={intake}
            onChange={setIntake}
            onSubmit={handleSubmit}
            onReset={handleReset}
            loading={loading}
          />
        </div>
        <div className="lg:col-span-6 xl:col-span-6">
          <TriageCockpit result={result} />
        </div>
      </div>

      {/* Bottom Tabs: Metrics, Queue Simulation, Cost Matrix, Rules Table */}
      <section className="glass-card rounded-2xl p-4 sm:p-6 shadow-xl">
        <div className="flex items-center gap-2 border-b border-slate-700/80 pb-3 mb-5 overflow-x-auto">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'metrics'
                ? 'bg-slate-800 text-cyan-400 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            📊 Model Benchmark & 4-Stage Ablations
          </button>
          <button
            onClick={() => setActiveTab('simulation')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'simulation'
                ? 'bg-slate-800 text-emerald-400 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            ⏱️ OPD Queue Simulation (FCFS vs Priority)
          </button>
          <button
            onClick={() => setActiveTab('cost_matrix')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'cost_matrix'
                ? 'bg-slate-800 text-yellow-400 border border-yellow-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            ⚖️ Asymmetric Cost Matrix Viewer
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all ${
              activeTab === 'rules'
                ? 'bg-slate-800 text-purple-400 border border-purple-500/40 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            📜 Deterministic Clinical Rules Table ({rules.length})
          </button>
        </div>

        {activeTab === 'metrics' && <MetricsTab metrics={metrics} />}
        {activeTab === 'simulation' && <QueueSimulationTab simulation={metrics?.queue_simulation || null} />}
        {activeTab === 'cost_matrix' && <CostMatrixTab />}
        {activeTab === 'rules' && <RulesTableTab rules={rules} />}
      </section>
    </div>
  );
};
