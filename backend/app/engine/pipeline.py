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
from app.engine.policy import policy_engine
from app.db.database import save_detection


from fastapi import BackgroundTasks
from app.api.schemas import ProcessingState, Channel, DetectionBlock, AssessmentBlock, DecisionBlock, EnforcementMode

# ... (omitting enrich_detection changes for a moment, let's focus on run_pipeline first, but we must update both conceptually)

def get_action_policy(severity_score: float, channel: str) -> dict:
    """Determine the recommended action and enforcement mode based on channel and severity."""
    action = "ALLOW"
    
    if channel == "url" or channel == "html":
        mode = EnforcementMode.PREVENTIVE
        if severity_score >= 85:
            action = "BLOCK"
        elif severity_score >= 65:
            action = "WARN"
    else:
        mode = EnforcementMode.ADVISORY
        if severity_score >= 85:
            action = "RECOMMEND_DELETION"
        elif severity_score >= 65:
            action = "HIGHLIGHT_WARNING"
        elif severity_score >= 35:
            action = "FLAG_FOR_REVIEW"
            
    return {"recommended_action": action, "enforcement_mode": mode}


async def enrich_detection(scan_id: str, artifact, suppress_rules: list = None):
    """
    Background Task: Perform deep analysis (URL expansion) and update detection.
    This fulfills the 'Enriched' part of the confidence contract.
    """
    try:
        # Layer 2: Full Normalization (including expansion)
        normalized = await normalize(artifact, skip_expansion=False)
        
        # Layer 3: Feature Extraction
        features = extract_features(normalized, normalized.signals)
        
        # Layer 4: ML Detection (Base)
        ml_result = detection_engine.predict(features, artifact.channel, suppress_rules)
        
        # Layer 5: Policy Assessment
        assessment_result = policy_engine.assess(features, ml_result["risk_score"], artifact.channel)
        
        # Explainability
        reasons = generate_explanations(features, {**ml_result, **assessment_result}, artifact.channel)
        
        # Layer 6: Update DB
        await save_detection({
            "scan_id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": artifact.channel,
            "input_preview": artifact.input_preview,
            "input_hash": artifact.input_hash,
            "normalized_url": normalized.normalized_url,
            "risk_score": assessment_result["risk_score"],
            "severity": assessment_result["severity"].name,
            "is_phishing": 1 if assessment_result["is_phishing"] else 0,
            "reasons_json": json.dumps(reasons),
            "features_json": json.dumps(features),
            "latency_ms": 0, # Enriched latency is async
            "model_versions_json": json.dumps(ml_result["model_versions"]),
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
    artifact = ingest(url=url, text=text, html_body=html_body, channel=channel, metadata=metadata)
    
    # Layer 2: Fast Normalization
    normalized = await normalize(artifact, skip_expansion=True)
    
    # ---- 1️⃣ DETECTION BLOCK (Raw Signals) ----
    features = extract_features(normalized, normalized.signals)
    
    detection_block = DetectionBlock(
        features=features,
        normalized_url=normalized.normalized_url
    )
    
    # ---- 2️⃣ ASSESSMENT BLOCK (ML + Policy Interpretation) ----
    # 2a. ML Inference
    ml_result = detection_engine.predict(features, channel, suppress_rules)
    
    # 2b. Policy Enforcement (Severity Floors & Threat Typing)
    assessment_result = policy_engine.assess(features, ml_result["risk_score"], channel)
    
    # 2c. Explainability
    # Explainer needs overrides from ML, plus we need to map confidence strings
    combined_context = {**ml_result, **assessment_result}
    raw_reasons = generate_explanations(features, combined_context, channel)
    
    assessment_block = AssessmentBlock(
        risk_score=assessment_result["risk_score"],
        severity=assessment_result["severity"],
        threat_type=assessment_result["threat_type"],
        is_phishing=assessment_result["is_phishing"],
        reasons=raw_reasons,
        confidence_band=assessment_result["confidence_band"],
        policy_version=assessment_result["policy_version"],
        model_version=f"url:{ml_result['model_versions']['url_model']},nlp:{ml_result['model_versions']['nlp_model']}"
    )
    
    # ---- 3️⃣ DECISION BLOCK (Action Recommendation) ----
    action_policy = get_action_policy(assessment_result["risk_score"], channel)
    decision_block = DecisionBlock(
        recommended_action=action_policy["recommended_action"],
        enforcement_mode=action_policy["enforcement_mode"]
    )
    
    # Latency check
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    # Build explicit response dict for router
    response = {
        "scan_id": scan_id,
        "channel": channel,
        "latency_ms": latency_ms,
        "processing_state": ProcessingState.PRELIMINARY if normalized.signals.get('expansion_pending') else ProcessingState.FINAL,
        "detection": detection_block,
        "assessment": assessment_block,
        "decision": decision_block,
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
            "risk_score": assessment_result["risk_score"],
            "severity": assessment_result["severity"].name, # stringify enum
            "is_phishing": 1 if assessment_result["is_phishing"] else 0,
            "reasons_json": json.dumps(raw_reasons),
            "features_json": json.dumps(features),
            "latency_ms": latency_ms,
            "model_versions_json": json.dumps(ml_result["model_versions"]),
        })
    except Exception as e:
        print(f"[WARN] Preliminary save failed: {e}")
    
    # Schedule Enrichment if pending
    if background_tasks and normalized.signals.get('expansion_pending'):
        background_tasks.add_task(enrich_detection, scan_id, artifact, suppress_rules)
        response["processing_state"] = ProcessingState.ENRICHING
    
    return response
