"""VIGILANT Engine - Policy Engine

Handles deterministic severity floors, threat typing, and intent escalation.
Acts on the DetectionBlock (features) and AssessmentBlock (ML scores).
"""
from typing import Dict, Any
from app.api.schemas import ThreatType, Severity

class PolicyEngine:
    def __init__(self):
        self.policy_version = "1.0.0"

    def assess(self, features: Dict[str, Any], base_score: float, channel: str) -> Dict[str, Any]:
        """
        Applies deterministic rules over the ML base score.
        Returns the finalized assessment properties.
        """
        severity_score = base_score
        threat_type = ThreatType.UNKNOWN
        confidence_band = "HIGH_CONFIDENCE"
        
        brand_impersonation = features.get('url_brand_similarity', 0) > 0.8 or features.get('nlp_sender_impersonation', 0) > 0.8
        urgency = features.get('nlp_urgency_score', 0) > 0.7
        coercion = features.get('nlp_intent_coercion', 0) > 0.7
        has_url = features.get('url_length', 0) > 0 or features.get('text_has_url', 0) > 0
        credential_harvest = features.get('nlp_intent_harvest', 0) > 0.7 or features.get('struct_has_login_form', 0) == 1
        
        # Rule 3: Credential Harvesting Intent
        if (brand_impersonation and credential_harvest) or (brand_impersonation and has_url and urgency and channel in ["email", "sms"]):
            # For emails with URLs and urgent brand impersonation, escalate to critical if asking for verification (simulated)
            severity_score = max(severity_score, 85.0) # Escalating to CRITICAL
            threat_type = ThreatType.CREDENTIAL_HARVESTING
            
        # Rule 2: Callback Phishing
        elif channel in ["email", "sms"] and brand_impersonation and coercion and not has_url:
            severity_score = max(severity_score, 50.0)
            threat_type = ThreatType.CALLBACK_PHISHING
            
        # Rule 1: Brand + Urgency
        elif channel in ["email", "sms"] and brand_impersonation and (urgency or coercion):
            severity_score = max(severity_score, 40.0)
            threat_type = ThreatType.BRAND_PHISHING
        
        # Default Threat Type Mapping if ML scored it high but no specific rule matched
        elif severity_score >= 35.0 and threat_type == ThreatType.UNKNOWN:
             if features.get('url_brand_similarity', 0) > 0.8:
                 threat_type = ThreatType.BRAND_PHISHING
             elif features.get('struct_has_login_form', 0) == 1:
                 threat_type = ThreatType.CREDENTIAL_HARVESTING
             else:
                 threat_type = ThreatType.SUSPICIOUS_PROMOTION

        if severity_score < 35.0:
            threat_type = ThreatType.NONE

        if severity_score >= 85:
            severity = Severity.CRITICAL
        elif severity_score >= 65:
            severity = Severity.HIGH
        elif severity_score >= 35:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        # Confidence banding logic
        if severity_score >= 65 and base_score < 35:
             confidence_band = "MIXED_SIGNALS" # Policy overrode ML heavily
        elif base_score >= 85 and not brand_impersonation and not credential_harvest and not urgency:
             confidence_band = "LOW_CONFIDENCE" # ML high but no obvious features

        return {
            "risk_score": round(severity_score, 2),
            "severity": severity,
            "threat_type": threat_type,
            "is_phishing": severity_score >= 50.0,
            "confidence_band": confidence_band,
            "policy_version": self.policy_version
        }

policy_engine = PolicyEngine()
