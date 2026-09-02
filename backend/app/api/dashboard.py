"""SENTINEL - Dashboard APIs for Merchant Risk Center"""
from fastapi import APIRouter, HTTPException
import aiosqlite
from pydantic import BaseModel
from typing import List
from app.core.config import settings

dashboard_router = APIRouter()


class DashboardAlert(BaseModel):
    timestamp: str
    assessment_id: str
    merchant_id: str
    amount: float
    payment_method: str
    risk_level: str
    fraud_type: str
    action_taken: str


@dashboard_router.get("/alerts", response_model=List[DashboardAlert])
async def get_dashboard_alerts():
    """Get real-time fraud & chargeback alerts for the merchant operations dashboard."""
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            rows = await db.execute_fetchall(
                """SELECT timestamp, assessment_id, merchant_id, amount, payment_method, 
                          risk_level, fraud_type, recommended_action 
                   FROM assessments 
                   ORDER BY timestamp DESC LIMIT 50"""
            )

            alerts = []
            for row in rows:
                alerts.append(DashboardAlert(
                    timestamp=row["timestamp"],
                    assessment_id=row["assessment_id"],
                    merchant_id=row["merchant_id"],
                    amount=float(row["amount"]),
                    payment_method=row["payment_method"],
                    risk_level=row["risk_level"],
                    fraud_type=row["fraud_type"],
                    action_taken=row["recommended_action"],
                ))
            return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")
