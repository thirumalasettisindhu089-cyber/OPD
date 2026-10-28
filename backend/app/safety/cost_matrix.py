"""
backend/app/safety/cost_matrix.py - Asymmetric Cost Matrix & Decision Theory
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import numpy as np

# 5x5 Asymmetric Cost Matrix
# Rows: True Level (1 to 5, index 0 to 4)
# Columns: Predicted Level (1 to 5, index 0 to 4)
# Under-triaging a true emergency is penalized up to 50x more than over-triaging mild cases.
ASYMMETRIC_COST_MATRIX = np.array([
    # Pred: L1   L2   L3   L4    L5
    [   0.0, 10.0, 35.0, 80.0, 150.0],  # True L1 (Resuscitation)
    [   2.0,  0.0, 15.0, 45.0,  95.0],  # True L2 (Emergent)
    [   5.0,  2.0,  0.0, 10.0,  30.0],  # True L3 (Urgent)
    [   8.0,  3.0,  1.0,  0.0,   5.0],  # True L4 (Less Urgent)
    [  10.0,  5.0,  2.0,  1.0,   0.0],  # True L5 (Non-urgent)
], dtype=np.float64)

# Abstention cost vector per true level (denoting 'CANNOT ASSESS - SEND TO NURSE NOW')
# Abstaining on Level 1 costs 5.0 (much better than under-triaging as L4=80 or L5=150)
ABSTENTION_COSTS = np.array([5.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float64)

CONFIDENCE_THRESHOLD = 0.40


def calculate_expected_costs(probs: np.ndarray) -> np.ndarray:
    """
    Computes expected asymmetric cost for each candidate triage level j:
    E[Cost(j)] = Sum_{i=1..5} P(True = i) * Cost(i, j)
    """
    return np.dot(probs, ASYMMETRIC_COST_MATRIX)


def find_cost_optimal_level(probs: np.ndarray) -> int:
    """Returns 1-indexed optimal triage level that minimizes expected cost."""
    expected_costs = calculate_expected_costs(probs)
    return int(np.argmin(expected_costs)) + 1
