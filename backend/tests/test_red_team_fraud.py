"""
SENTINEL Red Team Test Suite - Adversarial Attacks & False-Positive Stress Tests
Tests 6 realistic edge cases spanning automated attacks, syndicates, and legitimate high-ticket transactions.
"""
import os
import sys
import unittest
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.api.schemas import TransactionRequest, PaymentMethod, Action, RiskLevel
from app.engine.pipeline import score_transaction


class TestRedTeamFraud(unittest.IsolatedAsyncioTestCase):

    async def test_01_velocity_attack(self):
        """Red Team 1: 10 transactions within 1 minute from automated script."""
        req = TransactionRequest(
            merchant_id="MERCH_QUICK_PAY",
            amount=4999.0,
            payment_method=PaymentMethod.UPI,
            device_fingerprint="dev_bot_burst_01",
            metadata={"txn_count_1h": 10, "txn_count_24h": 15}
        )
        res = await score_transaction(req)
        print(f"\n[RED TEAM 1: Velocity Attack] Score: {res['fraud_score']}, Action: {res['decision'].recommended_action.value}")
        self.assertGreaterEqual(res['fraud_score'], 80.0)
        self.assertEqual(res['decision'].recommended_action, Action.BLOCK)

    async def test_02_card_testing_pattern(self):
        """Red Team 2: Micro-transaction enumeration attack (< INR 100)."""
        req = TransactionRequest(
            merchant_id="MERCH_GATEWAY",
            amount=49.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            metadata={"txn_count_1h": 6}
        )
        res = await score_transaction(req)
        print(f"[RED TEAM 2: Card Testing] Score: {res['fraud_score']}, Action: {res['decision'].recommended_action.value}")
        self.assertGreaterEqual(res['fraud_score'], 80.0)
        self.assertEqual(res['decision'].recommended_action, Action.BLOCK)

    async def test_03_legitimate_high_value_must_not_block(self):
        """Red Team 3: INR 200,000 legitimate purchase from 3-year customer (False Positive Stress)."""
        req = TransactionRequest(
            merchant_id="MERCH_TATACLIQ_LUXURY",
            amount=200000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="vip_patron@corporation.com",
            customer_phone="+919876543210",
            billing_country="IN",
            shipping_country="IN",
            metadata={
                "customer_account_age_days": 1095,  # 3 years
                "customer_total_txns": 180,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "device_fingerprint_new": False,
                "ip_risk_score": 0.01,
                "txn_count_1h": 0,
                "is_late_night": False,
                "hour_of_day": 14,
                "merchant_avg_txn": 80000.0,
            }
        )
        res = await score_transaction(req)
        print(f"[RED TEAM 3: Legit High-Value (INR 200k)] Score: {res['fraud_score']}, Action: {res['decision'].recommended_action.value}")
        # MUST NOT BE BLOCKED - Must be ALLOW or at worst REVIEW for high-ticket
        self.assertLess(res['fraud_score'], 35.0)
        self.assertEqual(res['decision'].recommended_action, Action.ALLOW)

    async def test_04_abuse_ring_syndicate(self):
        """Red Team 4: New device, proxy routing, disposable email, international card."""
        req = TransactionRequest(
            merchant_id="MERCH_DIGITAL_CARDS",
            amount=25000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="attacker77@mailinator.com",
            billing_country="US",
            shipping_country="IN",
            is_international=True,
            metadata={
                "device_fingerprint_new": True,
                "ip_risk_score": 0.92,
                "txn_count_24h": 8,
                "billing_shipping_mismatch": True
            }
        )
        res = await score_transaction(req)
        print(f"[RED TEAM 4: Abuse Ring] Score: {res['fraud_score']}, Action: {res['decision'].recommended_action.value}")
        self.assertGreaterEqual(res['fraud_score'], 85.0)
        self.assertEqual(res['decision'].recommended_action, Action.BLOCK)

    async def test_05_normal_upi_groceries(self):
        """Red Team 5: Routine daily UPI groceries of INR 450."""
        req = TransactionRequest(
            merchant_id="MERCH_ZEPTO_DAILY",
            amount=450.0,
            payment_method=PaymentMethod.UPI,
            customer_email="rajesh.kumar@gmail.com",
            customer_phone="+919988776655",
            metadata={
                "customer_account_age_days": 400,
                "customer_total_txns": 120,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "device_fingerprint_new": False,
                "ip_risk_score": 0.02,
                "txn_count_1h": 0,
            }
        )
        res = await score_transaction(req)
        print(f"[RED TEAM 5: Routine UPI INR 450] Score: {res['fraud_score']}, Action: {res['decision'].recommended_action.value}")
        self.assertLess(res['fraud_score'], 15.0)
        self.assertEqual(res['decision'].recommended_action, Action.ALLOW)

    async def test_06_chargeback_abuser(self):
        """Red Team 6: Friendly fraud cardholder with 40% dispute rate."""
        req = TransactionRequest(
            merchant_id="MERCH_ELECTRONICS_HUB",
            amount=38000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            metadata={"customer_dispute_rate": 0.40, "customer_total_txns": 25}
        )
        res = await score_transaction(req)
        print(f"[RED TEAM 6: Chargeback Abuser] CB Score: {res['chargeback_score']}, Action: {res['decision'].recommended_action.value}")
        self.assertGreaterEqual(res['chargeback_score'], 70.0)
        self.assertIn(res['decision'].recommended_action, [Action.BLOCK, Action.REVIEW])


if __name__ == "__main__":
    print("=" * 70)
    print("  SENTINEL - Red Team Fraud & Adversarial Resilience Test Suite")
    print("=" * 70)
    unittest.main()
