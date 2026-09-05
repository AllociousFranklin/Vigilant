"""
SENTINEL - Brutal Real-World Adversarial & Edge-Case Benchmark Suite

Tests realistic, high-difficulty Indian BFSI payment scenarios:
1. Adversarial Evasion (Fraudsters staying just below policy floors)
2. Legitimate High-Stress Edge Cases (Hospital emergency, flash sales, expat gifting)
3. Friendly Fraud & Chargeback Abuse nuances
4. Zero-telemetry and chaotic data conditions

Produces honest metrics, diagnostics, and failure analysis.
"""
import os
import sys
import asyncio
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.api.schemas import TransactionRequest, PaymentMethod, Action, RiskLevel
from app.engine.pipeline import score_transaction


@dataclass
class Scenario:
    id: str
    name: str
    category: str
    ground_truth: str  # 'FRAUD' or 'LEGITIMATE'
    expected_action: str  # 'BLOCK', 'ALLOW', or 'REVIEW'
    request: TransactionRequest
    context_notes: str


def build_scenarios() -> list[Scenario]:
    scenarios = []

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 1: ADVERSARIAL EVASION (Fraudsters evading rules)
    # ═══════════════════════════════════════════════════════════════

    # 1.1 Evasive Micro-Testing: Tested with INR 149 instead of < 100, 4 txns/hr (just under 5 threshold)
    scenarios.append(Scenario(
        id="ADV-01",
        name="Evasive Micro-Testing (INR 149, 4 txns/hr)",
        category="Adversarial Evasion",
        ground_truth="FRAUD",
        expected_action="BLOCK",
        request=TransactionRequest(
            transaction_id="TXN_ADV_01",
            merchant_id="MERCH_PAY_GATEWAY",
            amount=149.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="anon.test.9182@gmail.com",
            metadata={
                "txn_count_1h": 4,  # Just below the >= 5 velocity spike rule
                "txn_count_24h": 6,
                "is_first_time_card": True,
                "ip_risk_score": 0.45,  # Moderate residential proxy
                "device_fingerprint_new": True,
            }
        ),
        context_notes="Fraudster tests stolen card with INR 149 (evading <100 card test rule) and 4 txns/hr (evading >=5 velocity rule)."
    ))

    # 1.2 Low-and-Slow Account Takeover at 8:30 PM (Evades Late Night ATO rule)
    scenarios.append(Scenario(
        id="ADV-02",
        name="Prime-Time ATO with Clean Residential IP",
        category="Adversarial Evasion",
        ground_truth="FRAUD",
        expected_action="BLOCK",
        request=TransactionRequest(
            transaction_id="TXN_ADV_02",
            merchant_id="MERCH_APPLE_RESELLER",
            amount=89900.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="compromised.user@infosys.com",
            customer_phone="+919845012345",
            metadata={
                "device_fingerprint_new": True,
                "is_late_night": False,  # Transacts at 8:30 PM (evades overnight ATO rule)
                "hour_of_day": 20,
                "ip_risk_score": 0.25,  # Clean Jio/Airtel residential broadband proxy
                "txn_count_1h": 0,
                "customer_account_age_days": 800,  # Old compromised account
                "customer_total_txns": 45,
                "customer_dispute_rate": 0.0,
            }
        ),
        context_notes="Stolen credentials used for iPhone purchase at 8:30 PM on residential IP. Evades late-night rule."
    ))

    # 1.3 Strategic Chargeback Abuser: 28% dispute rate (evades >= 35% chronic disputer rule)
    scenarios.append(Scenario(
        id="ADV-03",
        name="Strategic Friendly Fraud (28% Dispute Rate)",
        category="Adversarial Evasion",
        ground_truth="FRAUD",
        expected_action="BLOCK",
        request=TransactionRequest(
            transaction_id="TXN_ADV_03",
            merchant_id="MERCH_LUXURY_WATCH",
            amount=42000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="smart.disputer@yahoo.com",
            metadata={
                "customer_dispute_rate": 0.28,  # Below 35% rule floor
                "customer_total_txns": 25,
                "customer_account_age_days": 240,
                "device_fingerprint_new": False,
                "ip_risk_score": 0.15,
                "is_first_time_card": False,
            }
        ),
        context_notes="Chronic friendly fraudster keeps dispute rate at 28% to avoid the 35% hard rule floor."
    ))

    # 1.4 Distributed Carding Ring (1 txn per identity, identical BIN & merchant)
    scenarios.append(Scenario(
        id="ADV-04",
        name="Distributed Syndicate (Decentralized Botnet)",
        category="Adversarial Evasion",
        ground_truth="FRAUD",
        expected_action="BLOCK",
        request=TransactionRequest(
            transaction_id="TXN_ADV_04",
            merchant_id="MERCH_DIGITAL_GIFT_CARDS",
            amount=4999.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="botnet_node_44@tempmail.com",
            card_bin="411111",
            metadata={
                "txn_count_1h": 1,  # Only 1 txn from this bot node
                "txn_count_24h": 1,
                "device_fingerprint_new": True,
                "ip_risk_score": 0.65,  # Just below 0.70 syndicate floor
                "email_domain_risk": 0.90,  # Disposable
                "phone_verified": False,
            }
        ),
        context_notes="Syndicate attacks with disposable email and proxy, but only 1 transaction per node to evade velocity counters."
    ))

    # 1.5 Synthetic Identity Mule (New company domain, high value)
    scenarios.append(Scenario(
        id="ADV-05",
        name="Synthetic Identity Mule Account",
        category="Adversarial Evasion",
        ground_truth="FRAUD",
        expected_action="BLOCK",
        request=TransactionRequest(
            transaction_id="TXN_ADV_05",
            merchant_id="MERCH_B2B_ELECTRONICS",
            amount=65000.0,
            payment_method=PaymentMethod.NET_BANKING,
            customer_email="director@shady-logistics-llp.in",  # Not in disposable list
            metadata={
                "customer_account_age_days": 1,
                "customer_total_txns": 1,
                "phone_verified": False,
                "device_fingerprint_new": True,
                "ip_risk_score": 0.55,
            }
        ),
        context_notes="Newly minted synthetic business persona with day-old account transacting INR 65k via NetBanking."
    ))

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 2: REAL-LIFE FALSE POSITIVE TRAPS (Legitimate Stress)
    # ═══════════════════════════════════════════════════════════════

    # 2.1 3:00 AM Emergency Hospital UPI (Triggers ATO Rule: New device + High Value + Late Night)
    scenarios.append(Scenario(
        id="LEGIT-01",
        name="3:00 AM Emergency Hospital ICU Deposit",
        category="Legitimate Stress",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_HOSPITAL_01",
            merchant_id="MERCH_APOLLO_HOSPITALS",
            amount=75000.0,
            payment_method=PaymentMethod.UPI,
            customer_email="sunita.sharma@gmail.com",
            customer_phone="+919811223344",
            metadata={
                "device_fingerprint_new": True,  # Using daughter's phone at hospital desk
                "is_late_night": True,  # 3:15 AM emergency
                "hour_of_day": 3,
                "is_high_value": True,
                "customer_account_age_days": 900,
                "customer_total_txns": 140,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "ip_risk_score": 0.05,
                "txn_count_1h": 0,
            }
        ),
        context_notes="Critical false-positive trap: INR 75k ICU payment at 3 AM from daughter's phone. ATO rule risk!"
    ))

    # 2.2 Big Billion Day / Diwali Midnight Flash Sale
    scenarios.append(Scenario(
        id="LEGIT-02",
        name="Diwali Midnight Flash Sale (iPhone 16)",
        category="Legitimate Stress",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_FLASHSALE_02",
            merchant_id="MERCH_FLIPKART_BIG_BILLION",
            amount=79900.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="kartik.iyer@tcs.com",
            customer_phone="+919920304050",
            metadata={
                "device_fingerprint_new": True,  # Bought brand new iPad on sale
                "is_late_night": True,  # Midnight 12:05 AM launch
                "hour_of_day": 0,
                "customer_account_age_days": 1200,
                "customer_total_txns": 210,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "ip_risk_score": 0.02,
                "txn_count_1h": 1,
            }
        ),
        context_notes="Established customer buying iPhone at midnight launch on new iPad. Late night + new device."
    ))

    # 2.3 NRI Expat Sending Diwali Gift to Parents (Cross-border mismatch)
    scenarios.append(Scenario(
        id="LEGIT-03",
        name="NRI Expat Gifting Parents in Bangalore",
        category="Legitimate Stress",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_NRI_03",
            merchant_id="MERCH_TANISHQ_JEWELLERY",
            amount=55000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="anand.venkat@microsoft.com",
            billing_country="US",
            shipping_country="IN",
            is_international=True,
            metadata={
                "billing_shipping_mismatch": True,  # Billed in Seattle, shipped to Bangalore
                "is_international": True,
                "is_high_value": True,
                "customer_account_age_days": 730,
                "customer_total_txns": 35,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "ip_risk_score": 0.03,
            }
        ),
        context_notes="NRI in Seattle gifting jewelry to parents in India. Cross-border + address mismatch."
    ))

    # 2.4 Wedding Gold Purchase (Akshaya Tritiya INR 3,50,000)
    scenarios.append(Scenario(
        id="LEGIT-04",
        name="Akshaya Tritiya Gold (INR 3,50,000 UPI)",
        category="Legitimate Stress",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_GOLD_04",
            merchant_id="MERCH_MALABAR_GOLD",
            amount=350000.0,
            payment_method=PaymentMethod.UPI,
            customer_email="rajendra.prasad@yahoo.co.in",
            customer_phone="+919440112233",
            metadata={
                "customer_account_age_days": 1800,  # 5 years
                "customer_total_txns": 350,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "device_fingerprint_new": False,
                "ip_risk_score": 0.01,
                "txn_count_1h": 0,
                "hour_of_day": 16,
                "merchant_avg_txn": 45000.0,
            }
        ),
        context_notes="Massive INR 3.5L gold purchase for wedding. High amount anomaly on 5-year trusted customer."
    ))

    # 2.5 College Student Daily UPI Groceries / Food Burst (3 txns in 30 mins)
    scenarios.append(Scenario(
        id="LEGIT-05",
        name="Exam Night Quick-Commerce Burst (3 txns/hr)",
        category="Legitimate Stress",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_ZEPTO_05",
            merchant_id="MERCH_ZEPTO_DELIVERY",
            amount=180.0,
            payment_method=PaymentMethod.UPI,
            customer_email="rohit.bits@gmail.com",
            customer_phone="+919870011223",
            metadata={
                "txn_count_1h": 3,  # Ordered snacks, then Red Bull, then notes
                "txn_count_24h": 4,
                "customer_account_age_days": 180,
                "customer_total_txns": 40,
                "customer_dispute_rate": 0.0,
                "phone_verified": True,
                "device_fingerprint_new": False,
                "ip_risk_score": 0.02,
            }
        ),
        context_notes="Student making multiple rapid micro-orders on Zepto during exam week. Should not trigger card testing or velocity."
    ))

    # 2.6 Senior Citizen First-Time E-Pharmacy Buyer
    scenarios.append(Scenario(
        id="LEGIT-06",
        name="Senior Citizen First E-Pharmacy Order",
        category="Legitimate Stress",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_PHARMA_06",
            merchant_id="MERCH_1MG_HEALTHCARE",
            amount=3200.0,
            payment_method=PaymentMethod.DEBIT_CARD,
            customer_email="krishnamurthy1954@gmail.com",
            metadata={
                "customer_account_age_days": 2,  # Brand new user
                "customer_total_txns": 1,
                "phone_verified": False,  # Struggled with OTP
                "device_fingerprint_new": True,
                "ip_risk_score": 0.08,
            }
        ),
        context_notes="70-year old retiree buying monthly insulin. New device, unverified phone, brand new account."
    ))

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 3: REALISTIC CHARGEBACK & RETURN SCENARIOS
    # ═══════════════════════════════════════════════════════════════

    # 3.1 Wardrobing / Serial Returner (High return propensity)
    scenarios.append(Scenario(
        id="CB-01",
        name="Serial Wardrobing Returner (Luxury Fashion)",
        category="Return & Chargeback",
        ground_truth="FRAUD",
        expected_action="REVIEW",
        request=TransactionRequest(
            transaction_id="TXN_FASHION_01",
            merchant_id="MERCH_MYNTRA_LUXE",
            amount=28000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="fashionista.glam@gmail.com",
            metadata={
                "customer_dispute_rate": 0.20,
                "customer_total_txns": 15,
                "customer_account_age_days": 120,
                "is_first_time_card": False,
                "device_fingerprint_new": False,
                "ip_risk_score": 0.10,
            }
        ),
        context_notes="High return propensity cardholder buying expensive party wear with history of returns/disputes."
    ))

    # 3.2 High-Ticket Electronics First-Time Claim
    scenarios.append(Scenario(
        id="CB-02",
        name="First-Time 'Package Empty' Fraud (INR 68,000 GPU)",
        category="Return & Chargeback",
        ground_truth="FRAUD",
        expected_action="REVIEW",
        request=TransactionRequest(
            transaction_id="TXN_GPU_02",
            merchant_id="MERCH_COMPUTRONICS",
            amount=68000.0,
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_email="gamer_apex@yahoo.com",
            metadata={
                "is_first_time_card": True,
                "customer_dispute_rate": 0.10,
                "customer_total_txns": 3,
                "customer_account_age_days": 30,
                "device_fingerprint_new": True,
                "ip_risk_score": 0.35,
            }
        ),
        context_notes="New gamer account ordering RTX 4080 with first-time card. High likelihood of claiming item not received."
    ))

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 4: ZERO-TELEMETRY & CHAOTIC EDGE INPUTS
    # ═══════════════════════════════════════════════════════════════

    # 4.1 Zero-Metadata Payload (Webhooks where enrichment failed)
    scenarios.append(Scenario(
        id="CHAOS-01",
        name="Zero-Metadata Ingestion Fallback",
        category="Data Chaos",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_CHAOS_01",
            merchant_id="MERCH_GENERIC_STORE",
            amount=1250.0,
            payment_method=PaymentMethod.UPI,
            # No metadata, no customer info, no device
        ),
        context_notes="Webhook arrived with only merchant, amount, and payment method. Engine must not crash or wildly misclassify."
    ))

    # 4.2 INR 1.00 Micro-Verification Auth
    scenarios.append(Scenario(
        id="CHAOS-02",
        name="INR 1.00 Micro-Auth Penny Drop",
        category="Data Chaos",
        ground_truth="LEGITIMATE",
        expected_action="ALLOW",
        request=TransactionRequest(
            transaction_id="TXN_PENNY_02",
            merchant_id="MERCH_BANK_VERIFY",
            amount=1.0,
            payment_method=PaymentMethod.UPI,
            customer_email="account.check@hdfcbank.com",
            metadata={
                "txn_count_1h": 0,
                "customer_account_age_days": 500,
            }
        ),
        context_notes="Pennny drop INR 1 bank mandate verification. Must not be flagged as card testing if single transaction."
    ))

    return scenarios


async def run_brutal_benchmark():
    scenarios = build_scenarios()

    print("=" * 80)
    print("  [SENTINEL] BRUTAL REAL-WORLD ADVERSARIAL BENCHMARK SUITE")
    print("  Testing 16 High-Difficulty Real-Life Indian BFSI Edge Cases")
    print("=" * 80)

    results = []
    
    tp = 0  # Fraud correctly BLOCKED / REVIEWED
    tn = 0  # Legit correctly ALLOWED
    fp = 0  # Legit wrongly BLOCKED / REVIEWED (False decline)
    fn = 0  # Fraud wrongly ALLOWED (Leaked fraud)

    category_stats = {}

    for s in scenarios:
        res = await score_transaction(s.request)
        fraud_score = res["fraud_score"]
        cb_score = res["chargeback_score"]
        action = res["decision"].recommended_action.value
        risk_level = res["assessment"].risk_level.value
        reasons = [r.reason for r in res["assessment"].reasons]
        overrides = [r.reason for r in res["assessment"].reasons if r.signal_strength == "POLICY_OVERRIDE"]

        is_fraud = (s.ground_truth == "FRAUD")
        
        if is_fraud:
            if action in ["BLOCK", "REVIEW"]:
                outcome = "CORRECT_DETECTION [TP]"
                tp += 1
            else:
                outcome = "MISSED_FRAUD [FN] [FAIL]"
                fn += 1
        else:
            if action == "ALLOW":
                outcome = "CLEAN_ALLOW [TN] [PASS]"
                tn += 1
            elif action == "REVIEW":
                outcome = "FRICTION_ALERT [FP-Mild] [REVIEW_FRICTION]"
                fp += 1
            else:  # BLOCK
                outcome = "FALSE_DECLINE [FP-Critical] [FALSE_BLOCK]"
                fp += 1

        cat = s.category
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0}
        category_stats[cat]["total"] += 1
        if "CORRECT" in outcome or "CLEAN" in outcome:
            category_stats[cat]["correct"] += 1

        print(f"\n[{s.id}] {s.name}")
        print(f"  Category    : {s.category}")
        print(f"  Ground Truth: {s.ground_truth} | Expected: {s.expected_action}")
        print(f"  SENTINEL    : Score={fraud_score:.1f} | CB_Score={cb_score:.1f} | Action={action} | Risk={risk_level}")
        if overrides:
            print(f"  Overrides   : {overrides}")
        print(f"  Outcome     : {outcome}")
        print(f"  Context     : {s.context_notes}")

        results.append({
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "ground_truth": s.ground_truth,
            "expected_action": s.expected_action,
            "fraud_score": fraud_score,
            "chargeback_score": cb_score,
            "sentinel_action": action,
            "sentinel_risk": risk_level,
            "overrides": overrides,
            "outcome": outcome,
            "context": s.context_notes
        })

    # ═══════════════════════════════════════════════════════════════
    # SUMMARY METRICS
    # ═══════════════════════════════════════════════════════════════
    total = len(scenarios)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    print("\n" + "=" * 80)
    print("  [REPORT] BRUTAL BENCHMARK EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total High-Difficulty Scenarios : {total}")
    print(f"True Positives (Fraud Caught)   : {tp}")
    print(f"True Negatives (Legit Allowed)  : {tn}")
    print(f"False Positives (Legit Flagged) : {fp}")
    print(f"False Negatives (Fraud Leaked)  : {fn}")
    print(f"Brutal Precision                : {precision:.2%}")
    print(f"Brutal Recall                   : {recall:.2%}")
    print(f"Brutal Overall Accuracy         : {accuracy:.2%}")

    print("\nCategory Breakdown:")
    for cat, stats in category_stats.items():
        pct = stats["correct"] / stats["total"] * 100.0
        print(f"  * {cat:28s}: {stats['correct']}/{stats['total']} passed ({pct:.1f}%)")

    print("=" * 80)

    # Save to json report
    report_path = os.path.join(os.path.dirname(__file__), '..', 'test_results', 'brutal_test_report.json')
    with open(report_path, 'w') as f:
        json.dump({
            "total_scenarios": total,
            "metrics": {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "accuracy": round(accuracy, 4),
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn,
            },
            "category_breakdown": category_stats,
            "detailed_results": results
        }, f, indent=2)

    print(f"\nDetailed report saved to: {report_path}")
    return results


if __name__ == "__main__":
    asyncio.run(run_brutal_benchmark())
