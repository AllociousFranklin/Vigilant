"""SENTINEL - Application Configuration"""
import os

class Settings:
    APP_NAME: str = "SENTINEL"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI Risk Manager — Payment Fraud & Chargeback Defense for Indian BFSI"

    # API
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ]

    # Database
    DB_PATH: str = os.getenv("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sentinel.db")))

    # ML Models
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "models")
    FRAUD_MODEL_PATH: str = os.path.join(MODEL_DIR, "fraud_classifier.joblib")
    CHARGEBACK_MODEL_PATH: str = os.path.join(MODEL_DIR, "chargeback_classifier.joblib")

    # Risk thresholds
    RISK_THRESHOLDS: dict = {
        "LOW": (0, 30),
        "MEDIUM": (30, 60),
        "HIGH": (60, 85),
        "CRITICAL": (85, 100),
    }

    # Ensemble weights
    FRAUD_MODEL_WEIGHT: float = 0.65
    ANOMALY_WEIGHT: float = 0.35

    # Rate limiting
    RATE_LIMIT: int = 100

settings = Settings()
