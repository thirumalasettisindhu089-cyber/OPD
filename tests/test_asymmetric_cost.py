"""
tests/test_asymmetric_cost.py - Unit tests for Asymmetric Decision Theory & Abstention
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import unittest
import numpy as np
from backend.config import ASYMMETRIC_COST_MATRIX, ABSTENTION_COSTS
from backend.model import SmartTriagePipeline


class TestAsymmetricCost(unittest.TestCase):

    def setUp(self):
        self.pipeline = SmartTriagePipeline()

    def test_borderline_emergency_shifts_to_urgency(self):
        """
        Tests the core hackathon insight:
        Under standard argmax:
          P(Level 2) = 0.35, P(Level 3) = 0.65 -> Argmax predicts Level 3!
        Under asymmetric cost minimization:
          Under-triaging Level 2 to Level 3 has cost 15.
          Over-triaging Level 3 to Level 2 has cost 2.
          Cost-minimizing decision must select Level 2 to prevent fatal under-triage!
        """
        probs = np.array([0.0, 0.35, 0.65, 0.0, 0.0])

        argmax_level = int(np.argmax(probs)) + 1
        self.assertEqual(argmax_level, 3)

        cost_min_level, expected_costs = self.pipeline.predict_cost_minimizing_level(probs)
        # Expected costs:
        # If predict L2: 0.35*Cost(2, 2) + 0.65*Cost(3, 2) = 0.35*0 + 0.65*2 = 1.30
        # If predict L3: 0.35*Cost(2, 3) + 0.65*Cost(3, 3) = 0.35*15 + 0.65*0 = 5.25
        # Expected cost of L2 (1.30) is MUCH lower than L3 (5.25)!
        self.assertEqual(cost_min_level, 2)
        self.assertLess(expected_costs[1], expected_costs[2])

    def test_abstention_on_extreme_uncertainty(self):
        """When probabilities are completely flat/uncertain, system should abstain."""
        flat_probs = np.array([0.20, 0.20, 0.20, 0.20, 0.20])
        dummy_record = {"chief_complaint": "feeling sick", "flags": {}}
        should_abstain, reason = self.pipeline.check_abstention(flat_probs, dummy_record)
        self.assertTrue(should_abstain)
        self.assertIn("High model uncertainty", reason)

    def test_abstention_on_missing_vitals_with_short_text(self):
        """When vitals are missing and text is uninformative, system should abstain."""
        # Confidence is adequate, but vital signals are missing
        confident_probs = np.array([0.10, 0.10, 0.60, 0.10, 0.10])
        record_with_missing_vitals = {
            "chief_complaint": "pain",  # 4 chars, very vague
            "flags": {
                "bp_systolic_missing": True,
                "heart_rate_missing": True,
                "spo2_missing": False,
            }
        }
        should_abstain, reason = self.pipeline.check_abstention(confident_probs, record_with_missing_vitals)
        self.assertTrue(should_abstain)
        self.assertIn("Critical vitals missing", reason)


if __name__ == "__main__":
    unittest.main()
