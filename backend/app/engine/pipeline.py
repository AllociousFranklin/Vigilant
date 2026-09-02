"""SENTINEL Engine - Pipeline Orchestrator

Chains all 6 layers together and measures latency:
1. Ingestion & Validation
2. Profile & Behavioral Enrichment
3. 30-Dimension Feature Extraction
4. Ensemble Fraud & Chargeback ML Scoring
5. Policy Enforcement & Fraud Taxonomy
6. Explainability & Chargeback Evidence Builder
"""
import time
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any

from app.api.schemas import (
    TransactionRequest, DetectionBlock, AssessmentBlock, DecisionBlock,
    ReasonDetail
)
from app.engine.ingestion import ingest
from app.engine.transaction_enricher import enrich
from app.engine.features import extract_all_features
from app.engine.detector import fraud_engine
from app.engine.policy import policy_engine
from app.engine.explainer import generate_explanations, generate_chargeback_evidence
from app.engine.shadow import log_shadow_inference
from app.db.database import save_assessment


async def score_transaction(request: TransactionRequest) -> dict:
    """
    Execute full SENTINEL fraud risk assessment pipeline.
    Expected latency: sub-15ms.
    """
    start_time = time.perf_counter()
    assessment_id = f"asm_{uuid.uuid4().hex[:12]}"
    now_ts = datetime.now(timezone.utc).isoformat()

    # Layer 1: Ingestion
    ingested = ingest(request)

    # Layer 2: Transaction & Profile Enrichment
    enriched = enrich(ingested)

    # Layer 3: Feature Extraction (30 dimensions)
    enrichment_dict = {
        'amount': enriched.amount,
        'merchant_avg_txn': enriched.merchant_avg_txn,
        'merchant_std_txn': enriched.merchant_std_txn,
        'merchant_fraud_rate_30d': enriched.merchant_fraud_rate_30d,
        'merchant_vintage_days': enriched.merchant_vintage_days,
        'merchant_category': enriched.merchant_category,
        'customer_account_age_days': enriched.customer_account_age_days,
        'customer_total_txns': enriched.customer_total_txns,
        'customer_dispute_rate': enriched.customer_dispute_rate,
        'customer_email': enriched.customer_email,
        'phone_verified': enriched.phone_verified,
        'device_fingerprint_new': enriched.device_fingerprint_new,
        'ip_risk_score': enriched.ip_risk_score,
        'geo_distance_km': enriched.geo_distance_km,
        'billing_shipping_mismatch': enriched.billing_shipping_mismatch,
        'txn_count_1h': enriched.txn_count_1h,
        'txn_count_24h': enriched.txn_count_24h,
        'distinct_merchants_1h': enriched.distinct_merchants_1h,
        'amount_sum_24h': enriched.amount_sum_24h,
        'hour_of_day': enriched.hour_of_day,
        'is_weekend': enriched.is_weekend,
        'days_since_last_txn': enriched.days_since_last_txn,
        'payment_method': enriched.payment_method,
        'is_international': enriched.is_international,
        'is_first_time_card': enriched.is_first_time_card,
        'card_bin': enriched.card_bin,
    }
    features = extract_all_features(enrichment_dict)

    # Layer 4: Ensemble ML Inference & Overrides
    ml_result = fraud_engine.predict(
        features=features,
        card_bin=ingested.card_bin,
        device_fingerprint=ingested.device_fingerprint
    )

    # Layer 5: Policy Assessment
    policy_result = policy_engine.assess(
        features=features,
        fraud_score=ml_result["fraud_score"],
        chargeback_score=ml_result["chargeback_score"],
        overrides=ml_result["overrides"]
    )

    # Layer 6: Explainability & Chargeback Evidence Dossier
    combined_context = {**ml_result, **policy_result}
    reasons = generate_explanations(features, combined_context)

    evidence_context = {
        'transaction_id': ingested.transaction_id,
        'merchant_id': ingested.merchant_id,
        'amount': ingested.amount,
        'currency': ingested.currency,
        'timestamp': now_ts,
        'fraud_score': policy_result["fraud_score"],
        'chargeback_score': policy_result["chargeback_score"],
        'fraud_type': policy_result["fraud_type"].value,
        'risk_level': policy_result["risk_level"].value,
    }
    evidence_text = generate_chargeback_evidence(evidence_context, reasons)

    # Measure latency
    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    # Blocks construction
    detection_block = DetectionBlock(
        features=features,
        enrichment_signals=enriched.signals
    )

    assessment_block = AssessmentBlock(
        fraud_score=policy_result["fraud_score"],
        chargeback_score=policy_result["chargeback_score"],
        risk_level=policy_result["risk_level"],
        fraud_type=policy_result["fraud_type"],
        is_fraudulent=policy_result["is_fraudulent"],
        reasons=reasons,
        confidence_band=policy_result["confidence_band"],
        policy_version=policy_result["policy_version"],
        model_version=f"fraud:{ml_result['model_versions']['fraud_model']},cb:{ml_result['model_versions']['chargeback_model']}"
    )

    decision_block = DecisionBlock(
        recommended_action=policy_result["recommended_action"],
        chargeback_evidence=evidence_text
    )

    # Shadow Mode Telemetry (Async-safe logging)
    try:
        log_shadow_inference(
            assessment_id=assessment_id,
            transaction_id=ingested.transaction_id,
            payment_method=ingested.payment_method,
            primary_res=policy_result,
            shadow_res=policy_result
        )
    except Exception as e:
        print(f"[WARN] Shadow mode telemetry skipped: {e}")

    # Persistence to SQLite
    try:
        await save_assessment({
            "assessment_id": assessment_id,
            "timestamp": now_ts,
            "merchant_id": ingested.merchant_id,
            "transaction_id": ingested.transaction_id,
            "amount": ingested.amount,
            "currency": ingested.currency,
            "payment_method": ingested.payment_method,
            "customer_id": ingested.customer_id,
            "fraud_score": policy_result["fraud_score"],
            "chargeback_score": policy_result["chargeback_score"],
            "risk_level": policy_result["risk_level"].value,
            "fraud_type": policy_result["fraud_type"].value,
            "is_fraudulent": 1 if policy_result["is_fraudulent"] else 0,
            "recommended_action": policy_result["recommended_action"].value,
            "reasons_json": json.dumps([r.model_dump() for r in reasons]),
            "features_json": json.dumps(features),
            "chargeback_evidence": evidence_text,
            "latency_ms": latency_ms,
            "model_versions_json": json.dumps(ml_result["model_versions"]),
            "device_fingerprint": ingested.device_fingerprint or "unknown_device",
        })
    except Exception as e:
        print(f"[WARN] Assessment database save failed: {e}")

    return {
        "assessment_id": assessment_id,
        "merchant_id": ingested.merchant_id,
        "amount": ingested.amount,
        "currency": ingested.currency,
        "latency_ms": latency_ms,
        "detection": detection_block,
        "assessment": assessment_block,
        "decision": decision_block,
        # Top-level bridge fields
        "fraud_score": policy_result["fraud_score"],
        "chargeback_score": policy_result["chargeback_score"],
        "risk_level": policy_result["risk_level"],
        "is_fraudulent": policy_result["is_fraudulent"],
        "reasons": reasons,
        "features": features,
    }
