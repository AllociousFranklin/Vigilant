"""SENTINEL Engine - Layer 6: Explainability & Chargeback Evidence Builder

Translates low-level feature signals and ML predictions into causally-linked,
human-readable fraud evidence.
Generates complete formal chargeback dispute response packages.
"""
from typing import Dict, Any, List
from app.api.schemas import ReasonDetail


FEATURE_REASON_MAP = {
    'txn_count_1h': {
        'threshold': 0.25,
        'reason': 'Abnormal velocity: elevated transaction attempts within past 1 hour',
        'category': 'Velocity',
    },
    'txn_count_24h': {
        'threshold': 0.35,
        'reason': 'Sustained high transaction count over 24-hour window',
        'category': 'Velocity',
    },
    'amount_zscore': {
        'threshold': 2.0,
        'reason': 'Transaction value deviates significantly from merchant baseline',
        'category': 'Transaction',
    },
    'is_high_value': {
        'threshold': 0.5,
        'reason': 'High-ticket transaction exceeding INR 50,000 threshold',
        'category': 'Transaction',
    },
    'is_late_night': {
        'threshold': 0.5,
        'reason': 'Transaction executed during overnight window (1:00 AM - 5:00 AM)',
        'category': 'Temporal',
    },
    'is_first_time_card': {
        'threshold': 0.5,
        'reason': 'Payment instrument used for the first time on merchant account',
        'category': 'Payment Instrument',
    },
    'is_international': {
        'threshold': 0.5,
        'reason': 'Cross-border international payment routing',
        'category': 'Payment Instrument',
    },
    'card_bin_risk': {
        'threshold': 0.30,
        'reason': 'Card BIN prefix associated with elevated issuer dispute frequency',
        'category': 'Payment Instrument',
    },
    'customer_dispute_rate': {
        'threshold': 0.08,
        'reason': 'Cardholder identity carries documented history of prior disputes/chargebacks',
        'category': 'Customer Risk',
    },
    'email_domain_risk': {
        'threshold': 0.50,
        'reason': 'Customer email registered on disposable or high-risk domain',
        'category': 'Customer Risk',
    },
    'phone_verified': {
        'threshold': 0.5,
        'reason': 'Customer mobile number lacks two-factor phone verification',
        'category': 'Customer Risk',
        'inverse': True,
    },
    'device_fingerprint_new': {
        'threshold': 0.5,
        'reason': 'Access originating from newly observed hardware fingerprint',
        'category': 'Device Intelligence',
    },
    'ip_risk_score': {
        'threshold': 0.40,
        'reason': 'IP traffic routed via commercial VPN, datacenter proxy, or Tor exit',
        'category': 'Network Intelligence',
    },
    'geo_distance_score': {
        'threshold': 0.40,
        'reason': 'Geographic anomaly between IP geolocation and billing domicile',
        'category': 'Network Intelligence',
    },
    'billing_shipping_mismatch': {
        'threshold': 0.5,
        'reason': 'Billing jurisdiction diverges from physical delivery destination',
        'category': 'Identity Verification',
    },
}


def get_signal_strength(measured_val: float, threshold: float, is_inverse: bool = False) -> str:
    """Determine signal strength: STRONG, MODERATE, or WEAK."""
    if is_inverse:
        intensity = (1.0 - measured_val) / max(1.0 - threshold, 0.1)
    else:
        intensity = measured_val / max(threshold, 0.01)

    if intensity >= 2.0:
        return "STRONG"
    elif intensity >= 1.2:
        return "MODERATE"
    else:
        return "WEAK"


def generate_explanations(features: dict, assessment_context: dict) -> List[ReasonDetail]:
    """
    Generate prioritized, human-readable evidence points from triggered signals.
    """
    reasons = []

    # Priority 1: System Policy Overrides
    overrides = assessment_context.get('overrides') or []
    for ovr in overrides:
        reasons.append(ReasonDetail(
            reason=f"[POLICY OVERRIDE] {ovr['reason']}",
            signal_strength="STRONG",
            category=ovr.get('category', 'System Policy'),
            feature_name=ovr.get('id'),
        ))

    # Priority 2: Feature-driven explanations
    for feat_name, mapping in FEATURE_REASON_MAP.items():
        val = float(features.get(feat_name, 0.0))
        threshold = mapping['threshold']
        is_inverse = mapping.get('inverse', False)

        triggered = (val < threshold) if is_inverse else (val > threshold)

        if triggered:
            strength = get_signal_strength(val, threshold, is_inverse)
            reasons.append(ReasonDetail(
                reason=mapping['reason'],
                signal_strength=strength,
                category=mapping['category'],
                feature_name=feat_name,
            ))

    # Sort so STRONG signals appear first
    strength_order = {"STRONG": 3, "MODERATE": 2, "WEAK": 1}
    reasons.sort(key=lambda r: strength_order.get(r.signal_strength, 0), reverse=True)

    if not reasons and assessment_context.get('fraud_score', 0) > 40:
        reasons.append(ReasonDetail(
            reason="Aggregated low-level behavioral signals indicate elevated anomaly risk",
            signal_strength="MODERATE",
            category="Combined Heuristics",
            feature_name="ensemble_anomaly"
        ))

    return reasons[:8]


def generate_chargeback_evidence(assessment_data: dict, reasons: List[ReasonDetail]) -> str:
    """
    Generate an authoritative Chargeback Dispute Evidence document
    formatted for submission to payment gateways (Razorpay/Visa/Mastercard/NPCI).
    """
    txn_id = assessment_data.get('transaction_id', 'N/A')
    merchant_id = assessment_data.get('merchant_id', 'N/A')
    amount = assessment_data.get('amount', 0.0)
    currency = assessment_data.get('currency', 'INR')
    timestamp = assessment_data.get('timestamp', 'N/A')
    fraud_score = assessment_data.get('fraud_score', 0.0)
    chargeback_score = assessment_data.get('chargeback_score', 0.0)
    fraud_type = assessment_data.get('fraud_type', 'UNKNOWN')
    risk_level = assessment_data.get('risk_level', 'HIGH')

    evidence_lines = []
    for r in reasons:
        evidence_lines.append(f"  • [{r.signal_strength}] ({r.category}) {r.reason}")

    evidence_list_str = "\n".join(evidence_lines) if evidence_lines else "  • No distinct anomalies recorded."

    dispute_document = f"""================================================================================
                    SENTINEL CHARGEBACK EVIDENCE DOSSIER
================================================================================
CASE REFERENCE        : DISPUTE-{txn_id}
MERCHANT ID           : {merchant_id}
TRANSACTION AMOUNT    : {currency} {amount:,.2f}
ASSESSMENT TIMESTAMP  : {timestamp}
FRAUD CLASSIFICATION  : {fraud_type}
ASSESSED RISK LEVEL   : {risk_level} (Fraud: {fraud_score}/100, Chargeback Propensity: {chargeback_score}/100)

--------------------------------------------------------------------------------
1. FORENSIC EVIDENCE & TELEMETRY SIGNALS:
--------------------------------------------------------------------------------
{evidence_list_str}

--------------------------------------------------------------------------------
2. MERCHANT DEFENSE & REPRESENTMENT STATEMENT:
--------------------------------------------------------------------------------
The merchant respectfully submits that the cardholder/account authorization for 
transaction {txn_id} was monitored by the SENTINEL Real-Time AI Risk Engine.

At the time of purchase, multi-dimensional risk scoring verified telemetry across 
device identity, IP reputation, velocity thresholds, and order fulfillment parameters.
The automated decisioning recorded a risk assessment of {risk_level}. 

Based on the forensic logs preserved above, the merchant requests that this dispute 
be resolved in favor of the merchant in accordance with card network operating 
regulations and BFSI chargeback representment guidelines.
================================================================================
"""
    return dispute_document.strip()
