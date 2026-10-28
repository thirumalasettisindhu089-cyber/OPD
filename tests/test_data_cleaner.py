"""
tests/test_data_cleaner.py - Unit tests for data cleaning & vitals sanitization
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import unittest
from backend.data_cleaner import (
    clean_patient_record,
    clean_text_complaint,
    collapse_repeated_characters,
    normalize_column_name,
)


class TestDataCleaner(unittest.TestCase):

    def test_column_alias_mapping(self):
        self.assertEqual(normalize_column_name("cc"), "chief_complaint")
        self.assertEqual(normalize_column_name("presenting_complaint"), "chief_complaint")
        self.assertEqual(normalize_column_name("sbp"), "bp_systolic")
        self.assertEqual(normalize_column_name("sys_bp"), "bp_systolic")
        self.assertEqual(normalize_column_name("pulse"), "heart_rate")
        self.assertEqual(normalize_column_name("temp_f"), "temperature")
        self.assertEqual(normalize_column_name("o2_sat"), "spo2")

    def test_impossible_vitals_zero_bp(self):
        record = {
            "age": 45,
            "cc": "feeling weak",
            "bp_systolic": 0,
            "bp_diastolic": 0,
            "heart_rate": 80,
            "temperature": 37.0,
            "spo2": 98,
        }
        res = clean_patient_record(record)
        # 0 BP must be treated as MISSING, NEVER normal
        self.assertIsNone(res["bp_systolic"])
        self.assertTrue(res["flags"]["bp_systolic_missing"])
        self.assertTrue(res["flags"]["bp_systolic_impossible"])

    def test_impossible_vitals_spo2_over_100(self):
        record = {
            "age": 30,
            "cc": "cough",
            "bp_systolic": 120,
            "heart_rate": 72,
            "spo2": 105,  # Physically impossible sensor artifact
        }
        res = clean_patient_record(record)
        self.assertIsNone(res["spo2"])
        self.assertTrue(res["flags"]["spo2_missing"])
        self.assertTrue(res["flags"]["spo2_impossible"])

    def test_fahrenheit_auto_conversion(self):
        # 98.6 entered in Celsius box
        record = {
            "age": 28,
            "cc": "mild fever",
            "temperature": 98.6,
        }
        res = clean_patient_record(record)
        self.assertTrue(res["flags"]["temp_fahrenheit_corrected"])
        self.assertAlmostEqual(res["temperature"], 37.0, places=1)

        # 96 C entered in Celsius box (classic hackathon prompt case)
        # 96 F = (96 - 32) * 5/9 = 35.55 C
        record_96 = {
            "age": 50,
            "cc": "cold",
            "temperature": 96.0,
        }
        res_96 = clean_patient_record(record_96)
        self.assertTrue(res_96["flags"]["temp_fahrenheit_corrected"])
        self.assertAlmostEqual(res_96["temperature"], 35.6, places=1)

    def test_text_normalization_repeated_letters(self):
        raw = "heaaaadacheee and paaain in chesst"
        cleaned = clean_text_complaint(raw)
        self.assertIn("headache", cleaned)
        self.assertIn("pain", cleaned)

    def test_pediatric_flag(self):
        rec_ped = {"age": 5, "cc": "fever"}
        res_ped = clean_patient_record(rec_ped)
        self.assertTrue(res_ped["is_pediatric"])

        rec_adult = {"age": 24, "cc": "fever"}
        res_adult = clean_patient_record(rec_adult)
        self.assertFalse(res_adult["is_pediatric"])


if __name__ == "__main__":
    unittest.main()
