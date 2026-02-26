"""VIGILANT - API Routes"""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.api.schemas import (
    ScanRequest, ScanResponse, ReasonDetail,
    FeedbackRequest, FeedbackResponse,
    StatsResponse, HistoryResponse, HistoryItem,
)
from app.engine.pipeline import run_pipeline
from app.db.database import save_feedback, get_detections, get_stats


router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan_artifact(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Main scan endpoint — accepts URL, email text, or SMS text.
    Returns risk score, severity, and human-readable reasons.
    Supports asynchronous enrichment and rule suppression.
    """
    # Validate that at least one input is provided
    if not request.url and not request.text and not request.html_body:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'url', 'text', or 'html_body' must be provided"
        )
    
    try:
        result = await run_pipeline(
            url=request.url,
            text=request.text,
            html_body=request.html_body,
            channel=request.channel.value,
            metadata=request.metadata,
            background_tasks=background_tasks,
            suppress_rules=request.suppress_rules
        )
        
        # Convert reasons to response model
        reasons = [
            ReasonDetail(
                reason=r["reason"],
                confidence=r["confidence"],
                category=r["category"],
            )
            for r in result["reasons"]
        ]
        
        return ScanResponse(
            scan_id=result["scan_id"],
            risk_score=result["risk_score"],
            severity=result["severity"],
            is_phishing=result["is_phishing"],
            reasons=reasons,
            overrides=result.get("overrides"),
            features=result["features"],
            normalized_url=result.get("normalized_url"),
            channel=request.channel,
            latency_ms=result["latency_ms"],
            processing_state=result["processing_state"],
            model_versions=result.get("model_versions"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str = Query(None),
    channel: str = Query(None),
):
    """Get paginated detection history."""
    try:
        items, total = await get_detections(page, page_size, severity, channel)
        
        history_items = []
        for item in items:
            reasons_data = json.loads(item.get("reasons_json", "[]"))
            reasons = [
                ReasonDetail(
                    reason=r.get("reason", ""),
                    confidence=r.get("confidence", 0),
                    category=r.get("category", ""),
                )
                for r in reasons_data
            ]
            
            history_items.append(HistoryItem(
                scan_id=item["scan_id"],
                timestamp=item["timestamp"],
                channel=item["channel"],
                risk_score=item["risk_score"],
                severity=item["severity"],
                is_phishing=bool(item["is_phishing"]),
                input_preview=item.get("input_preview", ""),
                reasons=reasons,
                latency_ms=item.get("latency_ms", 0),
            ))
        
        return HistoryResponse(
            items=history_items,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        stats = await get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit analyst feedback on a detection."""
    valid_verdicts = {"false_positive", "confirmed_threat", "uncertain"}
    if request.verdict not in valid_verdicts:
        raise HTTPException(
            status_code=400,
            detail=f"Verdict must be one of: {valid_verdicts}"
        )
    
    try:
        await save_feedback({
            "scan_id": request.scan_id,
            "verdict": request.verdict,
            "notes": request.notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return FeedbackResponse(
            success=True,
            message=f"Feedback recorded for scan {request.scan_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.engine.detector import detection_engine
    return {
        "status": "healthy",
        "service": "VIGILANT",
        "version": "1.0.0",
        "models_loaded": detection_engine._loaded,
        "url_model": detection_engine.url_model_version,
        "nlp_model": detection_engine.nlp_model_version,
    }
