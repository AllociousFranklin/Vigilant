"""
SENTINEL Test Suite - API Integration Tests
Tests all FastAPI REST endpoints using in-memory ASGI transport.
"""
import os
import sys
import asyncio
import unittest
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.main import app
from app.db.database import init_db


class TestAPIIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        await init_db()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_01_assess_endpoint_valid(self):
        """Test POST /api/assess with normal transaction."""
        payload = {
            "merchant_id": "MERCHANT_TEST_IN",
            "amount": 1499.0,
            "currency": "INR",
            "payment_method": "upi",
            "customer_email": "user@example.com",
            "customer_phone": "+919876543210"
        }
        res = await self.client.post("/api/assess", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("assessment_id", data)
        self.assertIn("fraud_score", data)
        self.assertIn("chargeback_score", data)
        self.assertIn("detection", data)
        self.assertIn("assessment", data)
        self.assertIn("decision", data)
        self.assertIn("recommended_action", data["decision"])
        print(f"  [OK] POST /api/assess OK (ID: {data['assessment_id']}, Score: {data['fraud_score']})")

    async def test_02_assess_endpoint_validation_error(self):
        """Test POST /api/assess with invalid amount (<= 0)."""
        payload = {
            "merchant_id": "MERCHANT_TEST_IN",
            "amount": -50.0,
            "payment_method": "upi"
        }
        res = await self.client.post("/api/assess", json=payload)
        self.assertIn(res.status_code, [400, 422])
        print("  [OK] Validation error handled correctly (HTTP 400/422)")

    async def test_03_transactions_endpoint(self):
        """Test GET /api/transactions paginated history."""
        res = await self.client.get("/api/transactions?page=1&page_size=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        print(f"  [OK] GET /api/transactions OK (Total items: {data['total']})")

    async def test_04_stats_endpoint(self):
        """Test GET /api/stats."""
        res = await self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_assessments", data)
        self.assertIn("frauds_detected", data)
        self.assertIn("total_amount_protected", data)
        print("  [OK] GET /api/stats OK")

    async def test_05_metrics_endpoint(self):
        """Test GET /api/metrics for Razorpay Track 02 honest metrics."""
        res = await self.client.get("/api/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("precision", data)
        self.assertIn("recall", data)
        self.assertIn("f1_score", data)
        self.assertIn("confusion_matrix", data)
        self.assertIn("false_positive_cost_inr", data)
        self.assertEqual(data["kill_switch_status"], "PASSED")
        print(f"  [OK] GET /api/metrics OK (Precision: {data['precision']:.2%}, Recall: {data['recall']:.2%})")

    async def test_06_health_endpoint(self):
        """Test GET /api/health."""
        res = await self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["service"], "SENTINEL")
        self.assertEqual(data["status"], "healthy")
        print("  [OK] GET /api/health OK")

    async def test_07_feedback_and_dispute_endpoint(self):
        """Test POST /api/feedback and GET /api/dispute/{id}."""
        # 1. Create a flagged transaction
        payload = {
            "transaction_id": "TXN_DISPUTE_API_TEST",
            "merchant_id": "MERCHANT_API",
            "amount": 29000.0,
            "payment_method": "credit_card",
            "metadata": {"customer_dispute_rate": 0.50}
        }
        assess_res = await self.client.post("/api/assess", json=payload)
        self.assertEqual(assess_res.status_code, 200)
        asm_id = assess_res.json()["assessment_id"]

        # 2. Retrieve dispute dossier
        disp_res = await self.client.get(f"/api/dispute/{asm_id}")
        self.assertEqual(disp_res.status_code, 200)
        disp_data = disp_res.json()
        self.assertIn("dossier_text", disp_data)
        self.assertIn("SENTINEL CHARGEBACK EVIDENCE", disp_data["dossier_text"])

        # 3. Submit feedback
        fb_payload = {
            "transaction_id": "TXN_DISPUTE_API_TEST",
            "outcome": "chargeback_won",
            "notes": "Merchant representment accepted by card network"
        }
        fb_res = await self.client.post("/api/feedback", json=fb_payload)
        self.assertEqual(fb_res.status_code, 200)
        self.assertTrue(fb_res.json()["success"])
        print("  [OK] POST /api/feedback & GET /api/dispute OK")


if __name__ == "__main__":
    print("=" * 70)
    print("  SENTINEL - API Integration Test Suite")
    print("=" * 70)
    unittest.main()
