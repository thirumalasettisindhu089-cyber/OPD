"""
backend/tests/test_rules.py - Unit tests for Deterministic Safety Rule Engine
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import unittest
from backend.app.ml.data_cleaner import clean_patient_record
from backend.app.safety.rules import evaluate_rules


class TestRuleEngine(unittest.TestCase):

    def test_adult_critical_vitals_resuscitation_hypotension(self):
        raw = {
            "age": 55,
            "chief_complaint": "feeling weak and dizzy",
            "bp_systolic": 65,
            "bp_diastolic": 40,
            "heart_rate": 110,
            "respiratory_rate": 20,
            "temperature": 36.8,
            "spo2": 96,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["rule_triggered"])
        self.assertEqual(rule_res["rule_level"], 1)

    def test_adult_critical_vitals_severe_hypoxia(self):
        raw = {
            "age": 60,
            "chief_complaint": "cough for 3 days",
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "heart_rate": 95,
            "respiratory_rate": 24,
            "temperature": 37.5,
            "spo2": 82,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["rule_triggered"])
        self.assertEqual(rule_res["rule_level"], 1)

    def test_red_flag_telugu_chest_pain(self):
        raw = {
            "age": 50,
            "chief_complaint": "gunde noppi chaala ekkuvaga undi, cheyyi laakkuntundi",
            "bp_systolic": 130,
            "bp_diastolic": 85,
            "heart_rate": 88,
            "respiratory_rate": 18,
            "temperature": 37.0,
            "spo2": 98,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["rule_triggered"])
        self.assertEqual(rule_res["rule_level"], 2)

    def test_negation_english_no_chest_pain(self):
        raw = {
            "age": 32,
            "chief_complaint": "patient has sprained ankle, denies chest pain, without shortness of breath",
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "heart_rate": 72,
            "respiratory_rate": 16,
            "temperature": 36.8,
            "spo2": 99,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertFalse(rule_res["rule_triggered"])

    def test_pediatric_vital_bypass(self):
        raw = {
            "age": 4,
            "chief_complaint": "mild ear ache",
            "bp_systolic": 85,
            "bp_diastolic": 55,
            "heart_rate": 110,
            "respiratory_rate": 24,
            "temperature": 37.0,
            "spo2": 99,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["pediatric_bypassed"])
        self.assertIsNone(rule_res["rule_level"])


if __name__ == "__main__":
    unittest.main()
