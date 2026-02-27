"""VIGILANT Engine - Policy Engine

Handles deterministic severity floors, threat typing, and intent escalation.
Acts on the DetectionBlock (features) and AssessmentBlock (ML scores).
"""
from typing import Dict, Any
from app.api.schemas import ThreatType, Severity

class PolicyEngine:
    def __init__(self):
        self.policy_version = "3.0.0"

    def assess(self, features: Dict[str, Any], base_score: float, channel: str) -> Dict[str, Any]:
        """
        Applies deterministic rules over the ML base score.
        Returns the finalized assessment properties.
        """
        severity_score = base_score
        threat_type = ThreatType.UNKNOWN
        confidence_band = "HIGH_CONFIDENCE"
        
        # Normalize brand confidence
        url_brand_similarity = features.get('url_brand_similarity', 0.0)
        url_brand_match = features.get('url_brand_match', 0.0)
        brand_confidence_url = max(url_brand_similarity, url_brand_match)
        nlp_sender_impersonation = features.get('nlp_sender_impersonation', 0.0)
        brand_confidence = max(brand_confidence_url, nlp_sender_impersonation)
        
        urgency = features.get('nlp_urgency_score', 0) > 0.7
        coercion = features.get('nlp_intent_coercion', 0) > 0.7
        has_url = features.get('url_length', 0) > 0 or features.get('text_has_url', 0) > 0
        credential_harvest = features.get('nlp_intent_harvest', 0) > 0.7 or features.get('struct_has_login_form', 0) == 1
        homoglyph_count = features.get('struct_homoglyph_count', 0.0)
        is_punycode = features.get('url_is_punycode', 0) == 1
        has_phone_number = features.get('nlp_phone_number_present', 0) == 1
        document_language = features.get('nlp_document_language', 0) == 1
        authority_score = features.get('nlp_authority_score', 0.0)
        
        # 1. Homoglyphs
        if homoglyph_count > 0:
            if brand_confidence > 0.7:
                severity_score = max(severity_score, 85.0) # CRITICAL
                threat_type = ThreatType.BRAND_PHISHING
            else:
                severity_score = max(severity_score, 65.0) # HIGH
        
        # 2. Punycode
        elif is_punycode and brand_confidence > 0.7:
            severity_score = max(severity_score, 65.0) # HIGH
            threat_type = ThreatType.BRAND_PHISHING
            
        # 3. Credential Harvesting Intent
        elif (brand_confidence > 0.7 and credential_harvest) or (brand_confidence > 0.7 and has_url and urgency and channel in ["email", "sms"]):
            # For emails with URLs and urgent brand impersonation, escalate to critical if asking for verification (simulated)
            severity_score = max(severity_score, 85.0) # Escalating to CRITICAL
            threat_type = ThreatType.CREDENTIAL_HARVESTING
            
        # 4. Callback Phishing
        elif channel in ["email", "sms"] and brand_confidence > 0.7 and coercion and has_phone_number and not has_url:
            severity_score = max(severity_score, 50.0) # MEDIUM
            threat_type = ThreatType.CALLBACK_PHISHING
            
        # 5. Brand + Urgency
        elif channel in ["email", "sms"] and brand_confidence > 0.7 and (urgency or coercion):
            severity_score = max(severity_score, 40.0)
            threat_type = ThreatType.BRAND_PHISHING
            
        # 6. Document lure (soft)
        elif document_language and not credential_harvest:
            threat_type = ThreatType.DOCUMENT_LURE
            severity_score = max(severity_score, 15.0) # Ensure it doesn't fall below something minimal, but LOW

        # 7. Safe Authority Guardrail (Must override prior ML scores)
        # If ML flagged it high but policy says it's just benign authority
        if authority_score > 0.7 and brand_confidence < 0.2 and not credential_harvest:
            severity_score = min(severity_score, 30.0) # Cap at LOW
            if severity_score < 35.0:
                 threat_type = ThreatType.UNKNOWN

        # Authority-based threat assignment if it wasn't suppressed
        if authority_score > 0.7 and severity_score >= 35.0 and threat_type == ThreatType.UNKNOWN:
             threat_type = ThreatType.SOCIAL_ENGINEERING
        
        # Default Threat Type Mapping if ML scored it high but no specific rule matched
        elif severity_score >= 35.0 and threat_type == ThreatType.UNKNOWN:
             if brand_confidence > 0.8:
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
        elif base_score >= 85 and brand_confidence <= 0.7 and not credential_harvest and not urgency:
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
