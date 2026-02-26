"""VIGILANT Engine - Pipeline Orchestrator

Chains all 6 layers together and measures latency.
This is the single entry point for all scan requests.
"""
import time
import uuid
import json
from datetime import datetime, timezone

from app.engine.ingestion import ingest
from app.engine.normalizer import normalize
from app.engine.features import extract_features
from app.engine.detector import detection_engine
from app.engine.explainer import generate_explanations
from app.db.database import save_detection


from fastapi import BackgroundTasks
from app.api.schemas import ProcessingState, Channel

async def enrich_detection(scan_id: str, artifact, suppress_rules: list = None):
    """
    Background Task: Perform deep analysis (URL expansion) and update detection.
    This fulfills the 'Enriched' part of the confidence contract.
    """
    try:
        # Layer 2: Full Normalization (including expansion)
        normalized = await normalize(artifact, skip_expansion=False)
        
        # Layer 3: Feature Extraction (on expanded URL)
        features = extract_features(normalized, normalized.signals)
        
        # Layer 4: Detection (Hardened)
        detection_result = detection_engine.predict(features, artifact.channel, suppress_rules)
        
        # Layer 5: Explainability
        reasons = generate_explanations(features, detection_result, artifact.channel)
        
        # Layer 6: Update DB (Using save_detection with INSERT OR REPLACE)
        await save_detection({
            "scan_id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": artifact.channel,
            "input_preview": artifact.input_preview,
            "input_hash": artifact.input_hash,
            "normalized_url": normalized.normalized_url,
            "risk_score": detection_result["risk_score"],
            "severity": detection_result["severity"],
            "is_phishing": 1 if detection_result["is_phishing"] else 0,
            "reasons_json": json.dumps(reasons),
            "features_json": json.dumps(features),
            "latency_ms": 0, # Enriched latency is async
            "model_versions_json": json.dumps(detection_result["model_versions"]),
        })
        print(f"[INFO] Scan {scan_id} enriched successfully.")
    except Exception as e:
        print(f"[ERROR] Enrichment failed for {scan_id}: {e}")

async def run_pipeline(url: str = None, text: str = None, html_body: str = None,
                       channel: str = "url", metadata: dict = None,
                       background_tasks: BackgroundTasks = None,
                       suppress_rules: list = None) -> dict:
    """
    Execute the VIGILANT v2.0 Pipeline (Preliminary Stage).
    Returns a result in <50ms and schedules deep enrichment.
    """
    start_time = time.perf_counter()
    scan_id = str(uuid.uuid4())[:12]
    
    # Layer 1: Ingestion
    artifact = ingest(
        url=url,
        text=text,
        html_body=html_body,
        channel=channel,
        metadata=metadata,
    )
    
    # Layer 2: Fast Normalization (Skip expansion for low latency)
    normalized = await normalize(artifact, skip_expansion=True)
    
    # Layer 3: Feature Extraction
    features = extract_features(normalized, normalized.signals)
    
    # Layer 4: Preliminary Detection
    detection_result = detection_engine.predict(features, channel, suppress_rules)
    
    # Layer 5: Explainability
    reasons = generate_explanations(features, detection_result, channel)
    
    # Latency check (Target: <50ms)
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    # Build Preliminary Response
    response = {
        "scan_id": scan_id,
        "risk_score": detection_result["risk_score"],
        "severity": detection_result["severity"],
        "is_phishing": detection_result["is_phishing"],
        "reasons": reasons,
        "features": features,
        "normalized_url": normalized.normalized_url,
        "channel": channel,
        "latency_ms": latency_ms,
        "processing_state": ProcessingState.PRELIMINARY if normalized.signals.get('expansion_pending') else ProcessingState.FINAL,
        "model_versions": detection_result["model_versions"],
    }
    
    # Layer 6: Store Preliminary Result
    try:
        await save_detection({
            "scan_id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "input_preview": artifact.input_preview,
            "input_hash": artifact.input_hash,
            "normalized_url": normalized.normalized_url,
            "risk_score": detection_result["risk_score"],
            "severity": detection_result["severity"],
            "is_phishing": 1 if detection_result["is_phishing"] else 0,
            "reasons_json": json.dumps(reasons),
            "features_json": json.dumps(features),
            "latency_ms": latency_ms,
            "model_versions_json": json.dumps(detection_result["model_versions"]),
        })
    except Exception as e:
        print(f"[WARN] Preliminary save failed: {e}")
    
    # Schedule Enrichment if pending
    if background_tasks and normalized.signals.get('expansion_pending'):
        background_tasks.add_task(enrich_detection, scan_id, artifact, suppress_rules)
        response["processing_state"] = ProcessingState.ENRICHING
    
    return response
