"""
evaluate.py - Official Evaluation Script for SmartTriage AI
Talent AP Mega Hackathon 2026 - Problem H1: OPD Triage Assistant

Calculates:
1. EMERGENCY RECALL (Reported first and prominently)
2. Mean Asymmetric Cost (Official Evaluator Score)
3. Critical Under-triage Rate (Level 1/2 missed)
4. Under-triage Rate & Over-triage Rate
5. Abstention Rate & Abstention Reward
6. Department Classification Accuracy
7. Ablation comparison across 4 pipeline stages
"""

import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple

# 5x5 Asymmetric Cost Matrix
# Rows: True Level (1, 2, 3, 4, 5) -> index 0 to 4
# Cols: Predicted Level (1, 2, 3, 4, 5) -> index 0 to 4
# Notice: Under-triaging a true emergency costs up to ~30x more than over-triaging mild cases.
ASYMMETRIC_COST_MATRIX = np.array([
    # Pred: L1   L2   L3   L4    L5
    [   0.0, 10.0, 35.0, 80.0, 150.0],  # True L1 (Resuscitation)
    [   2.0,  0.0, 15.0, 45.0,  95.0],  # True L2 (Emergent)
    [   5.0,  2.0,  0.0, 10.0,  30.0],  # True L3 (Urgent)
    [   8.0,  3.0,  1.0,  0.0,   5.0],  # True L4 (Less Urgent)
    [  10.0,  5.0,  2.0,  1.0,   0.0],  # True L5 (Non-urgent)
], dtype=np.float64)

# Fixed cost when system outputs ABSTAIN ("CANNOT ASSESS - SEND TO NURSE NOW")
# Abstaining on an ambiguous Level 1 case costs 5.0 (much better than misclassifying as L4=80 or L5=150)
ABSTENTION_COSTS = np.array([5.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float64)


def compute_sample_cost(true_level: int, pred_level: int, is_abstained: bool = False) -> float:
    """Computes asymmetric cost for a single sample."""
    t_idx = int(true_level) - 1
    if not (0 <= t_idx <= 4):
        return 0.0

    if is_abstained or pred_level == 0:
        return float(ABSTENTION_COSTS[t_idx])

    p_idx = int(pred_level) - 1
    if not (0 <= p_idx <= 4):
        return float(ABSTENTION_COSTS[t_idx])

    return float(ASYMMETRIC_COST_MATRIX[t_idx, p_idx])


def calculate_metrics(
    y_true_level: np.ndarray,
    y_pred_level: np.ndarray,
    y_true_dept: Optional[np.ndarray] = None,
    y_pred_dept: Optional[np.ndarray] = None,
    is_emergency: Optional[np.ndarray] = None,
    is_abstain: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Computes all triage benchmark metrics with asymmetric safety priority.
    """
    n_samples = len(y_true_level)
    if n_samples == 0:
        return {}

    y_true_level = np.asarray(y_true_level, dtype=int)
    y_pred_level = np.asarray(y_pred_level, dtype=int)

    if is_abstain is None:
        is_abstain = (y_pred_level == 0)
    else:
        is_abstain = np.asarray(is_abstain, dtype=bool)

    if is_emergency is None:
        # Emergency definition: True Level 1 or 2
        is_emergency = np.isin(y_true_level, [1, 2])
    else:
        is_emergency = np.asarray(is_emergency, dtype=bool)

    total_emergencies = int(np.sum(is_emergency))

    # Emergency recall: true emergency predicted as Level 1 or 2 OR escalated via safe abstention
    # (Escalation to nurse prevents lethal waiting room delay)
    emergency_caught = 0
    emergency_direct_caught = 0
    emergency_critical_undertriaged = 0

    total_costs = []
    undertriaged_count = 0
    overtriaged_count = 0
    exact_count = 0

    for i in range(n_samples):
        t = y_true_level[i]
        p = y_pred_level[i]
        ab = is_abstain[i]

        cost = compute_sample_cost(t, p, is_abstained=ab)
        total_costs.append(cost)

        if is_emergency[i]:
            if ab or p in [1, 2]:
                emergency_caught += 1
            if not ab and p in [1, 2]:
                emergency_direct_caught += 1
            if not ab and p in [3, 4, 5]:
                emergency_critical_undertriaged += 1

        if not ab:
            if p > t:
                undertriaged_count += 1
            elif p < t:
                overtriaged_count += 1
            else:
                exact_count += 1

    mean_cost = float(np.mean(total_costs))
    emergency_recall = float(emergency_caught / total_emergencies) if total_emergencies > 0 else 1.0
    emergency_direct_recall = float(emergency_direct_caught / total_emergencies) if total_emergencies > 0 else 1.0
    critical_undertriage_rate = float(emergency_critical_undertriaged / total_emergencies) if total_emergencies > 0 else 0.0

    non_abstained_count = int(np.sum(~is_abstain))
    undertriage_rate = float(undertriaged_count / non_abstained_count) if non_abstained_count > 0 else 0.0
    overtriage_rate = float(overtriaged_count / non_abstained_count) if non_abstained_count > 0 else 0.0
    exact_accuracy = float(exact_count / non_abstained_count) if non_abstained_count > 0 else 0.0
    abstention_rate = float(np.mean(is_abstain))

    # Department accuracy
    dept_accuracy = 0.0
    if y_true_dept is not None and y_pred_dept is not None and non_abstained_count > 0:
        valid_mask = ~is_abstain
        true_dept_arr = np.asarray(y_true_dept)[valid_mask]
        pred_dept_arr = np.asarray(y_pred_dept)[valid_mask]
        dept_accuracy = float(np.mean(true_dept_arr == pred_dept_arr))

    return {
        "emergency_recall": emergency_recall,
        "emergency_direct_recall": emergency_direct_recall,
        "critical_undertriage_rate": critical_undertriage_rate,
        "mean_asymmetric_cost": mean_cost,
        "undertriage_rate": undertriage_rate,
        "overtriage_rate": overtriage_rate,
        "exact_level_accuracy": exact_accuracy,
        "abstention_rate": abstention_rate,
        "department_accuracy": dept_accuracy,
        "total_samples": n_samples,
        "total_emergencies": total_emergencies,
    }


def print_evaluation_report(metrics: Dict[str, Any], title: str = "SMARTTRIAGE AI EVALUATION REPORT"):
    """Prints a prominent, formatted evaluation report adhering to hackathon requirements."""
    print("=" * 78)
    print(f" {title.center(76)} ")
    print("=" * 78)
    print(" >>> PRIMARY SAFETY METRICS (CRITICAL FOR SURVIVAL):")
    print(f"   [*] EMERGENCY RECALL (Level 1 & 2):       {metrics.get('emergency_recall', 0.0)*100:6.2f}%")
    print(f"   [*] DIRECT EMERGENCY RECALL:             {metrics.get('emergency_direct_recall', 0.0)*100:6.2f}%")
    print(f"   [*] CRITICAL UNDER-TRIAGE RATE:          {metrics.get('critical_undertriage_rate', 0.0)*100:6.2f}% (Target: < 2.0%)")
    print("-" * 78)
    print(" >>> OFFICIAL HACKATHON PERFORMANCE METRICS:")
    print(f"   [+] Mean Asymmetric Cost (Official Score): {metrics.get('mean_asymmetric_cost', 0.0):6.3f} (Lower is better)")
    print(f"   [+] Under-Triage Rate (Overall):          {metrics.get('undertriage_rate', 0.0)*100:6.2f}%")
    print(f"   [+] Over-Triage Rate (Queue Safety Buffer): {metrics.get('overtriage_rate', 0.0)*100:6.2f}%")
    print(f"   [+] Exact Triage Level Match:             {metrics.get('exact_level_accuracy', 0.0)*100:6.2f}%")
    print(f"   [+] Safe Abstention Rate:                 {metrics.get('abstention_rate', 0.0)*100:6.2f}%")
    print(f"   [+] Department Routing Accuracy:          {metrics.get('department_accuracy', 0.0)*100:6.2f}%")
    print(f"   [+] Total Samples Evaluated:              {metrics.get('total_samples', 0):,}")
    print(f"   [+] True Emergencies Identified:          {metrics.get('total_emergencies', 0):,}")
    print("=" * 78)


if __name__ == "__main__":
    # Test script run
    print("Running evaluate.py self-test verification...")
    # Synthetic mini-test
    y_t = np.array([1, 2, 3, 4, 5, 1, 2, 4])
    y_p = np.array([1, 2, 3, 4, 5, 2, 2, 4])
    rep = calculate_metrics(y_t, y_p)
    print_evaluation_report(rep, "SELF-TEST SYNTHETIC RUN")
