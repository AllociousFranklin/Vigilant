"""VIGILANT - Threat Data Curation Layer

Handles the transition of feeds and high-confidence detections
into the curated_training_pool for adaptive retraining.
"""
import sqlite3
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

from app.engine.detector import detection_engine

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'threat_intel.db')


def init_curation_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS curated_training_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_hash TEXT NOT NULL,
            url TEXT,
            text_content TEXT,
            features_json TEXT NOT NULL,
            label INTEGER NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL, -- 'PENDING', 'APPROVED', 'REJECTED'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_to_pool(input_hash: str, features: Dict[str, Any], label: int, source: str, status: str = 'PENDING', url: str = None, text_content: str = None):
    init_curation_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO curated_training_pool 
            (input_hash, url, text_content, features_json, label, source, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (input_hash, url, text_content, json.dumps(features), label, source, status))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to add to curation pool: {e}")
    finally:
        conn.close()

def validate_pending_pool():
    """
    Layer 4: Quality Filtering.
    Evaluates PENDING samples. If they pass structural sanity checks,
    they are promoted to APPROVED.
    """
    init_curation_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, features_json, label, source FROM curated_training_pool WHERE status = 'PENDING'")
    rows = c.fetchall()
    
    approved_count = 0
    rejected_count = 0
    
    for row_id, features_json, label, source in rows:
        try:
            features = json.loads(features_json)
            
            # Rule 1: Missing core features?
            if 'url_length' not in features and 'nlp_urgency_score' not in features:
                c.execute("UPDATE curated_training_pool SET status = 'REJECTED' WHERE id = ?", (row_id,))
                rejected_count += 1
                continue
                
            # Rule 2: Validation of PhishTank inputs
            if source == 'PhishTank' and label == 1:
                # Does the feature extractor actually see anything suspicious? 
                # (Prevents poisoning if PhishTank gets hijacked or lists google.com)
                if features.get('url_length', 0) > 10 or features.get('url_suspicious_tld', 0) == 1 or features.get('struct_redirection_chain_len', 0) > 0:
                     c.execute("UPDATE curated_training_pool SET status = 'APPROVED' WHERE id = ?", (row_id,))
                     approved_count += 1
                else:
                     logger.warning(f"PhishTank sample {row_id} lacks structural evidence. Keeping PENDING/REJECTED.")
                     c.execute("UPDATE curated_training_pool SET status = 'REJECTED' WHERE id = ?", (row_id,))
                     rejected_count += 1
            else:
                # Other sources (e.g. analyst feedback) can be auto-approved or require human intervention.
                # For now, require manual analyst approval via API for non-PhishTank sources.
                pass
                
        except Exception as e:
             logger.error(f"Error validating row {row_id}: {e}")
             
    conn.commit()
    conn.close()
    
    logger.info(f"Pool Validation: {approved_count} approved, {rejected_count} rejected.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_curation_db()
    validate_pending_pool()
