import sys; sys.path.insert(0, '.')
import asyncio
from app.db.database import init_db
from app.engine.pipeline import run_pipeline
from app.api.dashboard import get_dashboard_alerts

async def test_demo():
    await init_db()
    
    # Laptop A
    res_a = await run_pipeline(url='http://paypa1-update.tk', channel='url', device_id='laptop-abc-123')
    print("Laptop A scan result severity:", res_a['assessment'].severity.name if hasattr(res_a['assessment'].severity, 'name') else res_a['assessment'].severity)
    
    # Laptop B 
    res_b = await run_pipeline(url='https://google.com', channel='url', device_id='laptop-xyz-789')
    print("Laptop B scan result severity:", res_b['assessment'].severity.name if hasattr(res_b['assessment'].severity, 'name') else res_b['assessment'].severity)

    # Fetch alerts
    alerts = await get_dashboard_alerts()
    print("\n--- Dashboard Alerts ---")
    for a in alerts[:2]: # Get only latest 2
        print(f"[{a.timestamp}] {a.device_id} -> {a.url} | {a.severity} ({a.action_taken})")

if __name__ == '__main__':
    asyncio.run(test_demo())
