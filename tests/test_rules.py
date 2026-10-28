"""
tests/test_rules.py - Unit tests for Deterministic Rule Engine
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import unittest
from backend.data_cleaner import clean_patient_record
from backend.rule_engine import evaluate_rules, is_negated


class TestRuleEngine(unittest.TestCase):

    def test_adult_critical_vitals_resuscitation_hypotension(self):
        # Adult with SBP 65 (< 70) must trigger Level 1 Resuscitation
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
        self.assertEqual(rule_res["rule_id"], "VITAL_L1_PROFOUND_SHOCK")

    def test_adult_critical_vitals_severe_hypoxia(self):
        # Adult with SpO2 82% (< 85%) must trigger Level 1 Resuscitation
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
        self.assertEqual(rule_res["rule_id"], "VITAL_L1_SEVERE_HYPOXIA")

    def test_red_flag_telugu_chest_pain(self):
        # Transliterated Telugu: "gunde noppi"
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
        self.assertIn("CARDIAC: gunde noppi", rule_res["red_flag_chips"])

    def test_red_flag_hindi_chest_pain(self):
        # Transliterated Hindi: "chhati me dard"
        raw = {
            "age": 48,
            "chief_complaint": "chhati me dard ho raha hai subah se",
            "bp_systolic": 135,
            "bp_diastolic": 88,
            "heart_rate": 82,
            "temperature": 36.9,
            "spo2": 99,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["rule_triggered"])
        self.assertEqual(rule_res["rule_level"], 2)
        self.assertIn("CARDIAC: chhati me dard", rule_res["red_flag_chips"])

    def test_negation_english_no_chest_pain(self):
        # "patient has sprained ankle, no chest pain" -> Cardiac red flag MUST NOT trigger!
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
        self.assertEqual(len(rule_res["red_flag_chips"]), 0)

    def test_negation_telugu_gunde_noppi_ledu(self):
        # "kaalu noppi undi kani gunde noppi ledu" -> MUST NOT trigger cardiac red flag!
        raw = {
            "age": 40,
            "chief_complaint": "kaalu noppi undi kani gunde noppi ledu",
            "bp_systolic": 122,
            "bp_diastolic": 80,
            "heart_rate": 74,
            "respiratory_rate": 16,
            "temperature": 37.0,
            "spo2": 98,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertFalse(rule_res["rule_triggered"])

    def test_negation_hindi_chhati_dard_nahi(self):
        # "pet dard hai par chhati dard nahi hai" -> MUST NOT trigger cardiac red flag!
        raw = {
            "age": 42,
            "chief_complaint": "pet dard hai par chhati dard nahi hai",
            "bp_systolic": 124,
            "bp_diastolic": 82,
            "heart_rate": 76,
            "temperature": 37.1,
            "spo2": 98,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertFalse(rule_res["rule_triggered"])

    def test_pediatric_vital_bypass(self):
        # Child age 4 with SBP 85 (which is hypotensive for an adult, but normal for a 4-year-old)
        # Rule engine must BYPASS adult rule and notify nurse!
        raw = {
            "age": 4,
            "chief_complaint": "mild ear ache",
            "bp_systolic": 85,
            "bp_diastolic": 55,
            "heart_rate": 110,  # Normal for toddler
            "respiratory_rate": 24,
            "temperature": 37.0,
            "spo2": 99,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["pediatric_bypassed"])
        # Did not trigger adult hypotension Level 2 rule
        self.assertIsNone(rule_res["rule_level"])
        self.assertTrue(any("PEDIATRIC PATIENT" in alert for alert in rule_res["nurse_alerts"]))

    def test_anaphylaxis_level_1(self):
        # Throat closing after medication/sting
        raw = {
            "age": 25,
            "chief_complaint": "severe allergic reaction, throat closing, tongue swelling",
            "bp_systolic": 110,
            "bp_diastolic": 70,
            "heart_rate": 105,
            "temperature": 36.8,
            "spo2": 95,
        }
        cleaned = clean_patient_record(raw)
        rule_res = evaluate_rules(cleaned)
        self.assertTrue(rule_res["rule_triggered"])
        self.assertEqual(rule_res["rule_level"], 1)
        self.assertEqual(rule_res["rule_id"], "RED_FLAG_L1_ANAPHYLAXIS")


if __name__ == "__main__":
    unittest.main()
