"""SENTINEL - Database Layer (SQLite with aiosqlite)"""
import aiosqlite
from app.core.config import settings

DB_PATH = settings.DB_PATH


async def get_db():
    """Get an aiosqlite database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize the database and create tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                merchant_id TEXT NOT NULL,
                transaction_id TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'INR',
                payment_method TEXT NOT NULL,
                customer_id TEXT,
                fraud_score REAL NOT NULL,
                chargeback_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                fraud_type TEXT NOT NULL,
                is_fraudulent INTEGER NOT NULL,
                recommended_action TEXT NOT NULL,
                reasons_json TEXT,
                features_json TEXT,
                chargeback_evidence TEXT,
                latency_ms REAL,
                model_versions_json TEXT,
                device_fingerprint TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id TEXT NOT NULL,
                transaction_id TEXT,
                outcome TEXT NOT NULL,
                notes TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_timestamp ON assessments(timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_risk ON assessments(risk_level)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_merchant ON assessments(merchant_id)
        """)
        await db.commit()


async def save_assessment(assessment: dict):
    """Save a fraud risk assessment to the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO assessments 
            (assessment_id, timestamp, merchant_id, transaction_id, amount, currency,
             payment_method, customer_id, fraud_score, chargeback_score, risk_level,
             fraud_type, is_fraudulent, recommended_action, reasons_json, features_json,
             chargeback_evidence, latency_ms, model_versions_json, device_fingerprint)
            VALUES (:assessment_id, :timestamp, :merchant_id, :transaction_id, :amount,
                    :currency, :payment_method, :customer_id, :fraud_score, :chargeback_score,
                    :risk_level, :fraud_type, :is_fraudulent, :recommended_action, :reasons_json,
                    :features_json, :chargeback_evidence, :latency_ms, :model_versions_json,
                    :device_fingerprint)
        """, assessment)
        await db.commit()


async def save_outcome(outcome: dict):
    """Save chargeback outcome feedback."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO outcomes (assessment_id, transaction_id, outcome, notes, timestamp)
            VALUES (:assessment_id, :transaction_id, :outcome, :notes, :timestamp)
        """, outcome)
        await db.commit()


async def get_assessments(page: int = 1, page_size: int = 20, risk_level: str = None, merchant_id: str = None):
    """Get paginated assessment history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        where_clauses = []
        params = {}
        if risk_level:
            where_clauses.append("risk_level = :risk_level")
            params["risk_level"] = risk_level
        if merchant_id:
            where_clauses.append("merchant_id = :merchant_id")
            params["merchant_id"] = merchant_id
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        count_row = await db.execute_fetchall(
            f"SELECT COUNT(*) as cnt FROM assessments {where_sql}", params
        )
        total = count_row[0][0] if count_row else 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        rows = await db.execute_fetchall(
            f"""SELECT * FROM assessments {where_sql}
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset""",
            params
        )
        return [dict(row) for row in rows], total


async def get_stats():
    """Get dashboard statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        row = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM assessments")
        total = row[0][0] if row else 0

        row = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM assessments WHERE is_fraudulent = 1")
        frauds = row[0][0] if row else 0

        row = await db.execute_fetchall("SELECT COALESCE(SUM(amount), 0) as total FROM assessments WHERE is_fraudulent = 1")
        amount_protected = round(row[0][0], 2) if row else 0.0

        row = await db.execute_fetchall("SELECT AVG(latency_ms) as avg_lat FROM assessments")
        avg_latency = round(row[0][0], 2) if row and row[0][0] else 0.0

        fp_row = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM outcomes WHERE outcome = 'legitimate'"
        )
        fp_count = fp_row[0][0] if fp_row else 0
        fp_rate = round((fp_count / frauds * 100) if frauds > 0 else 0.0, 2)

        risk_rows = await db.execute_fetchall(
            "SELECT risk_level, COUNT(*) as cnt FROM assessments GROUP BY risk_level"
        )
        risk_dist = {row[0]: row[1] for row in risk_rows}

        pm_rows = await db.execute_fetchall(
            "SELECT payment_method, COUNT(*) as cnt FROM assessments GROUP BY payment_method"
        )
        pm_dist = {row[0]: row[1] for row in pm_rows}

        trend_rows = await db.execute_fetchall("""
            SELECT DATE(timestamp) as date, COUNT(*) as total,
                   SUM(CASE WHEN is_fraudulent = 1 THEN 1 ELSE 0 END) as frauds,
                   SUM(CASE WHEN is_fraudulent = 1 THEN amount ELSE 0 END) as amount_blocked
            FROM assessments
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        """)
        trend = [{"date": row[0], "total": row[1], "frauds": row[2], "amount_blocked": row[3]} for row in trend_rows]

        return {
            "total_assessments": total,
            "frauds_detected": frauds,
            "total_amount_protected": amount_protected,
            "avg_latency_ms": avg_latency,
            "false_positive_rate": fp_rate,
            "risk_distribution": risk_dist,
            "payment_method_distribution": pm_dist,
            "recent_trend": list(reversed(trend)),
        }
