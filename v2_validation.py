import httpx
import time
import asyncio
import json

BASE_URL = "http://localhost:8001"

async def test_async_severity_upgrade():
    print("\n--- [PHASE 4] Testing Async Severity Upgrade ---")
    
    # We use a known shortener pattern. In a real test, this would be a real bit.ly link.
    # For this test, we simulate the 'preliminary' logic by checking if it triggers expansion.
    
    payload = {
        "url": "http://bit.ly/paypal-security-update-2026", # This will trigger 'was_shortened'
        "channel": "url"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Preliminary Request
        print(f"[STEP 1] Sending Preliminary Scan Request...")
        start = time.perf_counter()
        response = await client.post(f"{BASE_URL}/api/scan", json=payload)
        latency = (time.perf_counter() - start) * 1000
        
        if response.status_code != 200:
            print(f"  -> ERROR: Request failed with {response.status_code}")
            print(f"  -> Response: {response.text}")
            return

        data = response.json()
        scan_id = data["scan_id"]
        
        print(f"  -> Scan ID: {scan_id}")
        print(f"  -> Preliminary Processing State: {data['processing_state']}")
        print(f"  -> Preliminary Severity: {data['severity']}")
        print(f"  -> Preliminary Latency: {latency:.2f}ms (Target < 50ms)")
        
        assert data["processing_state"] in ["PRELIMINARY", "ENRICHING"]
        # Since bit.ly expansion takes time, the initial should be fast and likely LOW
        # (unless structural rules alone flag it).
        
        # 2. Wait for Background Enrichment
        print(f"[STEP 2] Waiting for Enriched Analysis (Background Task)...")
        await asyncio.sleep(5) # Give it time to attempt expansion (even if it 404s, it will finish)
        
        # 3. Check History for Updated Record
        print(f"[STEP 3] Verifying Enriched Record in History...")
        history_resp = await client.get(f"{BASE_URL}/api/history?page_size=1")
        history_data = history_resp.json()
        
        # Find our scan
        enriched_item = next((item for item in history_data["items"] if item["scan_id"] == scan_id), None)
        
        if enriched_item:
            print(f"  -> Enriched Severity: {enriched_item['severity']}")
            print(f"  -> Enriched Risk Score: {enriched_item['risk_score']}")
            
            # If our expansion logic worked (even if it just finished and realized it couldn't expand),
            # the record is now 'final' in the DB.
            # In a real environment with a real expansion to a phishing site, it would be CRITICAL.
        else:
            print("  -> ERROR: Scan ID not found in history.")

async def test_binary_overrides():
    print("\n--- [PHASE 4] Testing Binary Overrides & Suppression ---")
    
    # Payload that triggers RULE_HOMOGLYPH_INSECURE
    # http://pаypal.com (Cyrillic 'a')
    payload = {
        "url": "http://p\u0430ypal.com", 
        "channel": "url"
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: Forced Override
        print("[STEP 1] Testing Forced Override (RULE_HOMOGLYPH_INSECURE)...")
        resp = await client.post(f"{BASE_URL}/api/scan", json=payload)
        data = resp.json()
        print(f"  -> Severity: {data.get('severity')} (Expected: CRITICAL)")
        overrides = data.get('overrides') or []
        print(f"  -> Overrides: {[o.get('id') for o in overrides]}")
        
        # Test 2: Suppressed Override
        print("[STEP 2] Testing Suppressed Override...")
        payload["suppress_rules"] = ["RULE_HOMOGLYPH_INSECURE"]
        resp = await client.post(f"{BASE_URL}/api/scan", json=payload)
        data = resp.json()
        print(f"  -> Severity: {data.get('severity')} (Should be lower than CRITICAL)")
        overrides = data.get('overrides') or []
        print(f"  -> Overrides: {[o.get('id') for o in overrides]}")

if __name__ == "__main__":
    asyncio.run(test_async_severity_upgrade())
    asyncio.run(test_binary_overrides())
