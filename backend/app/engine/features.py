"""SENTINEL Engine - Feature Engineering

Extracts a 30-dimension fraud risk vector from a transaction payload.
Each feature is normalized to a usable range for ML models.
"""
import math
import hashlib
import re
from typing import Optional


# ─── FEATURE SCHEMA (EXACTLY 30 FEATURES, ORDER MATTERS) ───
# The ML models are trained on features in THIS EXACT ORDER.
# DO NOT reorder, add, or remove features without retraining.

TRANSACTION_FEATURES = [
    'amount_log',              # log(amount + 1)
    'amount_zscore',           # (amount - merchant_avg) / merchant_std
    'is_round_amount',         # 1 if amount is round number (1000, 5000, etc.)
    'amount_to_avg_ratio',     # amount / merchant_avg_amount
    'is_high_value',           # 1 if amount > 50000 INR
]

TEMPORAL_FEATURES = [
    'hour_of_day',             # 0-23, normalized to 0-1
    'is_weekend',              # 0 or 1
    'is_late_night',           # 1 if between 1am-5am
    'days_since_last_txn',     # 0 if first transaction, normalized
]

VELOCITY_FEATURES = [
    'txn_count_1h',            # count of txns from same customer in 1 hour
    'txn_count_24h',           # same, 24 hours
    'distinct_merchants_1h',   # unique merchants in 1 hour
    'amount_sum_24h_log',      # log(sum of amounts in 24h + 1)
]

PAYMENT_FEATURES = [
    'payment_method_risk',     # risk score by method type
    'is_international',        # 0 or 1
    'is_first_time_card',      # 0 or 1
    'card_bin_risk',           # risk score based on BIN prefix
]

CUSTOMER_FEATURES = [
    'customer_account_age_log',  # log(account_age_days + 1)
    'customer_total_txns_log',   # log(total_txns + 1)
    'customer_dispute_rate',     # historical dispute rate 0-1
    'email_domain_risk',         # free=0.3, corporate=0.05, disposable=0.9
    'phone_verified',            # 0 or 1
]

MERCHANT_FEATURES = [
    'merchant_fraud_rate_30d',   # merchant's recent fraud rate 0-1
    'merchant_category_risk',    # risk score by category
    'merchant_avg_txn_log',      # log(merchant avg txn + 1) for context
    'merchant_vintage_log',      # log(merchant_age_days + 1)
]

DEVICE_FEATURES = [
    'device_fingerprint_new',    # 0 or 1, never-seen device
    'ip_risk_score',             # proxy/VPN detection 0-1
    'geo_distance_score',        # 0-1, normalized geo distance
    'billing_shipping_mismatch', # 0 or 1
]

ALL_FEATURE_NAMES = (
    TRANSACTION_FEATURES +
    TEMPORAL_FEATURES +
    VELOCITY_FEATURES +
    PAYMENT_FEATURES +
    CUSTOMER_FEATURES +
    MERCHANT_FEATURES +
    DEVICE_FEATURES
)

assert len(ALL_FEATURE_NAMES) == 30, f"Expected 30 features, got {len(ALL_FEATURE_NAMES)}"


def get_feature_fingerprint() -> str:
    """Generate a SHA-256 hash of the exact feature schema."""
    schema_str = ",".join(ALL_FEATURE_NAMES)
    return hashlib.sha256(schema_str.encode('utf-8')).hexdigest()


# ─── Risk Lookup Tables ───

PAYMENT_METHOD_RISK = {
    'credit_card': 0.35,
    'debit_card': 0.20,
    'upi': 0.15,
    'net_banking': 0.25,
    'wallet': 0.10,
}

MERCHANT_CATEGORY_RISK = {
    'electronics': 0.45,
    'gaming': 0.40,
    'travel': 0.35,
    'fashion': 0.25,
    'services': 0.20,
    'food': 0.10,
    'groceries': 0.08,
    'other': 0.20,
}

# Common free email domains (higher fraud risk)
FREE_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'rediffmail.com', 'ymail.com', 'aol.com', 'protonmail.com',
}

# Known disposable email domains (very high fraud risk)
DISPOSABLE_EMAIL_DOMAINS = {
    'tempmail.com', 'guerrillamail.com', 'mailinator.com',
    'throwaway.email', 'temp-mail.org', 'sharklasers.com',
    'yopmail.com', 'trashmail.com',
}


# ─── Feature Extraction Functions ───

def extract_transaction_features(amount: float, merchant_avg: float = 5000.0,
                                  merchant_std: float = 3000.0) -> dict:
    """Extract transaction amount features."""
    features = {}
    features['amount_log'] = math.log(amount + 1)
    features['amount_zscore'] = (amount - merchant_avg) / max(merchant_std, 1.0)
    # Round amount check: divisible by 500 or 1000
    features['is_round_amount'] = 1.0 if (amount % 500 == 0 and amount >= 500) else 0.0
    features['amount_to_avg_ratio'] = amount / max(merchant_avg, 1.0)
    features['is_high_value'] = 1.0 if amount > 50000 else 0.0
    return features


def extract_temporal_features(hour: int = 12, is_weekend: bool = False,
                               days_since_last: float = 30.0) -> dict:
    """Extract time-based features."""
    features = {}
    features['hour_of_day'] = hour / 23.0  # Normalize to 0-1
    features['is_weekend'] = 1.0 if is_weekend else 0.0
    features['is_late_night'] = 1.0 if (1 <= hour <= 5) else 0.0
    features['days_since_last_txn'] = min(days_since_last / 365.0, 1.0)  # Normalize, cap at 1
    return features


def extract_velocity_features(txn_count_1h: int = 0, txn_count_24h: int = 1,
                                distinct_merchants_1h: int = 1,
                                amount_sum_24h: float = 0.0) -> dict:
    """Extract transaction velocity features."""
    features = {}
    features['txn_count_1h'] = min(txn_count_1h / 10.0, 1.0)  # Normalize, cap at 10
    features['txn_count_24h'] = min(txn_count_24h / 50.0, 1.0)
    features['distinct_merchants_1h'] = min(distinct_merchants_1h / 5.0, 1.0)
    features['amount_sum_24h_log'] = math.log(amount_sum_24h + 1)
    return features


def extract_payment_features(payment_method: str = "credit_card",
                              is_international: bool = False,
                              is_first_time_card: bool = False,
                              card_bin: str = None) -> dict:
    """Extract payment method features."""
    features = {}
    # If payment_method is Enum or string
    method_str = getattr(payment_method, "value", str(payment_method)).lower()
    features['payment_method_risk'] = PAYMENT_METHOD_RISK.get(method_str, 0.20)
    features['is_international'] = 1.0 if is_international else 0.0
    features['is_first_time_card'] = 1.0 if is_first_time_card else 0.0
    # Card BIN risk: simulate based on first digit
    if card_bin and len(str(card_bin)) >= 1:
        first_digit = str(card_bin)[0]
        # 4 = Visa (medium), 5 = Mastercard (medium), 6 = RuPay (low), 3 = Amex (higher)
        bin_risk = {'3': 0.35, '4': 0.20, '5': 0.22, '6': 0.12}.get(first_digit, 0.25)
    else:
        bin_risk = 0.20
    features['card_bin_risk'] = bin_risk
    return features


def extract_customer_features(account_age_days: int = 365,
                                total_txns: int = 50,
                                dispute_rate: float = 0.0,
                                email: str = None,
                                phone_verified: bool = True) -> dict:
    """Extract customer profile features."""
    features = {}
    features['customer_account_age_log'] = math.log(account_age_days + 1)
    features['customer_total_txns_log'] = math.log(total_txns + 1)
    features['customer_dispute_rate'] = min(dispute_rate, 1.0)

    # Email domain risk
    if email:
        domain = email.split('@')[-1].lower() if '@' in email else ''
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            features['email_domain_risk'] = 0.90
        elif domain in FREE_EMAIL_DOMAINS:
            features['email_domain_risk'] = 0.30
        else:
            features['email_domain_risk'] = 0.05  # Corporate email
    else:
        features['email_domain_risk'] = 0.50  # No email provided

    features['phone_verified'] = 1.0 if phone_verified else 0.0
    return features


def extract_merchant_features(fraud_rate_30d: float = 0.01,
                                category: str = "other",
                                avg_txn: float = 5000.0,
                                vintage_days: int = 365) -> dict:
    """Extract merchant profile features."""
    features = {}
    features['merchant_fraud_rate_30d'] = min(fraud_rate_30d, 1.0)
    features['merchant_category_risk'] = MERCHANT_CATEGORY_RISK.get(category, 0.20)
    features['merchant_avg_txn_log'] = math.log(avg_txn + 1)
    features['merchant_vintage_log'] = math.log(vintage_days + 1)
    return features


def extract_device_features(device_new: bool = False,
                              ip_risk: float = 0.0,
                              geo_distance_km: float = 0.0,
                              billing_shipping_mismatch: bool = False) -> dict:
    """Extract device and network features."""
    features = {}
    features['device_fingerprint_new'] = 1.0 if device_new else 0.0
    features['ip_risk_score'] = min(ip_risk, 1.0)
    # Normalize geo distance: 0km = 0, 5000km+ = 1
    features['geo_distance_score'] = min(geo_distance_km / 5000.0, 1.0)
    features['billing_shipping_mismatch'] = 1.0 if billing_shipping_mismatch else 0.0
    return features


def extract_all_features(transaction_data: dict) -> dict:
    """
    Master function: Extract the full 30-dimension fraud feature vector.

    transaction_data is a dict with keys matching TransactionRequest fields
    plus optional enrichment fields (velocity, customer history, merchant profile).
    """
    amount = float(transaction_data.get('amount', 0.0))
    merchant_avg = float(transaction_data.get('merchant_avg_txn', 5000.0))
    merchant_std = float(transaction_data.get('merchant_std_txn', 3000.0))

    all_features = {}

    # Transaction features (5)
    all_features.update(extract_transaction_features(amount, merchant_avg, merchant_std))

    # Temporal features (4)
    all_features.update(extract_temporal_features(
        hour=int(transaction_data.get('hour_of_day', 12)),
        is_weekend=bool(transaction_data.get('is_weekend', False)),
        days_since_last=float(transaction_data.get('days_since_last_txn', 30.0)),
    ))

    # Velocity features (4)
    all_features.update(extract_velocity_features(
        txn_count_1h=int(transaction_data.get('txn_count_1h', 0)),
        txn_count_24h=int(transaction_data.get('txn_count_24h', 1)),
        distinct_merchants_1h=int(transaction_data.get('distinct_merchants_1h', 1)),
        amount_sum_24h=float(transaction_data.get('amount_sum_24h', 0.0)),
    ))

    # Payment features (4)
    all_features.update(extract_payment_features(
        payment_method=transaction_data.get('payment_method', 'credit_card'),
        is_international=bool(transaction_data.get('is_international', False)),
        is_first_time_card=bool(transaction_data.get('is_first_time_card', False)),
        card_bin=transaction_data.get('card_bin'),
    ))

    # Customer features (5)
    all_features.update(extract_customer_features(
        account_age_days=int(transaction_data.get('customer_account_age_days', 365)),
        total_txns=int(transaction_data.get('customer_total_txns', 50)),
        dispute_rate=float(transaction_data.get('customer_dispute_rate', 0.0)),
        email=transaction_data.get('customer_email'),
        phone_verified=bool(transaction_data.get('phone_verified', True)),
    ))

    # Merchant features (4)
    all_features.update(extract_merchant_features(
        fraud_rate_30d=float(transaction_data.get('merchant_fraud_rate_30d', 0.01)),
        category=transaction_data.get('merchant_category', 'other') or 'other',
        avg_txn=merchant_avg,
        vintage_days=int(transaction_data.get('merchant_vintage_days', 365)),
    ))

    # Device features (4)
    all_features.update(extract_device_features(
        device_new=bool(transaction_data.get('device_fingerprint_new', False)),
        ip_risk=float(transaction_data.get('ip_risk_score', 0.0)),
        geo_distance_km=float(transaction_data.get('geo_distance_km', 0.0)),
        billing_shipping_mismatch=bool(transaction_data.get('billing_shipping_mismatch', False)),
    ))

    return all_features
