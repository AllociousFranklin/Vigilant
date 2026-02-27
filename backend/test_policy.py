import asyncio
from app.api.schemas import ScanRequest, Channel
from app.engine.detector import detection_engine
from app.engine.normalizer import normalize
from app.engine.ingestion import ingest
from app.engine.policy import PolicyEngine
from app.engine.features import extract_features

async def test_payload(label, url=None, text=None, channel=Channel.URL):
    print(f"--- Testing {label} ---")
    
    artifact = ingest(url=url, text=text, html_body=None, channel=channel.value, metadata=None)
    norm = await normalize(artifact, skip_expansion=True)
    features = extract_features(norm, norm.signals)
    
    # Simulate detection
    detect_res = detection_engine.predict(features, channel=channel.value)
    
    # Run policy
    policy = PolicyEngine()
    policy_res = policy.assess(features, detect_res['risk_score'], channel.value)
    
    print(f"Severity: {policy_res.get('severity', 'None')}")
    print(f"Threat Type: {policy_res.get('threat_type', 'None')}")
    print(f"Risk Score: {policy_res.get('risk_score', 'None')}")
    print(f"Brand Confidence: {max(features.get('url_brand_similarity', 0), features.get('url_brand_match', 0), features.get('nlp_sender_impersonation', 0))}")
    print(f"Features mapped: URL={ascii(url) if url else None}, Text={ascii(text[:20]) if text else None}")
    print()

async def main():
    # 1. Homoglyphs over HTTPS
    await test_payload("HTTPS Homoglyph", url="https://pаypal.com/login")
    # 2. Punycode
    await test_payload("Punycode Attack", url="https://xn--pypal-4ve.com/login")
    # 3. Callback Phishing
    text = "This is Microsoft Security. Your account was accessed from Russia. Call us immediately: +1-800-123-4567"
    await test_payload("Callback Phishing", text=text, channel=Channel.EMAIL)
    # 4. Document Lure
    text2 = "Secure Document Review Please sign the attached document to proceed."
    await test_payload("Document Lure", text=text2, channel=Channel.EMAIL)

if __name__ == "__main__":
    asyncio.run(main())
