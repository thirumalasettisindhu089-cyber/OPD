"""
backend/tests/test_api.py - Integration tests for FastAPI endpoints
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app


class TestTriageAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_get_rules_endpoint(self):
        res = self.client.get("/api/rules")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("rules", data)
        self.assertGreater(data["total_rules"], 5)

    def test_get_metrics_endpoint(self):
        res = self.client.get("/api/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ablations", data)
        self.assertIn("full_pipeline", data["ablations"])
        self.assertIn("emergency_recall", data["ablations"]["full_pipeline"])

    def test_triage_latency_under_200ms(self):
        payload = {
            "patient_id": "TEST_SPEED",
            "age": 45,
            "sex": "M",
            "chief_complaint": "routine blood pressure check, no pain",
            "bp_systolic": 125,
            "bp_diastolic": 82,
            "heart_rate": 72,
            "temperature": 37.0,
            "spo2": 98
        }
        res = self.client.post("/api/triage", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertLess(data["latency_ms"], 200.0)
        self.assertIn("disclaimer", data)
        self.assertIn("triage_level", data)

    def test_preset_telugu_chest_pain(self):
        payload = {
            "age": 52,
            "sex": "M",
            "chief_complaint": "gunde noppi severe ga undi, eeda thammudu cheyyi laakkuntundi",
            "bp_systolic": 135,
            "bp_diastolic": 90,
            "heart_rate": 96,
            "temperature": 37.1,
            "spo2": 97
        }
        res = self.client.post("/api/triage", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["triage_level"], 2)
        self.assertTrue(data["is_emergency"])
        self.assertIn("Emergency / Cardiology", data["recommended_department"])


if __name__ == "__main__":
    unittest.main()
