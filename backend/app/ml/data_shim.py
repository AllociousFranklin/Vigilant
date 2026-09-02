"""
SENTINEL Data Shim - Canonical Training Data Builder

Generates realistic synthetic Indian BFSI payment transactions with specific fraud
and legitimate behavioral patterns. Outputs training_v3.parquet.
Includes:
- 30 normalized features matching app.engine.features.ALL_FEATURE_NAMES exactly
- Dual target labels: 'label' (fraud) and 'chargeback_label' (dispute propensity)
- Dedicated kill-switch guardrail corpus of legitimate high-value transactions.
"""
import os
import sys
import math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.engine.features import ALL_FEATURE_NAMES, extract_all_features


def generate_canonical_dataset() -> pd.DataFrame:
    np.random.seed(42)
    rows = []

    # Helper for round amount logic consistent with features.py
    def check_round_amount(amt: float) -> float:
        return 1.0 if (amt % 500 == 0 and amt >= 500) else 0.0

    # ─────────────────────────────────────────────────────────────
    # 1. FRAUD PATTERNS (Total = 5000)
    # ─────────────────────────────────────────────────────────────

    # 1.1 Card Testing (n=800): Rapid small amounts, card testing botnet
    # Low chargeback rate because caught before settlement or below dispute threshold
    for _ in range(800):
        amount = float(np.random.uniform(10, 99))
        merch_avg = 5000.0
        merch_std = 3000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 0.0,
            'hour_of_day': np.random.uniform(0.0, 1.0),
            'is_weekend': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_late_night': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'days_since_last_txn': np.random.uniform(0.0, 0.05),
            'txn_count_1h': np.random.uniform(0.5, 1.0),       # 5 to 10+ txns in 1 hour
            'txn_count_24h': np.random.uniform(0.3, 0.9),
            'distinct_merchants_1h': np.random.uniform(0.4, 1.0),
            'amount_sum_24h_log': math.log(np.random.uniform(500, 5000) + 1),
            'payment_method_risk': 0.35,                       # Credit card
            'is_international': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_first_time_card': 1.0,
            'card_bin_risk': np.random.uniform(0.25, 0.35),
            'customer_account_age_log': math.log(np.random.randint(1, 10) + 1),
            'customer_total_txns_log': math.log(np.random.randint(1, 5) + 1),
            'customer_dispute_rate': np.random.uniform(0.0, 0.1),
            'email_domain_risk': np.random.choice([0.30, 0.90], p=[0.4, 0.6]),
            'phone_verified': float(np.random.choice([0, 1], p=[0.8, 0.2])),
            'merchant_fraud_rate_30d': np.random.uniform(0.02, 0.08),
            'merchant_category_risk': 0.45,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(365 + 1),
            'device_fingerprint_new': float(np.random.choice([0, 1], p=[0.3, 0.7])),
            'ip_risk_score': np.random.uniform(0.6, 0.95),
            'geo_distance_score': np.random.uniform(0.3, 0.9),
            'billing_shipping_mismatch': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'label': 1,
            'chargeback_label': 0,
            'source': 'fraud_card_testing'
        }
        rows.append(row)

    # 1.2 Velocity Spike (n=800): Sudden burst of high volume purchases
    for _ in range(800):
        if np.random.rand() < 0.25:
            amount = float(np.random.choice([5000, 10000, 15000, 20000, 25000, 50000]))
        else:
            amount = float(np.random.uniform(1000, 50000))
        merch_avg = 8000.0
        merch_std = 4000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 1.0 if amount > 50000 else 0.0,
            'hour_of_day': np.random.uniform(0.0, 1.0),
            'is_weekend': float(np.random.choice([0, 1], p=[0.6, 0.4])),
            'is_late_night': float(np.random.choice([0, 1], p=[0.4, 0.6])),
            'days_since_last_txn': np.random.uniform(0.0, 0.02),
            'txn_count_1h': np.random.uniform(0.6, 1.0),       # High velocity
            'txn_count_24h': np.random.uniform(0.5, 1.0),
            'distinct_merchants_1h': np.random.uniform(0.2, 0.8),
            'amount_sum_24h_log': math.log(np.random.uniform(30000, 200000) + 1),
            'payment_method_risk': np.random.choice([0.35, 0.20, 0.15], p=[0.6, 0.2, 0.2]),
            'is_international': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_first_time_card': float(np.random.choice([0, 1], p=[0.4, 0.6])),
            'card_bin_risk': np.random.uniform(0.20, 0.35),
            'customer_account_age_log': math.log(np.random.randint(5, 60) + 1),
            'customer_total_txns_log': math.log(np.random.randint(5, 30) + 1),
            'customer_dispute_rate': np.random.uniform(0.05, 0.30),
            'email_domain_risk': np.random.choice([0.30, 0.90], p=[0.6, 0.4]),
            'phone_verified': float(np.random.choice([0, 1], p=[0.6, 0.4])),
            'merchant_fraud_rate_30d': np.random.uniform(0.02, 0.06),
            'merchant_category_risk': np.random.choice([0.45, 0.40, 0.35]),
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(500 + 1),
            'device_fingerprint_new': float(np.random.choice([0, 1], p=[0.4, 0.6])),
            'ip_risk_score': np.random.uniform(0.4, 0.85),
            'geo_distance_score': np.random.uniform(0.3, 0.8),
            'billing_shipping_mismatch': float(np.random.choice([0, 1], p=[0.6, 0.4])),
            'label': 1,
            'chargeback_label': 0,
            'source': 'fraud_velocity_spike'
        }
        rows.append(row)

    # 1.3 High Value from New Device (n=800): ATO or stolen credentials
    for _ in range(800):
        if np.random.rand() < 0.3:
            amount = float(np.random.choice([50000, 75000, 100000, 150000, 200000]))
        else:
            amount = float(np.random.uniform(35000, 200000))
        merch_avg = 10000.0
        merch_std = 6000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 1.0,
            'hour_of_day': np.random.uniform(0.05, 0.25),      # Late night hours
            'is_weekend': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'is_late_night': 1.0,
            'days_since_last_txn': np.random.uniform(0.3, 1.0),
            'txn_count_1h': np.random.uniform(0.1, 0.4),
            'txn_count_24h': np.random.uniform(0.1, 0.4),
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + 1000),
            'payment_method_risk': 0.35,
            'is_international': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'is_first_time_card': 1.0,
            'card_bin_risk': np.random.uniform(0.25, 0.35),
            'customer_account_age_log': math.log(np.random.randint(1, 30) + 1),
            'customer_total_txns_log': math.log(np.random.randint(1, 10) + 1),
            'customer_dispute_rate': np.random.uniform(0.0, 0.2),
            'email_domain_risk': np.random.choice([0.30, 0.90], p=[0.5, 0.5]),
            'phone_verified': 0.0,
            'merchant_fraud_rate_30d': np.random.uniform(0.02, 0.07),
            'merchant_category_risk': 0.45,                    # Electronics/luxury
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(300 + 1),
            'device_fingerprint_new': 1.0,                     # Always new device!
            'ip_risk_score': np.random.uniform(0.7, 0.95),     # Proxy/VPN
            'geo_distance_score': np.random.uniform(0.5, 1.0),
            'billing_shipping_mismatch': 1.0,
            'label': 1,
            'chargeback_label': 0,
            'source': 'fraud_high_value_new_device'
        }
        rows.append(row)

    # 1.4 Billing/Shipping Mismatch & Cross-Border (n=800)
    # High dispute rate: goods shipped abroad with contested delivery -> Chargeback
    for _ in range(800):
        if np.random.rand() < 0.25:
            amount = float(np.random.choice([10000, 25000, 50000, 75000, 100000]))
        else:
            amount = float(np.random.uniform(5000, 100000))
        merch_avg = 7000.0
        merch_std = 4000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 1.0 if amount > 50000 else 0.0,
            'hour_of_day': np.random.uniform(0.0, 1.0),
            'is_weekend': float(np.random.choice([0, 1], p=[0.6, 0.4])),
            'is_late_night': float(np.random.choice([0, 1], p=[0.6, 0.4])),
            'days_since_last_txn': np.random.uniform(0.1, 0.8),
            'txn_count_1h': np.random.uniform(0.1, 0.5),
            'txn_count_24h': np.random.uniform(0.1, 0.6),
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + 5000),
            'payment_method_risk': 0.35,
            'is_international': 1.0,                           # Cross-border
            'is_first_time_card': 1.0,
            'card_bin_risk': np.random.uniform(0.28, 0.35),
            'customer_account_age_log': math.log(np.random.randint(5, 50) + 1),
            'customer_total_txns_log': math.log(np.random.randint(1, 8) + 1),
            'customer_dispute_rate': np.random.uniform(0.1, 0.4),
            'email_domain_risk': np.random.choice([0.30, 0.90], p=[0.6, 0.4]),
            'phone_verified': 0.0,
            'merchant_fraud_rate_30d': np.random.uniform(0.02, 0.05),
            'merchant_category_risk': 0.40,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(400 + 1),
            'device_fingerprint_new': 1.0,
            'ip_risk_score': np.random.uniform(0.6, 0.9),
            'geo_distance_score': np.random.uniform(0.7, 1.0),
            'billing_shipping_mismatch': 1.0,                  # Definite mismatch
            'label': 1,
            'chargeback_label': 1,                             # High dispute target
            'source': 'fraud_billing_mismatch'
        }
        rows.append(row)

    # 1.5 Chargeback Abuser (Friendly Fraud / First Party Fraud) (n=900)
    # Primary chargeback driver: cardholders who dispute legitimate orders claiming non-receipt
    for _ in range(900):
        if np.random.rand() < 0.3:
            amount = float(np.random.choice([2500, 5000, 10000, 15000, 25000, 50000]))
        else:
            amount = float(np.random.uniform(2000, 80000))
        merch_avg = 6000.0
        merch_std = 3500.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 1.0 if amount > 50000 else 0.0,
            'hour_of_day': np.random.uniform(0.3, 0.9),
            'is_weekend': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'is_late_night': 0.0,
            'days_since_last_txn': np.random.uniform(0.05, 0.3),
            'txn_count_1h': np.random.uniform(0.1, 0.4),
            'txn_count_24h': np.random.uniform(0.1, 0.5),
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + 2000),
            'payment_method_risk': np.random.choice([0.35, 0.20], p=[0.7, 0.3]),
            'is_international': float(np.random.choice([0, 1], p=[0.8, 0.2])),
            'is_first_time_card': 0.0,                         # Uses same card!
            'card_bin_risk': np.random.uniform(0.20, 0.30),
            'customer_account_age_log': math.log(np.random.randint(30, 300) + 1),
            'customer_total_txns_log': math.log(np.random.randint(10, 80) + 1),
            'customer_dispute_rate': np.random.uniform(0.30, 0.85), # Chronic disputer!
            'email_domain_risk': 0.30,                         # Regular gmail
            'phone_verified': 1.0,
            'merchant_fraud_rate_30d': np.random.uniform(0.01, 0.04),
            'merchant_category_risk': 0.35,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(600 + 1),
            'device_fingerprint_new': 0.0,                     # Known device
            'ip_risk_score': np.random.uniform(0.1, 0.4),
            'geo_distance_score': np.random.uniform(0.0, 0.3),
            'billing_shipping_mismatch': 0.0,
            'label': 1,
            'chargeback_label': 1,                             # Definite chargeback target
            'source': 'fraud_chargeback_abuser'
        }
        rows.append(row)

    # 1.6 Abuse Ring (Syndicate Fraud) (n=900)
    for _ in range(900):
        if np.random.rand() < 0.3:
            amount = float(np.random.choice([5000, 10000, 15000, 25000, 50000]))
        else:
            amount = float(np.random.uniform(5000, 50000))
        merch_avg = 5000.0
        merch_std = 3000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 0.0,
            'hour_of_day': np.random.uniform(0.0, 1.0),
            'is_weekend': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'is_late_night': float(np.random.choice([0, 1], p=[0.5, 0.5])),
            'days_since_last_txn': np.random.uniform(0.0, 0.05),
            'txn_count_1h': np.random.uniform(0.4, 0.9),
            'txn_count_24h': np.random.uniform(0.5, 1.0),
            'distinct_merchants_1h': np.random.uniform(0.4, 1.0),
            'amount_sum_24h_log': math.log(np.random.uniform(20000, 150000) + 1),
            'payment_method_risk': np.random.choice([0.35, 0.15], p=[0.6, 0.4]),
            'is_international': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_first_time_card': 1.0,
            'card_bin_risk': np.random.uniform(0.25, 0.35),
            'customer_account_age_log': math.log(np.random.randint(1, 15) + 1),
            'customer_total_txns_log': math.log(np.random.randint(1, 6) + 1),
            'customer_dispute_rate': np.random.uniform(0.15, 0.5),
            'email_domain_risk': np.random.choice([0.30, 0.90], p=[0.3, 0.7]),
            'phone_verified': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'merchant_fraud_rate_30d': np.random.uniform(0.03, 0.09),
            'merchant_category_risk': 0.45,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(200 + 1),
            'device_fingerprint_new': 1.0,                     # Fast cycling devices
            'ip_risk_score': np.random.uniform(0.7, 1.0),      # High proxy score
            'geo_distance_score': np.random.uniform(0.5, 0.95),
            'billing_shipping_mismatch': float(np.random.choice([0, 1], p=[0.4, 0.6])),
            'label': 1,
            'chargeback_label': 0,
            'source': 'fraud_abuse_ring'
        }
        rows.append(row)

    # ─────────────────────────────────────────────────────────────
    # 2. LEGITIMATE PATTERNS (Total = 5000)
    # ─────────────────────────────────────────────────────────────

    # 2.1 Regular Customer (n=1700): Established account, predictable behavior
    for _ in range(1700):
        if np.random.rand() < 0.25:
            amount = float(np.random.choice([500, 1000, 1500, 2000, 2500, 5000, 10000]))
        else:
            amount = float(np.random.uniform(200, 15000))
        merch_avg = 5000.0
        merch_std = 3000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 0.0,
            'hour_of_day': np.random.uniform(0.35, 0.9),      # Day / evening hours
            'is_weekend': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_late_night': 0.0,
            'days_since_last_txn': np.random.uniform(0.02, 0.2),
            'txn_count_1h': np.random.uniform(0.0, 0.2),
            'txn_count_24h': np.random.uniform(0.02, 0.1),
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + np.random.uniform(0, 3000) + 1),
            'payment_method_risk': np.random.choice([0.15, 0.20, 0.35, 0.10], p=[0.5, 0.25, 0.15, 0.1]),
            'is_international': 0.0,
            'is_first_time_card': 0.0,
            'card_bin_risk': np.random.uniform(0.12, 0.22),
            'customer_account_age_log': math.log(np.random.randint(180, 1200) + 1),
            'customer_total_txns_log': math.log(np.random.randint(30, 300) + 1),
            'customer_dispute_rate': np.random.uniform(0.0, 0.02),
            'email_domain_risk': np.random.choice([0.05, 0.30], p=[0.3, 0.7]),
            'phone_verified': 1.0,
            'merchant_fraud_rate_30d': np.random.uniform(0.005, 0.02),
            'merchant_category_risk': np.random.choice([0.08, 0.10, 0.20, 0.25]),
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(np.random.randint(365, 2000) + 1),
            'device_fingerprint_new': float(np.random.choice([0, 1], p=[0.95, 0.05])),
            'ip_risk_score': np.random.uniform(0.0, 0.15),
            'geo_distance_score': np.random.uniform(0.0, 0.15),
            'billing_shipping_mismatch': 0.0,
            'label': 0,
            'chargeback_label': 0,
            'source': 'legit_regular_customer'
        }
        rows.append(row)

    # 2.2 Low-Value Routine (n=1400): Daily groceries, food, small UPI
    for _ in range(1400):
        if np.random.rand() < 0.25:
            amount = float(np.random.choice([500, 1000, 1500, 2000]))
        else:
            amount = float(np.random.uniform(50, 2000))
        merch_avg = 1000.0
        merch_std = 600.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 0.0,
            'hour_of_day': np.random.uniform(0.3, 0.95),
            'is_weekend': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_late_night': 0.0,
            'days_since_last_txn': np.random.uniform(0.01, 0.08),
            'txn_count_1h': np.random.uniform(0.0, 0.1),
            'txn_count_24h': np.random.uniform(0.02, 0.15),
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + np.random.uniform(100, 1500) + 1),
            'payment_method_risk': np.random.choice([0.15, 0.20, 0.10], p=[0.7, 0.2, 0.1]),
            'is_international': 0.0,
            'is_first_time_card': 0.0,
            'card_bin_risk': np.random.uniform(0.12, 0.20),
            'customer_account_age_log': math.log(np.random.randint(90, 800) + 1),
            'customer_total_txns_log': math.log(np.random.randint(20, 250) + 1),
            'customer_dispute_rate': 0.0,
            'email_domain_risk': 0.30,
            'phone_verified': 1.0,
            'merchant_fraud_rate_30d': 0.005,
            'merchant_category_risk': 0.08,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(700 + 1),
            'device_fingerprint_new': float(np.random.choice([0, 1], p=[0.9, 0.1])),
            'ip_risk_score': np.random.uniform(0.0, 0.1),
            'geo_distance_score': np.random.uniform(0.0, 0.1),
            'billing_shipping_mismatch': 0.0,
            'label': 0,
            'chargeback_label': 0,
            'source': 'legit_low_value_routine'
        }
        rows.append(row)

    # 2.3 Verified Repeat (n=1300): Strong authentication, trusted hardware
    for _ in range(1300):
        if np.random.rand() < 0.25:
            amount = float(np.random.choice([500, 1000, 2500, 5000, 10000, 20000]))
        else:
            amount = float(np.random.uniform(500, 30000))
        merch_avg = 6000.0
        merch_std = 3500.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 0.0,
            'hour_of_day': np.random.uniform(0.35, 0.85),
            'is_weekend': float(np.random.choice([0, 1], p=[0.75, 0.25])),
            'is_late_night': 0.0,
            'days_since_last_txn': np.random.uniform(0.03, 0.25),
            'txn_count_1h': np.random.uniform(0.0, 0.2),
            'txn_count_24h': np.random.uniform(0.02, 0.1),
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + 1000),
            'payment_method_risk': np.random.choice([0.15, 0.20, 0.25], p=[0.5, 0.3, 0.2]),
            'is_international': 0.0,
            'is_first_time_card': 0.0,
            'card_bin_risk': np.random.uniform(0.12, 0.20),
            'customer_account_age_log': math.log(np.random.randint(300, 1500) + 1),
            'customer_total_txns_log': math.log(np.random.randint(50, 500) + 1),
            'customer_dispute_rate': 0.0,
            'email_domain_risk': np.random.choice([0.05, 0.30], p=[0.4, 0.6]),
            'phone_verified': 1.0,
            'merchant_fraud_rate_30d': np.random.uniform(0.005, 0.015),
            'merchant_category_risk': 0.20,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(1000 + 1),
            'device_fingerprint_new': 0.0,
            'ip_risk_score': np.random.uniform(0.0, 0.08),
            'geo_distance_score': np.random.uniform(0.0, 0.1),
            'billing_shipping_mismatch': 0.0,
            'label': 0,
            'chargeback_label': 0,
            'source': 'legit_verified_repeat'
        }
        rows.append(row)

    # 2.4 Legitimate High Value in Training Set (n=500)
    # High-ticket legitimate purchases included in training so model learns
    # that high amount != fraud if customer reputation and hardware trust are strong!
    for _ in range(500):
        if np.random.rand() < 0.3:
            amount = float(np.random.choice([60000, 80000, 100000, 150000, 200000, 300000]))
        else:
            amount = float(np.random.uniform(50000, 400000))
        merch_avg = 75000.0
        merch_std = 35000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 1.0,
            'hour_of_day': np.random.uniform(0.35, 0.85),
            'is_weekend': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_late_night': 0.0,
            'days_since_last_txn': np.random.uniform(0.05, 0.4),
            'txn_count_1h': 0.1,
            'txn_count_24h': 0.04,
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + 1),
            'payment_method_risk': np.random.choice([0.35, 0.25, 0.15], p=[0.6, 0.3, 0.1]),
            'is_international': float(np.random.choice([0, 1], p=[0.85, 0.15])),
            'is_first_time_card': 0.0,
            'card_bin_risk': 0.15,
            'customer_account_age_log': math.log(np.random.randint(400, 1800) + 1),
            'customer_total_txns_log': math.log(np.random.randint(80, 700) + 1),
            'customer_dispute_rate': 0.0,
            'email_domain_risk': np.random.choice([0.05, 0.30], p=[0.5, 0.5]),
            'phone_verified': 1.0,
            'merchant_fraud_rate_30d': 0.008,
            'merchant_category_risk': 0.35,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(1200 + 1),
            'device_fingerprint_new': float(np.random.choice([0, 1], p=[0.85, 0.15])),
            'ip_risk_score': np.random.uniform(0.01, 0.12),
            'geo_distance_score': np.random.uniform(0.0, 0.15),
            'billing_shipping_mismatch': 0.0,
            'label': 0,
            'chargeback_label': 0,
            'source': 'legit_high_value_train'
        }
        rows.append(row)

    # 2.5 Legitimate High Value — KILL-SWITCH EVALUATION HOLDOUT (n=100)
    # Strictly held out! NEVER included in training matrix X_train or X_test!
    for _ in range(100):
        if np.random.rand() < 0.3:
            amount = float(np.random.choice([60000, 80000, 100000, 150000, 200000, 500000]))
        else:
            amount = float(np.random.uniform(55000, 500000))
        merch_avg = 80000.0
        merch_std = 40000.0
        row = {
            'amount_log': math.log(amount + 1),
            'amount_zscore': (amount - merch_avg) / merch_std,
            'is_round_amount': check_round_amount(amount),
            'amount_to_avg_ratio': amount / merch_avg,
            'is_high_value': 1.0,
            'hour_of_day': np.random.uniform(0.4, 0.8),
            'is_weekend': float(np.random.choice([0, 1], p=[0.7, 0.3])),
            'is_late_night': 0.0,
            'days_since_last_txn': np.random.uniform(0.1, 0.5),
            'txn_count_1h': 0.1,                               # 1 transaction
            'txn_count_24h': 0.04,
            'distinct_merchants_1h': 0.2,
            'amount_sum_24h_log': math.log(amount + 1),
            'payment_method_risk': np.random.choice([0.35, 0.25], p=[0.7, 0.3]),
            'is_international': float(np.random.choice([0, 1], p=[0.9, 0.1])),
            'is_first_time_card': 0.0,
            'card_bin_risk': 0.15,
            'customer_account_age_log': math.log(np.random.randint(500, 2000) + 1),
            'customer_total_txns_log': math.log(np.random.randint(100, 800) + 1),
            'customer_dispute_rate': 0.0,
            'email_domain_risk': np.random.choice([0.05, 0.30], p=[0.5, 0.5]),
            'phone_verified': 1.0,
            'merchant_fraud_rate_30d': 0.008,
            'merchant_category_risk': 0.35,
            'merchant_avg_txn_log': math.log(merch_avg + 1),
            'merchant_vintage_log': math.log(1500 + 1),
            'device_fingerprint_new': float(np.random.choice([0, 1], p=[0.9, 0.1])),
            'ip_risk_score': 0.02,
            'geo_distance_score': np.random.uniform(0.0, 0.1),
            'billing_shipping_mismatch': 0.0,
            'label': 0,
            'chargeback_label': 0,
            'source': 'legit_high_value'
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    # Reorder columns strictly to ALL_FEATURE_NAMES + ['label', 'chargeback_label', 'source']
    columns_order = ALL_FEATURE_NAMES + ['label', 'chargeback_label', 'source']
    df = df[columns_order]
    return df


def produce_canonical_artifact():
    print("=" * 60)
    print("  SENTINEL Data Shim v1.0 - Canonical Training Artifact Builder")
    print("=" * 60)
    
    df = generate_canonical_dataset()
    print(f"[1/3] Generated dataset: {len(df)} total transactions")
    print(f"      Fraudulent (label=1): {(df['label'] == 1).sum()}")
    print(f"      Legitimate (label=0): {(df['label'] == 0).sum()}")
    print(f"      Chargeback Positive (chargeback_label=1): {(df['chargeback_label'] == 1).sum()}")
    print(f"      Kill-switch corpus (legit_high_value): {(df['source'] == 'legit_high_value').sum()}")
    
    output_path = os.path.join(os.path.dirname(__file__), "training_v3.parquet")
    print(f"[2/3] Writing canonical artifact to {output_path}...")
    df.to_parquet(output_path, index=False)
    print(f"[3/3] Done! Artifact ready for model training.")
    print("=" * 60)


if __name__ == "__main__":
    produce_canonical_artifact()
