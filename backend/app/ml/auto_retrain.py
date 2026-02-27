"""VIGILANT - Adaptive Retraining Trigger

Layer 5 & 6: Trigger-based Retraining & Incremental Dataset Builder.
Runs periodically. If enough curated APPROVED samples exist, it triggers
the sliding window build via data_shim, retrains, and saves shadow models.
"""
import os
import sys
import sqlite3
import logging
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'threat_intel.db')
ML_DIR = os.path.dirname(__file__)

RETRAIN_THRESHOLD = 50 # In prod this would be 10000

def check_trigger() -> bool:
    if not os.path.exists(DB_PATH):
        return False
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM curated_training_pool WHERE status = 'APPROVED'")
        count = c.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    finally:
        conn.close()
    
    logger.info(f"Retrain check: {count} APPROVED samples found (Threshold: {RETRAIN_THRESHOLD}).")
    return count >= RETRAIN_THRESHOLD

def execute_retrain_pipeline():
    logger.info("TRIGGER MET: Promoting dataset and running Sliding-Window training...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(ML_DIR, '..', '..')
    
    # 1. Build Canonical Artifact (Now includes Curated DB)
    logger.info("=> Running data_shim.py")
    subprocess.run(["python", os.path.join(ML_DIR, "data_shim.py")], check=True, env=env)
    
    # 2. Train URL Model
    logger.info("=> Running train_url_model.py")
    subprocess.run(["python", os.path.join(ML_DIR, "train_url_model.py")], check=True, env=env)
    
    # 3. Train NLP Model
    logger.info("=> Running train_nlp_model.py")
    subprocess.run(["python", os.path.join(ML_DIR, "train_nlp_model.py")], check=True, env=env)
    
    logger.info("Retraining successful! New models saved.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if check_trigger():
        execute_retrain_pipeline()
    else:
        logger.info("Trigger not met. Skipping retraining.")
