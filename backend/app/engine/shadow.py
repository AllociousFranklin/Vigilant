"""VIGILANT - Shadow Mode Telemetry

Logs inference deltas between the primary model and shadow model
for safe Continuous Learning deployments.
"""
import sqlite3
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'threat_intel.db')

def init_shadow_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS shadow_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            url TEXT,
            channel TEXT,
            primary_risk_score REAL,
            primary_severity TEXT,
            shadow_risk_score REAL,
            shadow_severity TEXT,
            delta_score REAL,
            diverged BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def log_shadow_inference(scan_id: str, url: str, channel: str, 
                         primary_res: dict, shadow_res: dict):
    init_shadow_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    p_score = primary_res.get("risk_score", 0.0)
    s_score = shadow_res.get("risk_score", 0.0)
    
    # Safely handle Enums (Severity is an Enum in the primary pipeline)
    p_sev = primary_res.get("severity")
    s_sev = shadow_res.get("severity")
    p_sev_str = p_sev.name if hasattr(p_sev, 'name') else str(p_sev)
    s_sev_str = s_sev.name if hasattr(s_sev, 'name') else str(s_sev)
    
    # Check if they diverged meaningfully (different severity bucket)
    diverged = 1 if p_sev_str != s_sev_str else 0
    delta = abs(p_score - s_score)
    
    try:
        c.execute('''
            INSERT INTO shadow_telemetry 
            (scan_id, url, channel, primary_risk_score, primary_severity, 
             shadow_risk_score, shadow_severity, delta_score, diverged)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (scan_id, url, channel, p_score, p_sev_str, s_score, s_sev_str, delta, diverged))
        conn.commit()
        
        if diverged:
            logger.warning(f"[SHADOW MODE] Inference Divergence on {url} (Primary: {p_sev_str}, Shadow: {s_sev_str})")
            
    except Exception as e:
        logger.error(f"Failed to log shadow telemetry: {e}")
    finally:
        conn.close()
