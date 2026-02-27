"""VIGILANT - PhishTank Threat Feed Ingestion Service

Periodically pulls verified phishing URLs from PhishTank or other threat intel sources
and stores them locally for real-time inference enrichment.
"""
import sqlite3
import urllib.request
import json
import logging
import os
from datetime import datetime
import urllib.parse

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure the DB directory exists
DB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'threat_intel.db')


def init_db():
    """Initialize the local Threat Intel database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Layer 1 Storage: Verified feeds only
    c.execute('''
        CREATE TABLE IF NOT EXISTS threat_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT NOT NULL,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(url)
        )
    ''')
    
    # Index for ultra-fast real-time lookup during detection
    c.execute('CREATE INDEX IF NOT EXISTS idx_domain ON threat_feed(domain)')
    
    conn.commit()
    conn.close()


def ingest_feed():
    """
    Simulated Ingestion Logic.
    In production, this downloads the latest JSON from PhishTank API.
    Since we don't have an API key, we will simulate a daily pull of common bad domains.
    """
    init_db()
    
    logger.info("Starting Threat Feed Ingestion...")
    
    # Simulated PhishTank Feed
    mock_feed = [
        "https://evil-login.net/auth",
        "http://paypal-verification-update.com/secure",
        "https://netflix-billing-issue-1394.info",
        "http://chase-bank-alert.xyz/login",
        "https://amazon-prime-refunds.net",
        "https://appleid-locked-recovery.com"
    ]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    added = 0
    for url in mock_feed:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.hostname or ""
            
            c.execute('''
                INSERT OR IGNORE INTO threat_feed (domain, url, source)
                VALUES (?, ?, ?)
            ''', (domain, url, 'PhishTank_Simulated'))
            
            if c.rowcount > 0:
                added += 1
        except Exception as e:
            logger.error(f"Error parsing feed URL {url}: {e}")
            
    conn.commit()
    conn.close()
    
    logger.info(f"Ingestion complete. Added {added} new indicators to local store.")


def check_domain(domain: str) -> bool:
    """Ultra-fast O(1) lookup against the local SQLite index."""
    if not domain:
        return False
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT 1 FROM threat_feed WHERE domain = ? LIMIT 1', (domain,))
        result = c.fetchone()
        conn.close()
        return bool(result)
    except sqlite3.OperationalError:
        # DB might not be initialized yet during first boot
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_feed()
