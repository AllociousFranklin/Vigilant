"""VIGILANT Engine - Layer 5: Explainability Engine

Translates model outputs into human-readable reasons.
This is the enterprise trust layer — security teams act on reasons, not scores.
"""

# Feature → Human-readable reason mapping
FEATURE_REASON_MAP = {
    # URL features
    'url_length': {
        'threshold': 75,
        'reason': 'Unusually long URL detected ({value} characters)',
        'category': 'URL Analysis',
    },
    'url_has_ip': {
        'threshold': 0.5,
        'reason': 'URL uses an IP address instead of a domain name',
        'category': 'URL Analysis',
    },
    'url_suspicious_tld': {
        'threshold': 0.5,
        'reason': 'Suspicious top-level domain detected',
        'category': 'URL Analysis',
    },
    'url_brand_similarity': {
        'threshold': 0.3,
        'reason': 'Domain impersonation detected — resembles a known brand',
        'category': 'Brand Impersonation',
    },
    'url_at_symbol': {
        'threshold': 0.5,
        'reason': 'URL contains @ symbol (potential redirect trick)',
        'category': 'URL Analysis',
    },
    'url_entropy': {
        'threshold': 4.5,
        'reason': 'High URL entropy suggests randomized/obfuscated content',
        'category': 'URL Analysis',
    },
    'url_has_https': {
        'threshold': -0.1,  # triggers when value is 0 (no HTTPS)
        'reason': 'No HTTPS encryption — connection is insecure',
        'category': 'Security',
        'inverse': True,
    },
    'url_subdomain_depth': {
        'threshold': 2,
        'reason': 'Excessive subdomain depth ({value} levels) — potential obfuscation',
        'category': 'URL Analysis',
    },
    'url_digit_ratio': {
        'threshold': 0.3,
        'reason': 'High digit ratio in URL suggests generated/obfuscated domain',
        'category': 'URL Analysis',
    },
    
    # NLP features
    'nlp_urgency_score': {
        'threshold': 0.3,
        'reason': 'Urgency-based language detected — creates pressure to act',
        'category': 'Social Engineering',
    },
    'nlp_threat_count': {
        'threshold': 0.3,
        'reason': 'Threatening or coercive language detected',
        'category': 'Social Engineering',
    },
    'nlp_credential_count': {
        'threshold': 0.3,
        'reason': 'Credential harvesting intent detected — requests sensitive information',
        'category': 'Credential Theft',
    },
    'nlp_action_count': {
        'threshold': 0.3,
        'reason': 'Suspicious call-to-action patterns detected',
        'category': 'Social Engineering',
    },
    'nlp_caps_ratio': {
        'threshold': 0.2,
        'reason': 'Excessive use of ALL CAPS — common intimidation tactic',
        'category': 'Social Engineering',
    },
    'nlp_sender_impersonation': {
        'threshold': 0.3,
        'reason': 'Content impersonates a known brand or organization',
        'category': 'Brand Impersonation',
    },
    # REMOVED AI PATTERN SCORE AS IT'S NOISY
    'nlp_exclamation_ratio': {
        'threshold': 0.15,
        'reason': 'Excessive exclamation marks — creates artificial urgency',
        'category': 'Social Engineering',
    },
    
    # Structural features
    'struct_href_mismatch': {
        'threshold': 0.1,
        'reason': 'Displayed link text does not match actual URL destination',
        'category': 'Deception',
    },
    'struct_has_login_form': {
        'threshold': 0.5,
        'reason': 'Login/credential form detected on suspicious page',
        'category': 'Credential Theft',
    },
    'struct_hidden_ratio': {
        'threshold': 0.1,
        'reason': 'Hidden content detected — potential cloaking technique',
        'category': 'Deception',
    },
    'text_unicode_noise': {
        'threshold': 0.1,
        'reason': 'Non-standard characters detected (often used to bypass text filters).',
        'category': 'Obfuscation',
    },
    'url_homoglyph_count': {
        'threshold': 0.1,
        'reason': 'Homoglyph characters detected (visually similar characters used to deceive)',
        'category': 'Obfuscation',
    },
    'struct_obfuscation_score': {
        'threshold': 0.1,
        'reason': 'URL obfuscation patterns detected (encoding, shortening, or punycode)',
        'category': 'Obfuscation',
    },
}

def get_signal_strength(measured_val: float, threshold: float, is_inverse: bool) -> str:
    """Returns 'STRONG', 'MODERATE', or 'WEAK' based on feature intensity relative to threshold."""
    if is_inverse:
        intensity = 1.0 - measured_val
    else:
        # If threshold is very small, we avoid division heavily
        if threshold <= 0:
            intensity = measured_val * 2
        else:
            intensity = measured_val / threshold

    if intensity > 2.5:
        return "STRONG"
    elif intensity > 1.2:
        return "MODERATE"
    else:
        return "WEAK"

def generate_explanations(features: dict, assessment_context: dict, channel: str = "url") -> list[dict]:
    """
    Layer 5: Generate human-readable explanations.
    Includes explicit channel-gating to prevent false explainability (like homoglyphs in SMS).
    Maps signal strength instead of fake percentages.
    """
    reasons = []
    
    # Priority 1: System Policy Overrides
    overrides = assessment_context.get('overrides') or []
    for ovr in overrides:
        reasons.append({
            'reason': f"{ovr['reason']}",
            'confidence': 100.0,
            'signal_strength': "STRONG",
            'category': 'System Policy',
            'id': ovr.get('id')
        })
        
    URL_ONLY_CATEGORIES = {'URL Analysis', 'Brand Impersonation', 'Security'}

    for feature_name, mapping in FEATURE_REASON_MAP.items():
        # CHANNEL FILTERING logic
        category = mapping.get('category', '')
        
        # Flaw 2 Fix: Homoglyph detection scoped to channel
        if channel != "url" and category in URL_ONLY_CATEGORIES:
            continue
        if channel != "url" and feature_name == "url_homoglyph_count":
            continue
        if channel == "url" and feature_name == "text_unicode_noise":
            continue
            
        value = features.get(feature_name, 0)
        threshold = mapping['threshold']
        is_inverse = mapping.get('inverse', False)
        
        # Check if feature exceeds threshold
        triggered = False
        if is_inverse:
            triggered = value < 0.5
        else:
            triggered = value > threshold
        
        if triggered:
            signal_strength = get_signal_strength(value, threshold, is_inverse)
            
            # Format the reason with actual values where applicable
            reason_text = mapping['reason']
            if '{value}' in reason_text:
                if isinstance(value, float) and value < 1:
                    reason_text = reason_text.replace('{value}', f"{value:.2f}")
                else:
                    reason_text = reason_text.replace('{value}', str(int(value)))
            
            reasons.append({
                'reason': reason_text,
                'signal_strength': signal_strength,
                'category': mapping['category'],
            })
    
    # Sort logically: Strongest signals first
    def strength_weight(r):
        return {"STRONG": 3, "MODERATE": 2, "WEAK": 1}.get(r.get('signal_strength', 'WEAK'), 0)
        
    reasons.sort(key=strength_weight, reverse=True)
    
    # If no specific reasons but risk is high, append generic policy warning
    if not reasons and assessment_context.get('risk_score', 0) > 50:
         reasons.append({
            'reason': 'Multiple subtle behavioral signals combine to indicate threat',
            'signal_strength': 'MODERATE',
            'category': 'Combined Analysis',
        })
    
    return reasons[:8]
