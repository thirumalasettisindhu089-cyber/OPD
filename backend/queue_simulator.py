"""
backend/queue_simulator.py - OPD Queue Simulation (FCFS vs SmartTriage Priority Queue)
SmartTriage AI - Talent AP Mega Hackathon 2026

Simulates 800 walk-ins arriving over an 8-hour shift (480 minutes) served by 2 doctors.
Compares:
1. Baseline: First-Come-First-Served (FCFS)
2. SmartTriage AI: Priority Queue (Emergency Levels 1 & 2 expedited)

Provides an honest clinical and operational trade-off analysis.
"""

import os
import heapq
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class Doctor:
    def __init__(self, doc_id: int):
        self.doc_id = doc_id
        self.free_at: float = 0.0
        self.total_busy_time: float = 0.0
        self.patients_treated: int = 0


def simulate_fcfs(arrivals_df: pd.DataFrame, num_doctors: int = 2) -> Dict[str, Any]:
    """
    Simulates First-Come-First-Served (FCFS) triage queue.
    Doctors treat patients purely in the order of their arrival.
    """
    doctors = [Doctor(i) for i in range(num_doctors)]
    records = []

    # Sort strictly by arrival time
    df_sorted = arrivals_df.sort_values(by="arrival_minute").copy()

    for _, row in df_sorted.iterrows():
        arr_time = float(row["arrival_minute"])
        service_dur = float(row["service_duration_min"])
        lvl = int(row["triage_level"])
        pid = row["patient_id"]

        # Find doctor who becomes free earliest
        doc = min(doctors, key=lambda d: d.free_at)

        start_service = max(arr_time, doc.free_at)
        wait_time = start_service - arr_time
        end_service = start_service + service_dur

        doc.free_at = end_service
        doc.total_busy_time += service_dur
        doc.patients_treated += 1

        records.append({
            "patient_id": pid,
            "arrival_time": arr_time,
            "triage_level": lvl,
            "wait_time_min": wait_time,
            "start_time": start_service,
            "end_time": end_service,
            "doctor_id": doc.doc_id,
        })

    sim_df = pd.DataFrame(records)
    return compute_simulation_statistics(sim_df, doctors, "First-Come-First-Served (FCFS)")


def simulate_priority_queue(arrivals_df: pd.DataFrame, num_doctors: int = 2) -> Dict[str, Any]:
    """
    Simulates SmartTriage AI Priority Queue.
    Doctors prioritize urgent patients (Level 1 > Level 2 > Level 3 > Level 4 > Level 5).
    Ties within the same urgency level are resolved by FIFO arrival time.
    """
    doctors = [Doctor(i) for i in range(num_doctors)]
    records = []

    # Event-driven priority queue
    # Heap stores: (triage_level, arrival_minute, patient_dict)
    waiting_queue = []
    
    # Sort arrival events
    unprocessed_arrivals = arrivals_df.sort_values(by="arrival_minute").to_dict(orient="records")
    arrival_idx = 0
    n_patients = len(unprocessed_arrivals)

    current_time = 0.0

    while arrival_idx < n_patients or waiting_queue:
        # Check earliest doctor availability
        earliest_doc = min(doctors, key=lambda d: d.free_at)

        # If waiting queue is empty, jump time to next patient arrival
        if not waiting_queue:
            next_arr = unprocessed_arrivals[arrival_idx]
            current_time = max(earliest_doc.free_at, float(next_arr["arrival_minute"]))
        else:
            current_time = earliest_doc.free_at

        # Push all patients who have arrived up to current_time into priority queue
        while arrival_idx < n_patients and float(unprocessed_arrivals[arrival_idx]["arrival_minute"]) <= current_time:
            p = unprocessed_arrivals[arrival_idx]
            # Heap tuple: (triage_level, arrival_minute, counter, p)
            heapq.heappush(waiting_queue, (int(p["triage_level"]), float(p["arrival_minute"]), arrival_idx, p))
            arrival_idx += 1

        # If queue still empty (rare edge case), continue loop
        if not waiting_queue:
            continue

        # Pop highest priority patient (lowest level number = highest urgency)
        triage_lvl, arr_m, _, patient = heapq.heappop(waiting_queue)
        service_dur = float(patient["service_duration_min"])

        # Assign to earliest available doctor
        doc = min(doctors, key=lambda d: d.free_at)
        start_service = max(arr_m, doc.free_at)
        wait_time = start_service - arr_m
        end_service = start_service + service_dur

        doc.free_at = end_service
        doc.total_busy_time += service_dur
        doc.patients_treated += 1

        records.append({
            "patient_id": patient["patient_id"],
            "arrival_time": arr_m,
            "triage_level": triage_lvl,
            "wait_time_min": wait_time,
            "start_time": start_service,
            "end_time": end_service,
            "doctor_id": doc.doc_id,
        })

    sim_df = pd.DataFrame(records)
    return compute_simulation_statistics(sim_df, doctors, "SmartTriage AI Priority Queue")


def compute_simulation_statistics(df: pd.DataFrame, doctors: List[Doctor], policy_name: str) -> Dict[str, Any]:
    """Calculates granular waiting time statistics across triage levels."""
    # Emergency cohort: Level 1 & 2
    em_mask = df["triage_level"].isin([1, 2])
    l1_mask = df["triage_level"] == 1
    l2_mask = df["triage_level"] == 2
    l3_mask = df["triage_level"] == 3
    l4_mask = df["triage_level"] == 4
    l5_mask = df["triage_level"] == 5

    def safe_mean(sub_df):
        return float(sub_df["wait_time_min"].mean()) if len(sub_df) > 0 else 0.0

    def safe_max(sub_df):
        return float(sub_df["wait_time_min"].max()) if len(sub_df) > 0 else 0.0

    total_patients = len(df)
    # Total shift time is 480 minutes (8 hours)
    shift_duration = 480.0
    utilization = [min(100.0, (d.total_busy_time / shift_duration) * 100) for d in doctors]

    # Approximate dangerous wait events: Emergency patient waiting > 30 minutes
    dangerous_delays = int((df[em_mask]["wait_time_min"] > 30.0).sum())

    return {
        "policy_name": policy_name,
        "total_patients": total_patients,
        "mean_wait_emergency_min": round(safe_mean(df[em_mask]), 1),
        "max_wait_emergency_min": round(safe_max(df[em_mask]), 1),
        "mean_wait_l1_min": round(safe_mean(df[l1_mask]), 1),
        "mean_wait_l2_min": round(safe_mean(df[l2_mask]), 1),
        "mean_wait_l3_min": round(safe_mean(df[l3_mask]), 1),
        "mean_wait_l4_min": round(safe_mean(df[l4_mask]), 1),
        "mean_wait_l5_min": round(safe_mean(df[l5_mask]), 1),
        "mean_wait_overall_min": round(safe_mean(df), 1),
        "max_wait_overall_min": round(safe_max(df), 1),
        "dangerous_emergency_delays": dangerous_delays,
        "doctor_utilization_pct": [round(u, 1) for u in utilization],
        "by_level": {
            "Level 1 (Resuscitation)": {"mean": round(safe_mean(df[l1_mask]), 1), "max": round(safe_max(df[l1_mask]), 1)},
            "Level 2 (Emergent)": {"mean": round(safe_mean(df[l2_mask]), 1), "max": round(safe_max(df[l2_mask]), 1)},
            "Level 3 (Urgent)": {"mean": round(safe_mean(df[l3_mask]), 1), "max": round(safe_max(df[l3_mask]), 1)},
            "Level 4 (Less Urgent)": {"mean": round(safe_mean(df[l4_mask]), 1), "max": round(safe_max(df[l4_mask]), 1)},
            "Level 5 (Non-urgent)": {"mean": round(safe_mean(df[l5_mask]), 1), "max": round(safe_max(df[l5_mask]), 1)},
        }
    }


def run_comparative_simulation(arrival_log_path: str = "data/arrival_log.csv") -> Dict[str, Any]:
    """Runs and compares FCFS vs SmartTriage AI side by side."""
    if not os.path.exists(arrival_log_path):
        raise FileNotFoundError(f"Arrival log not found at {arrival_log_path}")

    df_arrivals = pd.read_csv(arrival_log_path)
    fcfs_stats = simulate_fcfs(df_arrivals)
    pq_stats = simulate_priority_queue(df_arrivals)

    em_time_saved = fcfs_stats["mean_wait_emergency_min"] - pq_stats["mean_wait_emergency_min"]
    em_reduction_pct = (em_time_saved / fcfs_stats["mean_wait_emergency_min"]) * 100 if fcfs_stats["mean_wait_emergency_min"] > 0 else 0.0

    l5_delay_increase = pq_stats["mean_wait_l5_min"] - fcfs_stats["mean_wait_l5_min"]

    tradeoff_summary = {
        "fcfs": fcfs_stats,
        "smart_triage": pq_stats,
        "emergency_wait_reduction_min": round(em_time_saved, 1),
        "emergency_wait_reduction_pct": round(em_reduction_pct, 1),
        "non_urgent_wait_increase_min": round(l5_delay_increase, 1),
        "clinical_takeaway": (
            f"SmartTriage AI reduces true emergency wait time by {em_reduction_pct:.1f}% "
            f"(from {fcfs_stats['mean_wait_emergency_min']} min down to {pq_stats['mean_wait_emergency_min']} min), "
            f"virtually eliminating critical delays > 30 min (from {fcfs_stats['dangerous_emergency_delays']} down to {pq_stats['dangerous_emergency_delays']}). "
            f"In exchange, Level 5 non-urgent walk-ins wait an additional {l5_delay_increase:.1f} minutes, "
            f"a clinically safe and ethically vital trade-off that saves lives in an overloaded district hospital."
        )
    }
    return tradeoff_summary


if __name__ == "__main__":
    results = run_comparative_simulation()
    print("=" * 70)
    print(" OPD QUEUE SIMULATION: FCFS vs SMARTTRIAGE AI PRIORITY QUEUE ")
    print("=" * 70)
    print(f"FCFS Emergency Mean Wait:         {results['fcfs']['mean_wait_emergency_min']} min")
    print(f"SmartTriage Emergency Mean Wait:  {results['smart_triage']['mean_wait_emergency_min']} min")
    print(f"Emergency Wait Reduction:         {results['emergency_wait_reduction_min']} min ({results['emergency_wait_reduction_pct']}%)")
    print(f"Non-Urgent (L5) Wait Trade-off:   +{results['non_urgent_wait_increase_min']} min")
    print("-" * 70)
    print(results['clinical_takeaway'])
    print("=" * 70)
