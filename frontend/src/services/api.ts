import axios from 'axios';
import { PatientIntake, TriageResult, RulesResponse, BenchmarkMetrics, QueueSimulationResult } from '../types/triage';

const API_BASE = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const triagePatient = async (intake: PatientIntake): Promise<TriageResult> => {
  const response = await apiClient.post<TriageResult>('/triage', intake);
  return response.data;
};

export const fetchRules = async (): Promise<RulesResponse> => {
  const response = await apiClient.get<RulesResponse>('/rules');
  return response.data;
};

export const fetchMetrics = async (): Promise<BenchmarkMetrics> => {
  const response = await apiClient.get<BenchmarkMetrics>('/metrics');
  return response.data;
};

export const runSimulation = async (): Promise<QueueSimulationResult> => {
  const response = await apiClient.post<QueueSimulationResult>('/simulate');
  return response.data;
};
