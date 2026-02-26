"""VIGILANT - Pydantic Schemas for API Request/Response"""
from pydantic import BaseModel, Field
from typing import Optional, Any
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
    LOW = "LOW (Advisory)"
    MEDIUM = "MEDIUM (Suspicious)"
    HIGH = "HIGH (Likely Phishing)"
    CRITICAL = "CRITICAL (Block)"


class ThreatType(str, Enum):
    BRAND_PHISHING = "BRAND_PHISHING"
    CALLBACK_PHISHING = "CALLBACK_PHISHING"
    CREDENTIAL_HARVESTING = "CREDENTIAL_HARVESTING"
    MALWARE_DELIVERY = "MALWARE_DELIVERY"
    SUSPICIOUS_PROMOTION = "SUSPICIOUS_PROMOTION"
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"

class EnforcementMode(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    ADVISORY = "ADVISORY"


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
    confidence: Optional[float] = Field(None, ge=0, le=100) # Keep for backward compatibility internally, but we change it to signal_strength
    signal_strength: str = Field(default="MODERATE") # STRONG, MODERATE, WEAK
    category: str


class DetectionBlock(BaseModel):
    """Raw signals extracted from the artifact."""
    features: dict
    normalized_url: Optional[str] = None

class AssessmentBlock(BaseModel):
    """Interpretation of the signals (ML + Policy)."""
    risk_score: float = Field(..., ge=0, le=100)
    severity: Severity
    threat_type: ThreatType
    is_phishing: bool
    reasons: list[ReasonDetail]
    confidence_band: str = Field(default="HIGH_CONFIDENCE")
    policy_version: str
    model_version: str

class DecisionBlock(BaseModel):
    """Final action recommendation."""
    recommended_action: str
    enforcement_mode: EnforcementMode

class ScanResponse(BaseModel):
    """Output payload from phishing scan with explicit Separation of Concerns."""
    scan_id: str
    channel: Channel
    latency_ms: float
    processing_state: ProcessingState = Field(ProcessingState.FINAL)
    
    detection: DetectionBlock
    assessment: AssessmentBlock
    decision: DecisionBlock

    # Keeping old fields for a bit of backward compatibility during transition if needed, but the UI should use the blocks.
    risk_score: Optional[float] = None
    severity: Optional[Severity] = None
    is_phishing: Optional[bool] = None
    reasons: Optional[list[ReasonDetail]] = None
    features: Optional[dict] = None


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
    threat_type: str = Field(default="UNKNOWN")


class HistoryResponse(BaseModel):
    """Paginated detection history."""
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
