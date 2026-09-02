"""SENTINEL Engine - Layer 4: Fraud & Chargeback Scoring Engine

Ensemble inference core for real-time risk scoring.
Stateless, horizontally scalable, designed for sub-10ms response.
"""
import os
import json
import numpy as np
import joblib
from typing import Optional, Tuple, List, Dict, Any
from app.core.config import settings
from app.engine.features import ALL_FEATURE_NAMES, get_feature_fingerprint
from app.services.fraud_intel import check_card_bin, check_device


class FraudScoringEngine:
    """
    Layer 4: Ensemble scoring engine.
    - Model A: Transaction Fraud Classifier (XGBoost)
    - Model B: Chargeback & Dispute Propensity Classifier (Random Forest)
    - Non-negotiable deterministic security overrides (Policy Floors)
    - Real-time BIN & Device Threat Intelligence
    """

    def __init__(self):
        self.fraud_model = None
        self.chargeback_model = None
        self.fraud_model_version = "none"
        self.chargeback_model_version = "none"
        self._loaded = False

    def load_models(self):
        """Load pre-trained models and verify schema integrity."""
        current_fingerprint = get_feature_fingerprint()

        # 1. Fraud model (XGBoost)
        fraud_path = settings.FRAUD_MODEL_PATH
        fraud_meta_path = fraud_path.replace('.joblib', '_meta.json')
        if os.path.exists(fraud_path):
            if os.path.exists(fraud_meta_path):
                with open(fraud_meta_path, 'r') as f:
                    meta = json.load(f)
                    if meta.get("schema_hash") and meta["schema_hash"] != current_fingerprint:
                        raise RuntimeError(
                            f"Fraud Model schema mismatch! Expected {current_fingerprint}, "
                            f"got {meta['schema_hash']}. Please retrain."
                        )
            self.fraud_model = joblib.load(fraud_path)
            self.fraud_model_version = "v1.0-xgb"
        else:
            print(f"[WARN] Fraud model not found at {fraud_path} — heuristic fallback active")

        # 2. Chargeback model (Random Forest)
        cb_path = settings.CHARGEBACK_MODEL_PATH
        cb_meta_path = cb_path.replace('.joblib', '_meta.json')
        if os.path.exists(cb_path):
            if os.path.exists(cb_meta_path):
                with open(cb_meta_path, 'r') as f:
                    meta = json.load(f)
                    if meta.get("schema_hash") and meta["schema_hash"] != current_fingerprint:
                        raise RuntimeError(
                            f"Chargeback Model schema mismatch! Expected {current_fingerprint}, "
                            f"got {meta['schema_hash']}. Please retrain."
                        )
            self.chargeback_model = joblib.load(cb_path)
            self.chargeback_model_version = "v1.0-rf"
        else:
            print(f"[WARN] Chargeback model not found at {cb_path} — heuristic fallback active")

        self._loaded = True

    def _get_model_input(self, features: dict) -> np.ndarray:
        """Build strict feature vector aligned to ALL_FEATURE_NAMES."""
        vec = [float(features.get(name, 0.0)) for name in ALL_FEATURE_NAMES]
        return np.array([vec])

    def _heuristic_fraud_score(self, features: dict) -> float:
        """Fallback heuristic when ML model is unavailable."""
        score = 0.0
        if features.get('txn_count_1h', 0) > 0.4:
            score += 35.0
        if features.get('device_fingerprint_new', 0) == 1 and features.get('ip_risk_score', 0) > 0.6:
            score += 30.0
        if features.get('billing_shipping_mismatch', 0) == 1:
            score += 20.0
        if features.get('amount_zscore', 0) > 3.0:
            score += 20.0
        if features.get('customer_dispute_rate', 0) > 0.2:
            score += 25.0
        return min(score, 100.0)

    def _heuristic_chargeback_score(self, features: dict) -> float:
        """Fallback chargeback heuristic."""
        score = features.get('customer_dispute_rate', 0) * 80.0
        if features.get('is_first_time_card', 0) == 1 and features.get('is_high_value', 0) == 1:
            score += 25.0
        if features.get('billing_shipping_mismatch', 0) == 1:
            score += 20.0
        return min(score, 100.0)

    def apply_binary_rules(self, features: dict, base_fraud: float, base_cb: float) -> Tuple[float, float, list]:
        """
        Apply deterministic policy floors that cannot be diluted by statistical models.
        """
        overrides = []
        fraud_score = float(base_fraud)
        cb_score = float(base_cb)

        # Rule 1: High Velocity Spike
        if features.get('txn_count_1h', 0) >= 0.5:
            fraud_score = max(fraud_score, 82.0)
            overrides.append({
                "id": "RULE_VELOCITY_SPIKE",
                "reason": "Rapid transaction velocity detected (>5 txns/hr from same account/device)",
                "force_severity": "CRITICAL",
                "category": "Velocity"
            })

        # Rule 2: Card Testing Pattern
        if features.get('amount_log', 0) < 4.6 and features.get('txn_count_1h', 0) >= 0.3:
            fraud_score = max(fraud_score, 85.0)
            overrides.append({
                "id": "RULE_CARD_TESTING",
                "reason": "Card testing signature detected (rapid micro-authorizations under INR 100)",
                "force_severity": "CRITICAL",
                "category": "Card Abuse"
            })

        # Rule 3: Syndicate / Abuse Ring
        if (features.get('device_fingerprint_new', 0) == 1 and 
            features.get('ip_risk_score', 0) >= 0.7 and 
            (features.get('txn_count_24h', 0) >= 0.15 or features.get('billing_shipping_mismatch', 0) == 1)):
            fraud_score = max(fraud_score, 90.0)
            cb_score = max(cb_score, 85.0)
            overrides.append({
                "id": "RULE_ABUSE_RING",
                "reason": "Syndicate / abuse ring characteristics detected (new hardware with high proxy/VPN score)",
                "force_severity": "CRITICAL",
                "category": "Syndicate Risk"
            })

        # Rule 4: International High-Value Address Mismatch
        if (features.get('billing_shipping_mismatch', 0) == 1 and 
            features.get('is_international', 0) == 1 and 
            features.get('is_high_value', 0) == 1):
            fraud_score = max(fraud_score, 78.0)
            cb_score = max(cb_score, 75.0)
            overrides.append({
                "id": "RULE_GEO_MISMATCH",
                "reason": "Cross-border high-ticket purchase with mismatched billing and shipping jurisdictions",
                "force_severity": "HIGH",
                "category": "Identity"
            })

        # Rule 5: Chronic Chargeback Abuser
        if features.get('customer_dispute_rate', 0) >= 0.35:
            cb_score = max(cb_score, 85.0)
            fraud_score = max(fraud_score, 70.0)
            overrides.append({
                "id": "RULE_CHRONIC_DISPUTER",
                "reason": "Customer profile exhibits severe historical chargeback frequency (>35% dispute rate)",
                "force_severity": "HIGH",
                "category": "Chargeback Abuse"
            })

        # Rule 6: Account Takeover (ATO) Pattern
        if (features.get('device_fingerprint_new', 0) == 1 and 
            features.get('is_high_value', 0) == 1 and 
            features.get('is_late_night', 0) == 1):
            fraud_score = max(fraud_score, 85.0)
            overrides.append({
                "id": "RULE_ATO_PATTERN",
                "reason": "High-value purchase from unrecognized device executed during overnight hours",
                "force_severity": "CRITICAL",
                "category": "Account Takeover"
            })

        return fraud_score, cb_score, overrides

    def predict(self, features: dict, card_bin: str = None, device_fingerprint: str = None) -> dict:
        """
        Execute ensemble fraud and chargeback inference.
        """
        if not self._loaded:
            self.load_models()

        input_vec = self._get_model_input(features)

        # 1. Fraud model inference
        if self.fraud_model is not None:
            try:
                probs = self.fraud_model.predict_proba(input_vec)[0]
                base_fraud = float(probs[1]) * 100.0 if len(probs) > 1 else float(probs[0]) * 100.0
            except Exception as e:
                print(f"[WARN] Fraud model inference error: {e}")
                base_fraud = self._heuristic_fraud_score(features)
        else:
            base_fraud = self._heuristic_fraud_score(features)

        # 2. Chargeback model inference
        if self.chargeback_model is not None:
            try:
                probs = self.chargeback_model.predict_proba(input_vec)[0]
                base_cb = float(probs[1]) * 100.0 if len(probs) > 1 else float(probs[0]) * 100.0
            except Exception as e:
                print(f"[WARN] Chargeback model inference error: {e}")
                base_cb = self._heuristic_chargeback_score(features)
        else:
            base_cb = self._heuristic_chargeback_score(features)

        # 3. Apply binary policy overrides
        fraud_score, cb_score, overrides = self.apply_binary_rules(features, base_fraud, base_cb)

        # 4. Threat Intelligence Checks (Layer 2)
        if card_bin and check_card_bin(card_bin):
            overrides.append({
                "id": "RULE_THREAT_INTEL_BIN",
                "reason": f"Card BIN {card_bin} flagged in BFSI Fraud Intelligence database",
                "force_severity": "CRITICAL",
                "category": "Threat Intel"
            })
            fraud_score = max(fraud_score, 92.0)

        if device_fingerprint and check_device(device_fingerprint):
            overrides.append({
                "id": "RULE_THREAT_INTEL_DEVICE",
                "reason": "Device hardware hash linked to known fraud ring syndicate",
                "force_severity": "CRITICAL",
                "category": "Threat Intel"
            })
            fraud_score = max(fraud_score, 95.0)
            cb_score = max(cb_score, 90.0)

        fraud_score = min(round(fraud_score, 2), 100.0)
        cb_score = min(round(cb_score, 2), 100.0)

        # Severity classification
        max_score = max(fraud_score, cb_score)
        if max_score >= 85:
            risk_level = "CRITICAL"
        elif max_score >= 60:
            risk_level = "HIGH"
        elif max_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "fraud_score": fraud_score,
            "chargeback_score": cb_score,
            "risk_level": risk_level,
            "is_fraudulent": (fraud_score >= 50.0 or cb_score >= 60.0),
            "base_fraud_score": round(base_fraud, 2),
            "base_chargeback_score": round(base_cb, 2),
            "overrides": overrides,
            "model_versions": {
                "fraud_model": self.fraud_model_version,
                "chargeback_model": self.chargeback_model_version,
            }
        }


# Singleton instance
fraud_engine = FraudScoringEngine()
