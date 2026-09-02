"""SENTINEL Engine - Layer 5: Policy & Decision Engine

Applies deterministic business rules, fraud taxonomy classification,
severity thresholds, and final enforcement action (ALLOW, REVIEW, BLOCK).
"""
from typing import Dict, Any, List
from app.api.schemas import RiskLevel, FraudType, Action


class FraudPolicyEngine:
    """
    Evaluates ML inference outputs alongside behavioral signals to assign
    standardized BFSI fraud classifications and actionable merchant decisions.
    """

    def __init__(self):
        self.policy_version = "1.0.0"

    def determine_fraud_type(self, features: Dict[str, Any], fraud_score: float,
                             chargeback_score: float, overrides: List[dict]) -> FraudType:
        """Categorize threat into standard BFSI taxonomy."""
        # Overrides take precedence
        override_ids = {ovr.get('id') for ovr in overrides}

        if "RULE_CARD_TESTING" in override_ids or (features.get('amount_log', 0) < 4.6 and features.get('txn_count_1h', 0) >= 0.3):
            return FraudType.CARD_TESTING

        if "RULE_ATO_PATTERN" in override_ids or (features.get('device_fingerprint_new', 0) == 1 and features.get('is_high_value', 0) == 1 and features.get('is_late_night', 0) == 1):
            return FraudType.ACCOUNT_TAKEOVER

        if "RULE_ABUSE_RING" in override_ids or (features.get('device_fingerprint_new', 0) == 1 and features.get('ip_risk_score', 0) >= 0.7 and features.get('txn_count_24h', 0) >= 0.3):
            return FraudType.ABUSE_RING

        if "RULE_CHRONIC_DISPUTER" in override_ids or features.get('customer_dispute_rate', 0) >= 0.30:
            return FraudType.CHARGEBACK_ABUSE

        if features.get('email_domain_risk', 0) >= 0.85 and features.get('phone_verified', 1) == 0:
            return FraudType.SYNTHETIC_IDENTITY

        if features.get('billing_shipping_mismatch', 0) == 1 and features.get('is_international', 0) == 1:
            return FraudType.CARD_FRAUD

        if chargeback_score >= 65.0:
            return FraudType.FRIENDLY_FRAUD

        if fraud_score >= 60.0:
            return FraudType.CARD_FRAUD

        if max(fraud_score, chargeback_score) < 30.0:
            return FraudType.NONE

        return FraudType.UNKNOWN

    def assess(self, features: Dict[str, Any], fraud_score: float,
               chargeback_score: float, overrides: List[dict] = None) -> Dict[str, Any]:
        """
        Produce finalized assessment with risk level, fraud classification,
        and recommended enforcement action.
        """
        overrides = overrides or []
        max_score = max(fraud_score, chargeback_score)

        # 1. Severity assignment
        if max_score >= 80.0:
            risk_level = RiskLevel.CRITICAL
        elif max_score >= 60.0:
            risk_level = RiskLevel.HIGH
        elif max_score >= 30.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # 2. Recommended Action
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommended_action = Action.BLOCK
        elif risk_level == RiskLevel.MEDIUM:
            recommended_action = Action.REVIEW
        else:
            recommended_action = Action.ALLOW

        # 3. Fraud Type Classification
        fraud_type = self.determine_fraud_type(features, fraud_score, chargeback_score, overrides)

        # 4. Confidence Banding
        if overrides:
            confidence_band = "HIGH_CONFIDENCE (POLICY_OVERRIDE)"
        elif abs(fraud_score - chargeback_score) > 40.0:
            confidence_band = "MIXED_SIGNALS"
        elif max_score >= 70.0 or max_score <= 20.0:
            confidence_band = "HIGH_CONFIDENCE"
        else:
            confidence_band = "MODERATE_CONFIDENCE"

        return {
            "fraud_score": round(fraud_score, 2),
            "chargeback_score": round(chargeback_score, 2),
            "risk_level": risk_level,
            "fraud_type": fraud_type,
            "is_fraudulent": (max_score >= 50.0),
            "recommended_action": recommended_action,
            "confidence_band": confidence_band,
            "policy_version": self.policy_version,
        }


policy_engine = FraudPolicyEngine()
