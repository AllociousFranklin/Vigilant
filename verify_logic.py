import asyncio
import json
from app.engine.pipeline import run_pipeline
from app.api.schemas import Channel

async def test_redirect():
    print("Testing Redirect Logic...")
    result = await run_pipeline(
        url="http://microsoft.com@hacker-site.net/auth",
        channel="url"
    )
    print(f"Score: {result['risk_score']}")
    print(f"Severity: {result['severity']}")
    print(f"Reasons: {[r['reason'] for r in result['reasons']]}")
    
    print("\nTesting Email Scoping Logic...")
    result_email = await run_pipeline(
        text="HUGE SALE! Act now to get 50% off on all winter gear. Limited time offer!",
        channel="email"
    )
    print(f"Score: {result_email['risk_score']}")
    print(f"Severity: {result_email['severity']}")
    print(f"Reasons: {[r['reason'] for r in result_email['reasons']]}")

if __name__ == "__main__":
    asyncio.run(test_redirect())
