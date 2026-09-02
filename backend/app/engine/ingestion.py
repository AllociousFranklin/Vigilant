"""SENTINEL Engine - Layer 1: Ingestion & Validation

Entry point for transaction payloads. Validates fields, computes SHA-256 deduplication
hash, and standardizes into IngestedTransaction.
"""
import uuid
import hashlib
from typing import Optional
from dataclasses import dataclass, field
from app.api.schemas import TransactionRequest, PaymentMethod


@dataclass
class IngestedTransaction:
    """Standardized transaction after ingestion."""
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str = "INR"
    payment_method: str = "credit_card"
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    billing_country: str = "IN"
    shipping_country: Optional[str] = None
    card_bin: Optional[str] = None
    is_international: bool = False
    merchant_category: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    input_hash: str = ""


def compute_hash(merchant_id: str, amount: float, transaction_id: str) -> str:
    """Compute SHA-256 hash of transaction identifier elements for deduplication."""
    content = f"{merchant_id}:{amount}:{transaction_id}"
    return hashlib.sha256(content.encode('utf-8', errors='ignore')).hexdigest()[:16]


def ingest(request: TransactionRequest) -> IngestedTransaction:
    """
    Layer 1: Ingest and validate transaction payload.
    """
    if request.amount <= 0:
        raise ValueError("Transaction amount must be strictly greater than 0")
    if not request.merchant_id or not request.merchant_id.strip():
        raise ValueError("Merchant ID is required")

    txn_id = request.transaction_id or f"txn_{uuid.uuid4().hex[:12]}"
    method_str = request.payment_method.value if hasattr(request.payment_method, 'value') else str(request.payment_method)

    # Billing & shipping cross-border detection
    is_intl = request.is_international
    if request.billing_country and request.shipping_country:
        if request.billing_country.upper() != request.shipping_country.upper():
            is_intl = True

    input_hash = compute_hash(request.merchant_id, request.amount, txn_id)

    return IngestedTransaction(
        transaction_id=txn_id,
        merchant_id=request.merchant_id.strip(),
        amount=float(request.amount),
        currency=request.currency or "INR",
        payment_method=method_str,
        customer_email=request.customer_email.strip() if request.customer_email else None,
        customer_phone=request.customer_phone.strip() if request.customer_phone else None,
        customer_id=request.customer_id.strip() if request.customer_id else None,
        device_fingerprint=request.device_fingerprint.strip() if request.device_fingerprint else None,
        ip_address=request.ip_address.strip() if request.ip_address else None,
        billing_country=request.billing_country.upper() if request.billing_country else "IN",
        shipping_country=request.shipping_country.upper() if request.shipping_country else None,
        card_bin=request.card_bin.strip() if request.card_bin else None,
        is_international=is_intl,
        merchant_category=request.merchant_category,
        metadata=request.metadata or {},
        input_hash=input_hash,
    )
