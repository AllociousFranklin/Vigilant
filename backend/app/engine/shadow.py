"""SENTINEL - Shadow Mode Telemetry

Logs inference deltas between the primary model and shadow model
for safe Canary and Continuous Learning deployments.
"""
import sqlite3
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DB_PATH


def init_shadow_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS shadow_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transaction_id TEXT,
            payment_method TEXT,
            primary_fraud_score REAL,
            primary_risk_level TEXT,
            shadow_fraud_score REAL,
            shadow_risk_level TEXT,
            delta_score REAL,
            diverged BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()


def log_shadow_inference(assessment_id: str, transaction_id: str, payment_method: str, 
                         primary_res: dict, shadow_res: dict):
    """Log inference comparison between primary and candidate shadow models."""
    try:
        init_shadow_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        p_score = float(primary_res.get("fraud_score", 0.0))
        s_score = float(shadow_res.get("fraud_score", 0.0))

        p_lvl = primary_res.get("risk_level")
        s_lvl = shadow_res.get("risk_level")
        p_lvl_str = p_lvl.value if hasattr(p_lvl, 'value') else str(p_lvl)
        s_lvl_str = s_lvl.value if hasattr(s_lvl, 'value') else str(s_lvl)

        diverged = 1 if p_lvl_str != s_lvl_str else 0
        delta = abs(p_score - s_score)

        c.execute('''
            INSERT INTO shadow_telemetry 
            (assessment_id, transaction_id, payment_method, primary_fraud_score, primary_risk_level, 
             shadow_fraud_score, shadow_risk_level, delta_score, diverged)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (assessment_id, transaction_id, payment_method, p_score, p_lvl_str, s_score, s_lvl_str, delta, diverged))
        conn.commit()
        conn.close()

        if diverged:
            logger.info(f"[SHADOW TELEMETRY] Divergence on txn {transaction_id}: Primary={p_lvl_str}, Shadow={s_lvl_str}")

    except Exception as e:
        logger.warning(f"Shadow telemetry write skipped: {e}")
