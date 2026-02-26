import requests
import json
import time
import os
import numpy as np

API_URL = "http://127.0.0.1:8003/api/scan"

class BrutalTester:
    def __init__(self):
        self.results = {
            "functional": [],
            "adversarial": [],
            "false_positive": [],
            "explainability": [],
            "performance": [],
            "degradation": []
        }

    def log(self, category, name, payload, expected_behavior):
        print(f"[{category.upper()}] Testing: {name}...")
        try:
            start_time = time.perf_counter()
            response = requests.post(API_URL, json=payload, timeout=10)
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                result = {
                    "name": name,
                    "payload": payload,
                    "score": data['risk_score'],
                    "severity": data['severity'],
                    "reasons": [r['reason'] for r in data['reasons']],
                    "latency": latency,
                    "success": True,
                    "expected": expected_behavior
                }
                self.results[category].append(result)
                print(f"  -> Score: {data['risk_score']} ({data['severity']}) | Latency: {latency:.2f}ms")
            else:
                print(f"  [!!] API Error {response.status_code}")
                self.results[category].append({"name": name, "success": False, "error": response.status_code})
        except Exception as e:
            print(f"  [!!] Connection Error: {e}")
            self.results[category].append({"name": name, "success": False, "error": str(e)})

    def run_all(self):
        # 1. PILLAR: FUNCTIONAL CORRECTNESS
        self.log("functional", "Known Clean Domain", {"url": "https://www.google.com", "channel": "url"}, "Score < 10")
        self.log("functional", "Empty Input", {}, "Graceful 400 Error")
        
        # 2. PILLAR: ADVERSARIAL & EVASION
        self.log("adversarial", "Brand Spoof + No HTTPS", 
                 {"url": "http://pаypal-security.tk/login", "channel": "url"}, 
                 "CRITICAL (Red Flag Override)")
        self.log("adversarial", "Redirect Trick (@ symbol)", 
                 {"url": "http://microsoft.com@hacker-site.net/auth", "channel": "url"}, 
                 "MEDIUM/HIGH (at-symbol penalty)")
        self.log("adversarial", "Phishing without Links (Callback)", 
                 {"text": "Your Amazon account has been compromised. Do not click any links. Call us at 1-800-FAKE-SEC to verify.", "channel": "email"}, 
                 "MEDIUM (NLP Threat signals)")

        # 3. PILLAR: FALSE POSITIVE STRESS
        self.log("false_positive", "Marketing Spam (Benign)", 
                 {"text": "HUGE SALE! Act now to get 50% off on all winter gear. Limited time offer!", "channel": "email"}, 
                 "MEDIUM (Should be flagged as spam-like but not phishing)")
        self.log("false_positive", "High Entropy GitHub URL", 
                 {"url": "https://github.com/archive/v1.0.2/7dd6f630-8612-4a6c-b5e4-e5ea4ffb0b66.tar.gz", "channel": "url"}, 
                 "LOW (Reputable domain should override high entropy)")

        # 4. PILLAR: EXPLAINABILITY VALIDATION
        # Test: Does removing a word remove the reason?
        self.log("explainability", "Urgent Threat Text", 
                 {"text": "URGENT: Your account is restricted.", "channel": "email"}, 
                 "Should show Urgency reason")
        self.log("explainability", "Neutral Text", 
                 {"text": "Your account is open.", "channel": "email"}, 
                 "Urgency reason should disappear")

        # 5. PILLAR: PERFORMANCE & DEGRADATION
        # Test: Expand timeout (Mocked by a very long bitly link or invalid domain)
        self.log("performance", "Timeout Simulation", 
                 {"url": "http://this-domain-does-not-exist-and-will-timeout.com", "channel": "url"}, 
                 "Should finish under 2s and return Heuristic results")

        # Save results
        with open("brutal_audit_data.json", "w") as f:
            json.dump(self.results, f, indent=2)

if __name__ == "__main__":
    tester = BrutalTester()
    tester.run_all()
