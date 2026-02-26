"""VIGILANT - Pydantic Schemas for API Request/Response"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Channel(str, Enum):
    URL = "url"
    EMAIL = "email"
    SMS = "sms"
    HTML = "html"


class ProcessingState(str, Enum):
    PRELIMINARY = "PRELIMINARY"
    ENRICHING = "ENRICHING"
    FINAL = "FINAL"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScanRequest(BaseModel):
    """Input payload for phishing scan."""
    url: Optional[str] = Field(None, description="URL to scan")
    text: Optional[str] = Field(None, description="Email or SMS text content")
    html_body: Optional[str] = Field(None, description="Raw HTML body (optional)")
    channel: Channel = Field(Channel.URL, description="Source channel")
    metadata: Optional[dict] = Field(None, description="Additional metadata (org_id, timestamp, etc.)")
    suppress_rules: Optional[list[str]] = Field(default_factory=list, description="List of Rule IDs to suppress")


class ReasonDetail(BaseModel):
    """Single explainability reason."""
    reason: str
    confidence: float = Field(..., ge=0, le=100)
    category: str


class ScanResponse(BaseModel):
    """Output payload from phishing scan."""
    scan_id: str
    risk_score: float = Field(..., ge=0, le=100)
    severity: Severity
    is_phishing: bool
    reasons: list[ReasonDetail]
    overrides: Optional[list[dict]] = None
    features: Optional[dict] = None
    normalized_url: Optional[str] = None
    channel: Channel
    latency_ms: float
    processing_state: ProcessingState = Field(ProcessingState.FINAL)
    model_versions: Optional[dict] = None


class FeedbackRequest(BaseModel):
    """Analyst feedback on a detection."""
    scan_id: str
    verdict: str = Field(..., description="'false_positive', 'confirmed_threat', or 'uncertain'")
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Confirmation of feedback submission."""
    success: bool
    message: str


class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_scans: int
    threats_detected: int
    avg_latency_ms: float
    false_positive_rate: float
    severity_distribution: dict
    channel_distribution: dict
    recent_trend: list[dict]


class HistoryItem(BaseModel):
    """Single detection history entry."""
    scan_id: str
    timestamp: str
    channel: str
    risk_score: float
    severity: str
    is_phishing: bool
    input_preview: str
    reasons: list[ReasonDetail]
    latency_ms: float


class HistoryResponse(BaseModel):
    """Paginated detection history."""
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
