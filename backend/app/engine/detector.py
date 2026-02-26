"""VIGILANT Engine - Layer 4: Detection & Scoring Engine

Ensemble inference core. Stateless, horizontally scalable.
Designed for sub-100ms latency.
"""
import numpy as np
import joblib
import os
from typing import Optional
from app.core.config import settings


# Feature order must match training
URL_FEATURE_NAMES = [
    'url_length', 'url_dot_count', 'url_hyphen_count', 'url_at_symbol',
    'url_entropy', 'url_digit_ratio', 'url_has_ip', 'url_suspicious_tld',
    'url_subdomain_depth', 'url_path_length', 'url_has_https', 'url_brand_similarity',
    'url_brand_match',
]

NLP_FEATURE_NAMES = [
    'nlp_urgency_score', 'nlp_threat_count', 'nlp_credential_count',
    'nlp_action_count', 'nlp_exclamation_ratio', 'nlp_caps_ratio',
    'nlp_sender_impersonation', 'nlp_ai_pattern_score',
    'nlp_intent_trigger', 'nlp_intent_coercion', 'nlp_intent_harvest',
    'nlp_intent_alignment',
]

STRUCTURAL_FEATURE_NAMES = [
    'struct_href_mismatch', 'struct_has_login_form', 'struct_hidden_ratio',
    'struct_homoglyph_count', 'struct_obfuscation_score',
]

ALL_FEATURE_NAMES = URL_FEATURE_NAMES + NLP_FEATURE_NAMES + STRUCTURAL_FEATURE_NAMES


class DetectionEngine:
    """
    Layer 4: Ensemble detection engine.
    
    - Model A: URL-based classifier (XGBoost)
    - Model B: NLP text classifier (Random Forest)
    - Aggregation: Weighted confidence scoring
    - Graceful degradation: if one model fails, the other still works
    """
    
    def __init__(self):
        self.url_model = None
        self.nlp_model = None
        self.url_model_version = "none"
        self.nlp_model_version = "none"
        self._loaded = False
    
    def load_models(self):
        """Load pre-trained models from disk."""
        # URL model
        url_path = settings.URL_MODEL_PATH
        if os.path.exists(url_path):
            self.url_model = joblib.load(url_path)
            self.url_model_version = "v1.0"
        else:
            print(f"[WARN] URL model not found at {url_path} — using heuristic fallback")
        
        # NLP model
        nlp_path = settings.NLP_MODEL_PATH
        if os.path.exists(nlp_path):
            self.nlp_model = joblib.load(nlp_path)
            self.nlp_model_version = "v1.0"
        else:
            print(f"[WARN] NLP model not found at {nlp_path} — using heuristic fallback")
        
        self._loaded = True
    
    def _heuristic_url_score(self, features: dict) -> float:
        """Fallback heuristic when ML model is not available."""
        score = 0.0
        
        # Long URLs are suspicious
        if features.get('url_length', 0) > 75:
            score += 15
        if features.get('url_length', 0) > 150:
            score += 10
        
        # IP address instead of domain
        if features.get('url_has_ip', 0):
            score += 25
        
        # No HTTPS
        if not features.get('url_has_https', 0):
            score += 10
        
        # Suspicious TLD
        if features.get('url_suspicious_tld', 0):
            score += 20
        
        # Brand impersonation
        brand_sim = features.get('url_brand_similarity', 0)
        score += brand_sim * 30
        
        # High entropy
        if features.get('url_entropy', 0) > 4.5:
            score += 10
        
        # @ symbol in URL
        if features.get('url_at_symbol', 0):
            score += 20
        
        # Deep subdomains
        if features.get('url_subdomain_depth', 0) > 2:
            score += 10
        
        return min(score, 100)
    
    def _get_model_input(self, model, features: dict) -> np.ndarray:
        """
        Safely build feature vector for a model.
        Legacy models expect 25 features. New ones might expect more.
        """
        full_vec = [features.get(f, 0) for f in ALL_FEATURE_NAMES]
        
        # Check model expectations
        try:
            if hasattr(model, "n_features_in_"):
                n = model.n_features_in_
            elif hasattr(model, "feature_names_in_"):
                n = len(model.feature_names_in_)
            else:
                # Default fallback for our legacy models
                n = 25
            
            return np.array([full_vec[:n]])
        except Exception:
            # Absolute fallback to legacy size
            return np.array([full_vec[:25]])

    def apply_binary_rules(self, features: dict, base_score: float, channel: str = "url", suppress_rules: list = None) -> tuple[float, list]:
        """
        Apply non-negotiable security overrides.
        Rules are channel-scoped to prevent text analysis from using URL logic.
        """
        applied = []
        suppress_rules = suppress_rules or []
        new_score = float(base_score)

        if channel == "url":
            # Rule 1: Brand Spoofing
            if "RULE_BRAND_SPOOF" not in suppress_rules:
                if features.get('url_brand_similarity', 0) > 0.8 and features.get('url_brand_match', 0):
                    new_score = max(new_score, 80.0)
                    applied.append({
                        "id": "RULE_BRAND_SPOOF",
                        "reason": "Domain resembles a protected brand but is not official.",
                        "force_severity": "HIGH"
                    })

            # Rule 2: Homoglyphs on non-HTTPS
            if "RULE_HOMOGLYPH_INSECURE" not in suppress_rules:
                if features.get('struct_homoglyph_count', 0) > 0 and not features.get('url_has_https', 0):
                    new_score = max(new_score, 85.0)
                    applied.append({
                        "id": "RULE_HOMOGLYPH_INSECURE",
                        "reason": "Visually deceptive characters used on an insecure connection.",
                        "force_severity": "CRITICAL"
                    })

            # Rule 3: Redirection Obfuscation (@ symbol)
            if "RULE_REDIRECT_OBFUSCATION" not in suppress_rules:
                if features.get('url_at_symbol', 0):
                    new_score = max(new_score, 75.0)
                    applied.append({
                        "id": "RULE_REDIRECT_OBFUSCATION",
                        "reason": "URL uses '@' symbol to hide the actual host destination.",
                        "force_severity": "HIGH"
                    })

        return new_score, applied

    def predict(self, features: dict, channel: str = "url", suppress_rules: list = None) -> dict:
        """
        Run ensemble prediction with v2.0 hardening.
        """
        if not self._loaded:
            self.load_models()
        
        # 1. URL Model Prediction
        url_input = self._get_model_input(self.url_model, features)
        if self.url_model is not None:
            try:
                url_prob = self.url_model.predict_proba(url_input)[0]
                url_score = float(url_prob[1]) * 100 if len(url_prob) > 1 else float(url_prob[0]) * 100
            except Exception as e:
                print(f"[WARN] URL model inference error: {e}")
                url_score = self._heuristic_url_score(features)
        else:
            url_score = self._heuristic_url_score(features)
        
        # 2. NLP Model Prediction
        nlp_input = self._get_model_input(self.nlp_model, features)
        if self.nlp_model is not None:
            try:
                nlp_prob = self.nlp_model.predict_proba(nlp_input)[0]
                nlp_score = float(nlp_prob[1]) * 100 if len(nlp_prob) > 1 else float(nlp_prob[0]) * 100
            except Exception as e:
                print(f"[WARN] NLP model inference error: {e}")
                nlp_score = self._heuristic_nlp_score(features)
        else:
            nlp_score = self._heuristic_nlp_score(features)
        
        # 3. Structural Penalty
        struct_score = 0.0
        struct_score += features.get('struct_homoglyph_count', 0) * 40
        struct_score += features.get('struct_href_mismatch', 0) * 30
        struct_score += features.get('struct_has_login_form', 0) * 20
        struct_score += features.get('struct_obfuscation_score', 0) * 15
        
        # 4. Adaptive Weighting
        if channel == "url":
            base_score = (url_score * 0.7) + (nlp_score * 0.3)
        else:
            base_score = (url_score * 0.3) + (nlp_score * 0.7)
            
        # 5. Apply Binary Overrides (Stage A: Pre-aggregation)
        risk_score, overrides = self.apply_binary_rules(features, base_score, channel, suppress_rules)
        overrides = overrides or []
        
        # Final Aggregation
        final_score = (risk_score * 0.6) + (min(struct_score, 100) * 0.4)
        
        # 6. Apply Binary Overrides (Stage B: Final Floor Enforcement)
        # If any override forces a specific severity, ensure the final_score matches it.
        for ovr in overrides:
            if ovr.get('force_severity') == 'CRITICAL':
                final_score = max(final_score, 85.0)
            elif ovr.get('force_severity') == 'HIGH':
                final_score = max(final_score, 65.0)

        final_score = min(round(final_score, 2), 100)
        
        # Determine severity
        if final_score >= 85:
            severity = "CRITICAL"
        elif final_score >= 65:
            severity = "HIGH"
        elif final_score >= 35:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        return {
            "risk_score": final_score,
            "severity": severity,
            "is_phishing": final_score >= 50,
            "url_score": round(url_score, 2),
            "nlp_score": round(nlp_score, 2),
            "struct_score": round(struct_score, 2),
            "overrides": overrides,
            "model_versions": {
                "url_model": self.url_model_version,
                "nlp_model": self.nlp_model_version,
            },
        }


# Singleton instance
detection_engine = DetectionEngine()
