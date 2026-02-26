"""VIGILANT - Application Configuration"""
import os

class Settings:
    APP_NAME: str = "VIGILANT"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Real-Time AI/ML-Based Phishing Detection and Prevention System"
    
    # API
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://vigilant-phishing.vercel.app",
        "*",
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'vigilant.db'))}")
    DB_PATH: str = os.getenv("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "vigilant.db")))
    
    # ML Models
    MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "models")
    URL_MODEL_PATH: str = os.path.join(MODEL_DIR, "url_classifier.joblib")
    NLP_MODEL_PATH: str = os.path.join(MODEL_DIR, "nlp_classifier.joblib")
    
    # Detection thresholds
    RISK_THRESHOLDS: dict = {
        "LOW": (0, 30),
        "MEDIUM": (30, 60),
        "HIGH": (60, 85),
        "CRITICAL": (85, 100),
    }
    
    # Ensemble weights
    URL_MODEL_WEIGHT: float = 0.6
    NLP_MODEL_WEIGHT: float = 0.4
    
    # Short URL expansion timeout
    SHORT_URL_TIMEOUT: float = 2.0
    
    # Rate limiting
    RATE_LIMIT: int = 100  # requests per minute


settings = Settings()
