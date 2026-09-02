"""
SENTINEL Test Suite - Chargeback Evidence Responder Validation
Tests that the auto-generated chargeback dispute dossiers meet legal & BFSI evidentiary standards:
- Clear case references
- Prioritized strong signals
- Accurate fraud classifications
- Professional merchant representment statement
"""
import os
import sys
import asyncio
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.api.schemas import TransactionRequest, PaymentMethod, Action, FraudType
from app.engine.pipeline import score_transaction


class TestChargebackEvidence(unittest.IsolatedAsyncioTestCase):

    async def test_card_testing_evidence(self):
        """Scenario 1: Card testing attack dispute evidence."""
        req = TransactionRequest(
            transaction_id="TXN_TEST_001",
            merchant_id="MERCHANT_RETAIL_1",
            amount=45.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="botnet@tempmail.com",
            metadata={"txn_count_1h": 8, "ip_risk_score": 0.85, "device_fingerprint_new": True}
        )
        res = await score_transaction(req)
        dossier = res["decision"].chargeback_evidence

        self.assertIn("DISPUTE-TXN_TEST_001", dossier)
        self.assertIn("INR 45.00", dossier)
        self.assertIn("[STRONG]", dossier)
        self.assertEqual(res["decision"].recommended_action, Action.BLOCK)
        self.assertIn(res["assessment"].fraud_type, [FraudType.CARD_TESTING, FraudType.ABUSE_RING])
        print("  [OK] Card testing dispute evidence verified")

    async def test_cross_border_mismatch_evidence(self):
        """Scenario 2: Cross-border identity mismatch."""
        req = TransactionRequest(
            transaction_id="TXN_INTL_002",
            merchant_id="MERCHANT_LUXURY_IN",
            amount=65000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            billing_country="US",
            shipping_country="IN",
            is_international=True,
            metadata={"billing_shipping_mismatch": True, "ip_risk_score": 0.70}
        )
        res = await score_transaction(req)
        dossier = res["decision"].chargeback_evidence

        self.assertIn("INR 65,000.00", dossier)
        self.assertIn("Identity", dossier)
        self.assertIn("[STRONG]", dossier)
        self.assertEqual(res["decision"].recommended_action, Action.BLOCK)
        print("  [OK] Cross-border mismatch dispute evidence verified")

    async def test_chargeback_abuser_evidence(self):
        """Scenario 3: Chronic dispute abuser friendly fraud."""
        req = TransactionRequest(
            transaction_id="TXN_DISPUTER_003",
            merchant_id="MERCHANT_ELECTRONICS",
            amount=32000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="buyer@gmail.com",
            metadata={"customer_dispute_rate": 0.45, "customer_total_txns": 20}
        )
        res = await score_transaction(req)
        dossier = res["decision"].chargeback_evidence

        self.assertIn("Customer Risk", dossier)
        self.assertIn("chargeback", dossier.lower())
        self.assertGreaterEqual(res["chargeback_score"], 70.0)
        self.assertEqual(res["assessment"].fraud_type, FraudType.CHARGEBACK_ABUSE)
        print("  [OK] Chronic chargeback abuser evidence verified")

    async def test_account_takeover_evidence(self):
        """Scenario 4: High ticket purchase from new device overnight."""
        req = TransactionRequest(
            transaction_id="TXN_ATO_004",
            merchant_id="MERCHANT_JEWELRY",
            amount=85000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            metadata={
                "device_fingerprint_new": True,
                "hour_of_day": 2,
                "is_late_night": True,
                "ip_risk_score": 0.80
            }
        )
        res = await score_transaction(req)
        dossier = res["decision"].chargeback_evidence

        self.assertIn("INR 85,000.00", dossier)
        self.assertEqual(res["decision"].recommended_action, Action.BLOCK)
        self.assertIn(res["assessment"].fraud_type, [FraudType.ACCOUNT_TAKEOVER, FraudType.CARD_FRAUD])
        print("  [OK] Account takeover dispute evidence verified")

    async def test_abuse_ring_evidence(self):
        """Scenario 5: Syndicate abuse ring detection."""
        req = TransactionRequest(
            transaction_id="TXN_RING_005",
            merchant_id="MERCHANT_GAMING",
            amount=12000.0,
            payment_method=PaymentMethod.UPI,
            device_fingerprint="abuse_ring_hash_77a",
            metadata={"device_fingerprint_new": True, "ip_risk_score": 0.95, "txn_count_24h": 15}
        )
        res = await score_transaction(req)
        dossier = res["decision"].chargeback_evidence

        self.assertIn("DISPUTE-TXN_RING_005", dossier)
        self.assertEqual(res["decision"].recommended_action, Action.BLOCK)
        self.assertGreaterEqual(res["fraud_score"], 85.0)
        print("  [OK] Abuse ring syndicate evidence verified")


if __name__ == "__main__":
    print("=" * 70)
    print("  SENTINEL - Chargeback Evidence Generation Test Suite")
    print("=" * 70)
    unittest.main()
