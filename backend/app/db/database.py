"""VIGILANT - Database Layer (SQLite with aiosqlite)"""
import aiosqlite
import os
from app.core.config import settings


DB_PATH = settings.DB_PATH


async def init_db():
    """Initialize the database and create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                scan_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                channel TEXT NOT NULL,
                input_preview TEXT,
                input_hash TEXT,
                normalized_url TEXT,
                risk_score REAL NOT NULL,
                severity TEXT NOT NULL,
                is_phishing INTEGER NOT NULL,
                reasons_json TEXT,
                features_json TEXT,
                latency_ms REAL,
                model_versions_json TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                verdict TEXT NOT NULL,
                notes TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (scan_id) REFERENCES detections(scan_id)
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_detections_severity ON detections(severity)
        """)
        await db.commit()


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def save_detection(detection: dict):
    """Save a detection result to the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO detections (scan_id, timestamp, channel, input_preview, input_hash,
                                     normalized_url, risk_score, severity, is_phishing,
                                     reasons_json, features_json, latency_ms, model_versions_json)
            VALUES (:scan_id, :timestamp, :channel, :input_preview, :input_hash,
                    :normalized_url, :risk_score, :severity, :is_phishing,
                    :reasons_json, :features_json, :latency_ms, :model_versions_json)
        """, detection)
        await db.commit()


async def save_feedback(feedback: dict):
    """Save analyst feedback."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO feedback (scan_id, verdict, notes, timestamp)
            VALUES (:scan_id, :verdict, :notes, :timestamp)
        """, feedback)
        await db.commit()


async def get_detections(page: int = 1, page_size: int = 20, severity: str = None, channel: str = None):
    """Get paginated detection history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        where_clauses = []
        params = {}
        
        if severity:
            where_clauses.append("severity = :severity")
            params["severity"] = severity
        if channel:
            where_clauses.append("channel = :channel")
            params["channel"] = channel
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Get total count
        count_row = await db.execute_fetchall(
            f"SELECT COUNT(*) as cnt FROM detections {where_sql}", params
        )
        total = count_row[0][0] if count_row else 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        
        rows = await db.execute_fetchall(
            f"""SELECT * FROM detections {where_sql}
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset""",
            params
        )
        
        return [dict(row) for row in rows], total


async def get_stats():
    """Get dashboard statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Total scans
        row = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM detections")
        total_scans = row[0][0] if row else 0
        
        # Threats detected
        row = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM detections WHERE is_phishing = 1")
        threats = row[0][0] if row else 0
        
        # Average latency
        row = await db.execute_fetchall("SELECT AVG(latency_ms) as avg_lat FROM detections")
        avg_latency = round(row[0][0], 2) if row and row[0][0] else 0.0
        
        # False positive rate (from feedback)
        fp_row = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM feedback WHERE verdict = 'false_positive'"
        )
        fp_count = fp_row[0][0] if fp_row else 0
        fp_rate = round((fp_count / threats * 100) if threats > 0 else 0.0, 2)
        
        # Severity distribution
        sev_rows = await db.execute_fetchall(
            "SELECT severity, COUNT(*) as cnt FROM detections GROUP BY severity"
        )
        severity_dist = {row[0]: row[1] for row in sev_rows}
        
        # Channel distribution
        chan_rows = await db.execute_fetchall(
            "SELECT channel, COUNT(*) as cnt FROM detections GROUP BY channel"
        )
        channel_dist = {row[0]: row[1] for row in chan_rows}
        
        # Recent trend (last 7 days aggregated by date)
        trend_rows = await db.execute_fetchall("""
            SELECT DATE(timestamp) as date, COUNT(*) as total,
                   SUM(CASE WHEN is_phishing = 1 THEN 1 ELSE 0 END) as threats
            FROM detections
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        """)
        trend = [{"date": row[0], "total": row[1], "threats": row[2]} for row in trend_rows]
        
        return {
            "total_scans": total_scans,
            "threats_detected": threats,
            "avg_latency_ms": avg_latency,
            "false_positive_rate": fp_rate,
            "severity_distribution": severity_dist,
            "channel_distribution": channel_dist,
            "recent_trend": list(reversed(trend)),
        }
