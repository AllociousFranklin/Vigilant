"""VIGILANT - Dashboard APIs for Hackathon Demo"""
from fastapi import APIRouter, HTTPException
import aiosqlite
from pydantic import BaseModel
from typing import List
from app.core.config import settings

dashboard_router = APIRouter()

class DashboardAlert(BaseModel):
    timestamp: str
    device_id: str
    url: str
    severity: str
    action_taken: str

@dashboard_router.get("/alerts", response_model=List[DashboardAlert])
async def get_dashboard_alerts():
    """Get real-time alerts for the SOC dashboard."""
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            rows = await db.execute_fetchall(
                "SELECT timestamp, device_id, normalized_url, input_preview, channel, severity FROM detections ORDER BY timestamp DESC LIMIT 50"
            )
            
            alerts = []
            for row in rows:
                severity = row["severity"]
                
                # Infer action
                if severity == "CRITICAL" or severity == "CRITICAL (Block)":
                    action = "BLOCK"
                elif severity == "HIGH" or severity == "HIGH (Likely Phishing)":
                    action = "WARN"
                elif severity == "MEDIUM" or severity == "MEDIUM (Suspicious)":
                    action = "FLAG_FOR_REVIEW"
                else:
                    action = "ALLOW"
                    
                url = row["normalized_url"] if row["normalized_url"] else row["input_preview"]
                
                alerts.append(DashboardAlert(
                    timestamp=row["timestamp"],
                    device_id=row["device_id"] or "unknown_device",
                    url=url or "[Unknown Target]",
                    severity=severity,
                    action_taken=action
                ))
            return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")
