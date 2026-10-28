export interface PatientIntake {
  patient_id: string;
  age: number;
  sex: string;
  bp_systolic: number | null;
  bp_diastolic: number | null;
  heart_rate: number | null;
  respiratory_rate: number | null;
  temperature: number | null;
  spo2: number | null;
  known_conditions: string;
  current_medications: string;
  chief_complaint: string;
}

export interface CleanedIntake {
  age: number;
  sex: string;
  is_pediatric: boolean;
  chief_complaint: string;
  bp_systolic: number | null;
  bp_diastolic: number | null;
  heart_rate: number | null;
  respiratory_rate: number | null;
  temperature: number | null;
  spo2: number | null;
}

export interface TriageResult {
  patient_id: string;
  triage_level: number; // 0=Abstain, 1=Resuscitation, 2=Emergent, 3=Urgent, 4=Less Urgent, 5=Non-Urgent
  triage_level_name: string;
  color_code: string;
  is_emergency: boolean;
  recommended_department: string;
  rule_override: boolean;
  rule_applied?: string | null;
  is_abstain: boolean;
  abstain_reason?: string | null;
  red_flags: string[];
  clinical_why: string[];
  nurse_alerts: string[];
  data_warnings: string[];
  probabilities: Record<string, number>;
  expected_costs: Record<string, number>;
  latency_ms: number;
  disclaimer: string;
  cleaned_intake?: CleanedIntake;
}

export interface RuleItem {
  id: string;
  category: string;
  condition: string;
  urgency_level: string;
  action: string;
  rationale: string;
}

export interface RulesResponse {
  total_rules: number;
  rules: RuleItem[];
  disclaimer: string;
}

export interface AblationMetrics {
  emergency_recall: number;
  emergency_direct_recall: number;
  critical_undertriage_rate: number;
  mean_asymmetric_cost: number;
  undertriage_rate: number;
  overtriage_rate: number;
  exact_level_accuracy: number;
  abstention_rate: number;
  department_accuracy: number;
  total_samples: number;
  total_emergencies: number;
}

export interface QueueSimSummary {
  policy_name: string;
  total_patients: number;
  mean_wait_emergency_min: number;
  max_wait_emergency_min: number;
  mean_wait_l1_min: number;
  mean_wait_l2_min: number;
  mean_wait_l3_min: number;
  mean_wait_l4_min: number;
  mean_wait_l5_min: number;
  mean_wait_overall_min: number;
  max_wait_overall_min: number;
  dangerous_emergency_delays: number;
  doctor_utilization_pct: number[];
  by_level: Record<string, { mean: number; max: number }>;
}

export interface QueueSimulationResult {
  emergency_wait_reduction_min: number;
  emergency_wait_reduction_pct: number;
  non_urgent_wait_increase_min: number;
  clinical_takeaway: string;
  fcfs: QueueSimSummary;
  smart_triage: QueueSimSummary;
}

export interface BenchmarkMetrics {
  dataset_name: string;
  synthetic_data_disclaimer: string;
  val_samples: number;
  ablations: {
    plain_argmax: AblationMetrics;
    cost_aware: AblationMetrics;
    cost_aware_plus_rules: AblationMetrics;
    full_pipeline: AblationMetrics;
  };
  queue_simulation: QueueSimulationResult;
}
