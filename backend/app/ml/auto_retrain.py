"""SENTINEL - Adaptive Retraining Trigger

Monitors outcomes database and periodically retrains fraud and chargeback models.
"""
import os
import sys
import sqlite3
import logging
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'sentinel.db')
ML_DIR = os.path.dirname(__file__)

RETRAIN_THRESHOLD = 50

def check_trigger() -> bool:
    if not os.path.exists(DB_PATH):
        return False
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM outcomes")
        count = c.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    finally:
        conn.close()
    
    logger.info(f"Retrain check: {count} outcomes found (Threshold: {RETRAIN_THRESHOLD}).")
    return count >= RETRAIN_THRESHOLD

def execute_retrain_pipeline():
    logger.info("TRIGGER MET: Retraining SENTINEL ML models...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(ML_DIR, '..', '..')
    
    logger.info("=> Running data_shim.py")
    subprocess.run(["python", os.path.join(ML_DIR, "data_shim.py")], check=True, env=env)
    
    logger.info("=> Running train_fraud_model.py")
    subprocess.run(["python", os.path.join(ML_DIR, "train_fraud_model.py")], check=True, env=env)
    
    logger.info("=> Running train_chargeback_model.py")
    subprocess.run(["python", os.path.join(ML_DIR, "train_chargeback_model.py")], check=True, env=env)
    
    logger.info("Retraining successful! New models saved.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if check_trigger():
        execute_retrain_pipeline()
    else:
        logger.info("Trigger not met. Skipping retraining.")
