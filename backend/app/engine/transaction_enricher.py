"""SENTINEL Engine - Layer 2: Transaction Enrichment

Enriches ingested transactions with merchant context, customer profile,
velocity statistics, device intelligence, and geo-location signals.
"""
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from app.engine.ingestion import IngestedTransaction


@dataclass
class EnrichedTransaction:
    """Enriched transaction carrying historical, velocity, and network signals."""
    # Base transaction fields
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    payment_method: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_id: Optional[str]
    device_fingerprint: Optional[str]
    ip_address: Optional[str]
    billing_country: str
    shipping_country: Optional[str]
    card_bin: Optional[str]
    is_international: bool
    merchant_category: str
    metadata: dict

    # Merchant profile enrichment
    merchant_avg_txn: float
    merchant_std_txn: float
    merchant_fraud_rate_30d: float
    merchant_vintage_days: int

    # Customer profile enrichment
    customer_account_age_days: int
    customer_total_txns: int
    customer_dispute_rate: float
    phone_verified: bool

    # Device & Network enrichment
    device_fingerprint_new: bool
    ip_risk_score: float
    geo_distance_km: float
    billing_shipping_mismatch: bool

    # Velocity & Temporal enrichment
    txn_count_1h: int
    txn_count_24h: int
    distinct_merchants_1h: int
    amount_sum_24h: float
    hour_of_day: int
    is_weekend: bool
    days_since_last_txn: float
    is_first_time_card: bool

    # Raw signals dict
    signals: dict = field(default_factory=dict)


def _hash_seed(value: str) -> int:
    """Generate a deterministic integer seed from string hash."""
    return int(hashlib.md5(value.encode('utf-8', errors='ignore')).hexdigest()[:8], 16)


def enrich(ingested: IngestedTransaction) -> EnrichedTransaction:
    """
    Enrich ingested transaction with deterministic profile signals and metadata overrides.
    """
    meta = ingested.metadata or {}
    now = datetime.now(timezone.utc)

    # 1. Merchant profile
    merch_seed = _hash_seed(ingested.merchant_id)
    default_avg = 3000.0 + (merch_seed % 7000)
    merchant_avg = float(meta.get('merchant_avg_txn', default_avg))
    merchant_std = float(meta.get('merchant_std_txn', merchant_avg * 0.5))
    merchant_fraud_rate = float(meta.get('merchant_fraud_rate_30d', 0.005 + ((merch_seed % 15) / 1000.0)))
    merchant_vintage = int(meta.get('merchant_vintage_days', 300 + (merch_seed % 1000)))

    category = ingested.merchant_category or meta.get('merchant_category', 'other')

    # 2. Customer profile
    cust_key = ingested.customer_id or ingested.customer_email or ingested.customer_phone or "guest"
    cust_seed = _hash_seed(cust_key)
    cust_age = int(meta.get('customer_account_age_days', 60 + (cust_seed % 800)))
    cust_txns = int(meta.get('customer_total_txns', 5 + (cust_seed % 150)))
    cust_dispute = float(meta.get('customer_dispute_rate', 0.0))
    phone_ver = bool(meta.get('phone_verified', ingested.customer_phone is not None))

    # 3. Device & Network
    device_new = bool(meta.get('device_fingerprint_new', ingested.device_fingerprint is None or "new" in str(ingested.device_fingerprint).lower()))
    
    # Check disposable email
    email_risk = 0.0
    if ingested.customer_email:
        domain = ingested.customer_email.split('@')[-1].lower() if '@' in ingested.customer_email else ''
        if any(d in domain for d in ['tempmail', 'mailinator', 'guerrillamail', 'throwaway', 'sharklasers', 'trashmail', 'yopmail']):
            email_risk = 0.90

    ip_risk = float(meta.get('ip_risk_score', email_risk))
    
    # Billing/shipping mismatch
    b_mismatch = bool(meta.get('billing_shipping_mismatch', False))
    if ingested.billing_country and ingested.shipping_country:
        if ingested.billing_country.upper() != ingested.shipping_country.upper():
            b_mismatch = True

    geo_dist = float(meta.get('geo_distance_km', 2500.0 if b_mismatch else 5.0))

    # 4. Velocity
    v_count_1h = int(meta.get('txn_count_1h', 0))
    v_count_24h = int(meta.get('txn_count_24h', max(v_count_1h, 1)))
    v_merchants = int(meta.get('distinct_merchants_1h', 1))
    v_sum_24h = float(meta.get('amount_sum_24h', ingested.amount * max(v_count_1h, 1)))

    hour = int(meta.get('hour_of_day', now.hour))
    is_wknd = bool(meta.get('is_weekend', now.weekday() >= 5))
    days_since = float(meta.get('days_since_last_txn', 14.0))
    first_card = bool(meta.get('is_first_time_card', device_new))

    signals = {
        'merchant_avg': merchant_avg,
        'customer_age_days': cust_age,
        'velocity_1h': v_count_1h,
        'velocity_24h': v_count_24h,
        'ip_risk': ip_risk,
        'billing_mismatch': b_mismatch,
    }

    return EnrichedTransaction(
        transaction_id=ingested.transaction_id,
        merchant_id=ingested.merchant_id,
        amount=ingested.amount,
        currency=ingested.currency,
        payment_method=ingested.payment_method,
        customer_email=ingested.customer_email,
        customer_phone=ingested.customer_phone,
        customer_id=ingested.customer_id,
        device_fingerprint=ingested.device_fingerprint,
        ip_address=ingested.ip_address,
        billing_country=ingested.billing_country,
        shipping_country=ingested.shipping_country,
        card_bin=ingested.card_bin,
        is_international=ingested.is_international,
        merchant_category=category,
        metadata=meta,
        merchant_avg_txn=merchant_avg,
        merchant_std_txn=merchant_std,
        merchant_fraud_rate_30d=merchant_fraud_rate,
        merchant_vintage_days=merchant_vintage,
        customer_account_age_days=cust_age,
        customer_total_txns=cust_txns,
        customer_dispute_rate=cust_dispute,
        phone_verified=phone_ver,
        device_fingerprint_new=device_new,
        ip_risk_score=ip_risk,
        geo_distance_km=geo_dist,
        billing_shipping_mismatch=b_mismatch,
        txn_count_1h=v_count_1h,
        txn_count_24h=v_count_24h,
        distinct_merchants_1h=v_merchants,
        amount_sum_24h=v_sum_24h,
        hour_of_day=hour,
        is_weekend=is_wknd,
        days_since_last_txn=days_since,
        is_first_time_card=first_card,
        signals=signals,
    )
