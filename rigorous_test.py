import requests
import json
import time
import pandas as pd

API_URL = "http://localhost:8000/api/scan"

TEST_CASES = [
    {
        "name": "Homoglyph Typosquatting",
        "type": "url",
        "payload": {"url": "http://pаypal.com/secure-login", "channel": "url"},
        "description": "Uses Cyrillic 'a' (\\u0430) instead of Latin 'a'. Tests Layer 2 Normalization."
    },
    {
        "name": "Shortened Phishing URL",
        "type": "url",
        "payload": {"url": "https://bit.ly/3uX9jK1", "channel": "url"}, # Mocked expansion in engine
        "description": "Tests Layer 2 Expansion and Layer 3 Entropy/TLD analysis."
    },
    {
        "name": "Encoded Redirect Trick",
        "type": "url",
        "payload": {"url": "http://google.com@phish-site.tk/%6c%6f%67%69%6e", "channel": "url"},
        "description": "Uses @ symbol and hex encoding. Tests Layer 2 Decoding and Layer 3 @ symbol detection."
    },
    {
        "name": "Urgency Social Engineering (Email)",
        "type": "email",
        "payload": {
            "text": "URGENT: Your account access has been restricted due to suspicious activity. Verify your identity within 24 hours at http://secure-verify.zip or your account will be PERMANENTLY DELETED.",
            "channel": "email"
        },
        "description": "Tests Layer 3 NLP Features (Urgency, Threat, Credential intent)."
    },
    {
        "name": "SMS Prize Scam",
        "type": "sms",
        "payload": {
            "text": "CONGRATULATIONS! You have won a $1000 Amazon Gift Card. Claim now at http://amz-rewards.top/claim. Fast! Limited time only!",
            "channel": "sms"
        },
        "description": "Tests Layer 3 NLP and URL TLD features."
    },
    {
        "name": "Legitimate Enterprise URL",
        "type": "url",
        "payload": {"url": "https://www.microsoft.com/en-us/security", "channel": "url"},
        "description": "Tests False Positive avoidance on high-reputation domains."
    },
    {
        "name": "Legitimate Personal Email",
        "type": "email",
        "payload": {
            "text": "Hey, are we still meeting for lunch at 1 PM? Let me know! Looking forward to it.",
            "channel": "email"
        },
        "description": "Tests baseline for low-risk textual content."
    }
]

def run_tests():
    print("🚀 Starting Rigorous Security Testing for VIGILANT...\n")
    results = []
    
    for case in TEST_CASES:
        print(f"Testing Case: {case['name']}...")
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=case['payload'], timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "Name": case['name'],
                    "Status": "PASSED" if data['is_phishing'] == (case['type'] != 'legit') else "FLAGGED",
                    "Score": data['risk_score'],
                    "Severity": data['severity'],
                    "Reasons": ", ".join([r['reason'] for r in data['reasons'][:2]]),
                    "Latency": data['latency_ms']
                })
                print(f"  [✓] Score: {data['risk_score']} | Severity: {data['severity']}")
            else:
                print(f"  [✗] Failed with status code: {response.status_code}")
        except Exception as e:
            print(f"  [✗] Error: {e}")
            
    # Save to JSON for report generation
    with open("rigorous_test_results.json", "w") as f:
        json.dump({"results": results, "timestamp": time.ctime()}, f, indent=2)

if __name__ == "__main__":
    # Wait for server to be ready
    time.sleep(5)
    run_tests()
