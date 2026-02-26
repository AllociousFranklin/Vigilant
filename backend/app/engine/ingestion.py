"""VIGILANT Engine - Layer 1: Ingestion & Validation

Entry point for all artifacts. No ML logic here.
Just validation, classification, and forwarding.
"""
import re
import hashlib
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class IngestedArtifact:
    """Standardized artifact after ingestion."""
    artifact_id: str
    channel: str  # url, email, sms, html
    raw_url: Optional[str] = None
    raw_text: Optional[str] = None
    raw_html: Optional[str] = None
    extracted_urls: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    input_hash: str = ""
    input_preview: str = ""


# Common URL pattern
URL_PATTERN = re.compile(
    r'https?://[^\s<>"\']+|'
    r'www\.[^\s<>"\']+|'
    r'[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?',
    re.IGNORECASE
)


def extract_urls_from_text(text: str) -> list[str]:
    """Extract all URLs from a text body."""
    if not text:
        return []
    urls = URL_PATTERN.findall(text)
    # Normalize: add https:// if missing
    normalized = []
    for url in urls:
        url = url.strip().rstrip('.,;:!?)')
        url = url.replace('[.]', '.').replace('[-]', '-').replace('[:]', ':')
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        normalized.append(url)
    return list(set(normalized))


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of input for deduplication."""
    return hashlib.sha256(content.encode('utf-8', errors='ignore')).hexdigest()[:16]


def create_preview(url: str = None, text: str = None, max_len: int = 100) -> str:
    """Create a short preview of the input for logging."""
    content = url or text or ""
    if len(content) > max_len:
        return content[:max_len] + "..."
    return content


def ingest(url: str = None, text: str = None, html_body: str = None,
           channel: str = "url", metadata: dict = None) -> IngestedArtifact:
    """
    Layer 1: Ingest and validate raw input.
    
    - Validates that at least one input is provided
    - Extracts URLs from text/HTML if present
    - Computes input hash for deduplication
    - Returns standardized IngestedArtifact
    """
    import uuid

    if not url and not text and not html_body:
        raise ValueError("At least one of url, text, or html_body must be provided")
    
    if url:
        url = url.replace('[.]', '.').replace('[-]', '-').replace('[:]', ':')
    if text:
        text = text.replace('[.]', '.').replace('[-]', '-').replace('[:]', ':')
    if html_body:
        html_body = html_body.replace('[.]', '.').replace('[-]', '-').replace('[:]', ':')
    
    # Extract URLs from text content
    extracted_urls = []
    if url:
        url = url.replace('[.]', '.').replace('[-]', '-').replace('[:]', ':')
        extracted_urls.append(url.strip())
    if text:
        extracted_urls.extend(extract_urls_from_text(text))
    if html_body:
        extracted_urls.extend(extract_urls_from_text(html_body))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for u in extracted_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    
    # Compute hash from all inputs
    hash_input = f"{url or ''}{text or ''}{html_body or ''}"
    input_hash = compute_hash(hash_input)
    
    artifact = IngestedArtifact(
        artifact_id=str(uuid.uuid4()),
        channel=channel,
        raw_url=url,
        raw_text=text,
        raw_html=html_body,
        extracted_urls=unique_urls,
        metadata=metadata or {},
        input_hash=input_hash,
        input_preview=create_preview(url, text),
    )
    
    return artifact
