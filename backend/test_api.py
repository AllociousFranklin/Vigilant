import requests
import json

URL = "http://localhost:8000/api/scan"

cases = [
    {
        "name": "PayPal Flaw 1 Fix (Brand + Credential Harvester)",
        "payload": {
            "channel": "email",
            "text": "Your PayPal account has been suspended.\nVerify immediately:\nhttp://paypa1-update.tk"
        }
    },
    {
        "name": "Callback Phishing Fix (Brand + Coercion)",
        "payload": {
            "channel": "email",
            "text": "GeekSquad Auto-Renewal $499.00 processed. Call 800-444-1234 within 24 hours to cancel or face legal penalties."
        }
    }
]

for case in cases:
    print(f"--- Running: {case['name']} ---")
    try:
        response = requests.post(URL, json=case['payload'])
        # Pretty print response
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed to connect: {e}")
    print("\n")
