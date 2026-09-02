import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ShieldCheck, ShieldAlert, ShieldX, AlertTriangle, CheckCircle2,
    Zap, FileText, Copy, Check, ArrowRight, RefreshCw, Cpu
} from 'lucide-react';
import { sentinelApi } from '../utils/api';
import RiskGauge from '../components/RiskGauge';

const PRESETS = [
    {
        name: "Routine UPI (Legit)",
        tag: "Low Risk",
        color: "var(--success)",
        payload: {
            merchant_id: "MERCH_ZEPTO_DAILY",
            amount: 450,
            payment_method: "upi",
            customer_email: "rajesh.kumar@gmail.com",
            customer_phone: "+919988776655",
            billing_country: "IN",
            shipping_country: "IN",
            metadata: {
                customer_account_age_days: 400,
                customer_total_txns: 120,
                customer_dispute_rate: 0.0,
                phone_verified: true,
                device_fingerprint_new: false,
                ip_risk_score: 0.02,
                txn_count_1h: 0,
            }
        }
    },
    {
        name: "Legit High-Value (₹2,00,000)",
        tag: "False-Positive Test",
        color: "#00E5FF",
        payload: {
            merchant_id: "MERCH_TATACLIQ_LUXURY",
            amount: 200000,
            payment_method: "credit_card",
            customer_email: "vip_patron@corporation.com",
            customer_phone: "+919876543210",
            billing_country: "IN",
            shipping_country: "IN",
            metadata: {
                customer_account_age_days: 1095,
                customer_total_txns: 180,
                customer_dispute_rate: 0.0,
                phone_verified: true,
                device_fingerprint_new: false,
                ip_risk_score: 0.01,
                txn_count_1h: 0,
                hour_of_day: 14,
                merchant_avg_txn: 80000.0,
            }
        }
    },
    {
        name: "Velocity Burst Attack",
        tag: "Automated Bot",
        color: "var(--danger)",
        payload: {
            merchant_id: "MERCH_QUICK_PAY",
            amount: 4999,
            payment_method: "upi",
            device_fingerprint: "dev_bot_burst_01",
            metadata: {
                txn_count_1h: 10,
                txn_count_24h: 15,
                device_fingerprint_new: true,
            }
        }
    },
    {
        name: "Card Testing Attack",
        tag: "Micro Auth",
        color: "#FF1E56",
        payload: {
            merchant_id: "MERCH_GATEWAY",
            amount: 49,
            payment_method: "credit_card",
            card_bin: "411111",
            metadata: {
                txn_count_1h: 6,
                device_fingerprint_new: true,
            }
        }
    },
    {
        name: "Syndicate Abuse Ring",
        tag: "New Device + VPN",
        color: "#FF1E56",
        payload: {
            merchant_id: "MERCH_DIGITAL_CARDS",
            amount: 35000,
            payment_method: "credit_card",
            customer_email: "attacker77@mailinator.com",
            billing_country: "US",
            shipping_country: "IN",
            is_international: true,
            metadata: {
                device_fingerprint_new: true,
                ip_risk_score: 0.92,
                txn_count_24h: 8,
                billing_shipping_mismatch: true
            }
        }
    },
    {
        name: "Chronic Dispute Abuser",
        tag: "Chargeback Risk",
        color: "var(--warning)",
        payload: {
            merchant_id: "MERCH_ELECTRONICS_HUB",
            amount: 38000,
            payment_method: "credit_card",
            customer_email: "chronic_disputer@gmail.com",
            metadata: {
                customer_dispute_rate: 0.45,
                customer_total_txns: 25,
            }
        }
    }
];

const TransactionScorer = () => {
    const [formData, setFormData] = useState({
        merchant_id: "MERCHANT_RAZORPAY_01",
        amount: 14999,
        payment_method: "credit_card",
        customer_email: "buyer@example.com",
        customer_phone: "+919876543210",
        device_fingerprint: "dev_usr_laptop_88",
        billing_country: "IN",
        shipping_country: "IN",
        is_international: false,
        card_bin: "424242",
        merchant_category: "electronics",
    });

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [copiedDossier, setCopiedDossier] = useState(false);
    const [showDossier, setShowDossier] = useState(false);

    const handlePreset = (preset) => {
        setFormData({
            ...formData,
            ...preset.payload,
        });
        setResult(null);
    };

    const handleSubmit = async (e) => {
        if (e) e.preventDefault();
        setLoading(true);
        setCopiedDossier(false);
        try {
            const data = await sentinelApi.assessTransaction({
                merchant_id: formData.merchant_id,
                amount: parseFloat(formData.amount),
                currency: "INR",
                payment_method: formData.payment_method,
                customer_email: formData.customer_email || undefined,
                customer_phone: formData.customer_phone || undefined,
                device_fingerprint: formData.device_fingerprint || undefined,
                billing_country: formData.billing_country,
                shipping_country: formData.shipping_country || undefined,
                card_bin: formData.card_bin || undefined,
                is_international: formData.is_international,
                merchant_category: formData.merchant_category,
                metadata: formData.metadata || {},
            });
            setResult(data);
        } catch (err) {
            console.error("Assessment failed:", err);
            alert("Inference Error: " + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const copyDossier = () => {
        if (result?.decision?.chargeback_evidence) {
            navigator.clipboard.writeText(result.decision.chargeback_evidence);
            setCopiedDossier(true);
            setTimeout(() => setCopiedDossier(false), 2500);
        }
    };

    const getActionBadge = (action) => {
        if (action === "BLOCK") {
            return {
                bg: "rgba(255, 77, 79, 0.15)",
                border: "rgba(255, 77, 79, 0.4)",
                color: "var(--danger)",
                icon: ShieldX,
                text: "TRANSACTION BLOCKED"
            };
        }
        if (action === "REVIEW") {
            return {
                bg: "rgba(251, 191, 36, 0.15)",
                border: "rgba(251, 191, 36, 0.4)",
                color: "var(--warning)",
                icon: AlertTriangle,
                text: "FLAGGED FOR REVIEW"
            };
        }
        return {
            bg: "rgba(22, 199, 132, 0.15)",
            border: "rgba(22, 199, 132, 0.4)",
            color: "var(--success)",
            icon: ShieldCheck,
            text: "TRANSACTION APPROVED (ALLOW)"
        };
    };

    return (
        <div style={{ paddingTop: '100px', paddingBottom: '80px', maxWidth: '1280px', margin: '0 auto' }}>
            
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.35rem 0.9rem',
                    borderRadius: '20px',
                    background: 'rgba(0, 229, 255, 0.08)',
                    border: '1px solid rgba(0, 229, 255, 0.25)',
                    color: 'var(--accent)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    marginBottom: '1rem',
                }}>
                    <Cpu size={14} />
                    <span>RAZORPAY BUILDATHON TRACK 02: AI RISK MANAGER</span>
                </div>
                <h1 style={{
                    fontSize: '2.8rem',
                    fontWeight: 800,
                    fontFamily: 'Outfit, sans-serif',
                    letterSpacing: '-0.02em',
                    lineHeight: 1.15,
                    marginBottom: '0.75rem',
                }}>
                    Real-Time Payment Fraud & Chargeback Defense
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '720px', margin: '0 auto' }}>
                    Evaluates transactions across 30 behavioral signals using ensemble XGBoost + Random Forest,
                    applies non-negotiable policy floors, and auto-generates chargeback dispute dossiers.
                </p>
            </div>

            {/* Presets Bar */}
            <div style={{
                background: 'var(--bg-card)',
                padding: '1.25rem',
                borderRadius: '16px',
                border: '1px solid var(--border-subtle)',
                marginBottom: '2rem',
            }}>
                <div style={{
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    color: 'var(--text-muted)',
                    letterSpacing: '0.08em',
                    fontWeight: 700,
                    marginBottom: '0.85rem',
                }}>
                    Quick Demo Presets (Simulate Attack Vectors & Legit Benchmarks)
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
                    {PRESETS.map((p, i) => (
                        <button
                            key={i}
                            type="button"
                            onClick={() => handlePreset(p)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0.5rem 0.9rem',
                                borderRadius: '8px',
                                background: 'rgba(15, 23, 42, 0.8)',
                                border: '1px solid var(--border)',
                                color: 'var(--text-primary)',
                                fontSize: '0.85rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                            }}
                            onMouseOver={(e) => e.currentTarget.style.borderColor = p.color}
                            onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
                        >
                            <span style={{ fontWeight: 600 }}>{p.name}</span>
                            <span style={{
                                fontSize: '0.65rem',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                background: `${p.color}20`,
                                color: p.color,
                                fontWeight: 700,
                            }}>{p.tag}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Interactive Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: '2rem' }}>
                
                {/* Form Column */}
                <div style={{
                    background: 'var(--bg-card)',
                    padding: '2rem',
                    borderRadius: '16px',
                    border: '1px solid var(--border-subtle)',
                }}>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem', fontFamily: 'Outfit' }}>
                        Transaction Parameters
                    </h3>

                    <form onSubmit={handleSubmit}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Merchant ID
                                </label>
                                <input
                                    type="text"
                                    value={formData.merchant_id}
                                    onChange={(e) => setFormData({ ...formData, merchant_id: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                    required
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Amount (INR ₹)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="1"
                                    value={formData.amount}
                                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                        fontWeight: 600,
                                    }}
                                    required
                                />
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Payment Method
                                </label>
                                <select
                                    value={formData.payment_method}
                                    onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                >
                                    <option value="upi">UPI (Instant VPA)</option>
                                    <option value="credit_card">Credit Card (Visa/Mastercard/RuPay)</option>
                                    <option value="debit_card">Debit Card</option>
                                    <option value="net_banking">Net Banking</option>
                                    <option value="wallet">Digital Wallet</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Card BIN (First 6 digits)
                                </label>
                                <input
                                    type="text"
                                    maxLength="6"
                                    value={formData.card_bin}
                                    onChange={(e) => setFormData({ ...formData, card_bin: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                />
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Customer Email
                                </label>
                                <input
                                    type="email"
                                    value={formData.customer_email}
                                    onChange={(e) => setFormData({ ...formData, customer_email: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Customer Phone (OTP verified)
                                </label>
                                <input
                                    type="text"
                                    value={formData.customer_phone}
                                    onChange={(e) => setFormData({ ...formData, customer_phone: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                />
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Billing Country
                                </label>
                                <input
                                    type="text"
                                    value={formData.billing_country}
                                    onChange={(e) => setFormData({ ...formData, billing_country: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                                    Shipping Country
                                </label>
                                <input
                                    type="text"
                                    value={formData.shipping_country}
                                    onChange={(e) => setFormData({ ...formData, shipping_country: e.target.value })}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'var(--bg-surface)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                    }}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '1rem',
                                borderRadius: '10px',
                                background: 'linear-gradient(135deg, #00E5FF 0%, #2563EB 100%)',
                                color: '#0A0F1C',
                                border: 'none',
                                fontSize: '1rem',
                                fontWeight: 700,
                                letterSpacing: '0.04em',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.75rem',
                                boxShadow: '0 4px 20px rgba(0, 229, 255, 0.25)',
                            }}
                        >
                            {loading ? (
                                <>
                                    <RefreshCw size={18} className="spinner" />
                                    <span>Running AI Inference...</span>
                                </>
                            ) : (
                                <>
                                    <Zap size={18} />
                                    <span>Assess Transaction Risk (Sub-15ms)</span>
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Results Column */}
                {result && (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        style={{
                            background: 'var(--bg-card)',
                            padding: '2rem',
                            borderRadius: '16px',
                            border: '1px solid var(--border-subtle)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '1.5rem',
                        }}
                    >
                        {/* Decision Banner */}
                        {(() => {
                            const badge = getActionBadge(result.decision.recommended_action);
                            const Icon = badge.icon;
                            return (
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    padding: '1rem 1.25rem',
                                    borderRadius: '12px',
                                    background: badge.bg,
                                    border: `1px solid ${badge.border}`,
                                    color: badge.color,
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <Icon size={24} />
                                        <div>
                                            <div style={{ fontSize: '1.1rem', fontWeight: 800, fontFamily: 'Outfit' }}>
                                                {badge.text}
                                            </div>
                                            <div style={{ fontSize: '0.75rem', opacity: 0.9 }}>
                                                Fraud Type: <strong>{result.assessment.fraud_type}</strong> • Confidence: {result.assessment.confidence_band}
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                            Inference Latency
                                        </div>
                                        <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                                            {result.latency_ms} ms
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Dual Gauges */}
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-around',
                            padding: '1rem',
                            background: 'rgba(15, 23, 42, 0.4)',
                            borderRadius: '12px',
                            border: '1px solid var(--border-subtle)',
                        }}>
                            <RiskGauge score={result.assessment.fraud_score} title="Transaction Fraud Risk" size={160} />
                            <RiskGauge score={result.assessment.chargeback_score} title="Chargeback Propensity" size={160} />
                        </div>

                        {/* Explanations List */}
                        <div>
                            <div style={{
                                fontSize: '0.8rem',
                                textTransform: 'uppercase',
                                color: 'var(--text-muted)',
                                letterSpacing: '0.08em',
                                fontWeight: 700,
                                marginBottom: '0.75rem',
                            }}>
                                Forensic Evidence Signals ({result.assessment.reasons.length} Detected)
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                {result.assessment.reasons.map((r, i) => (
                                    <div
                                        key={i}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            padding: '0.65rem 0.9rem',
                                            borderRadius: '8px',
                                            background: 'var(--bg-surface)',
                                            border: '1px solid var(--border-subtle)',
                                            fontSize: '0.85rem',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                            <span style={{
                                                fontSize: '0.65rem',
                                                padding: '2px 6px',
                                                borderRadius: '4px',
                                                fontWeight: 800,
                                                background: r.signal_strength === 'STRONG' ? 'rgba(255, 77, 79, 0.15)' : 'rgba(251, 191, 36, 0.15)',
                                                color: r.signal_strength === 'STRONG' ? 'var(--danger)' : 'var(--warning)',
                                            }}>
                                                {r.signal_strength}
                                            </span>
                                            <span style={{ color: 'var(--text-primary)' }}>{r.reason}</span>
                                        </div>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {r.category}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Chargeback Dispute Dossier Action */}
                        <div style={{
                            padding: '1.25rem',
                            borderRadius: '12px',
                            background: 'rgba(37, 99, 235, 0.08)',
                            border: '1px solid rgba(37, 99, 235, 0.25)',
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', fontWeight: 600, fontSize: '0.9rem' }}>
                                    <FileText size={18} />
                                    <span>Chargeback Evidence Dossier (Merchant Defense)</span>
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <button
                                        type="button"
                                        onClick={() => setShowDossier(!showDossier)}
                                        style={{
                                            padding: '0.35rem 0.75rem',
                                            borderRadius: '6px',
                                            background: 'rgba(255, 255, 255, 0.08)',
                                            border: 'none',
                                            color: 'var(--text-secondary)',
                                            fontSize: '0.75rem',
                                            cursor: 'pointer',
                                        }}
                                    >
                                        {showDossier ? "Hide" : "View"}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={copyDossier}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.4rem',
                                            padding: '0.35rem 0.75rem',
                                            borderRadius: '6px',
                                            background: copiedDossier ? 'var(--success)' : 'var(--accent)',
                                            border: 'none',
                                            color: '#0A0F1C',
                                            fontSize: '0.75rem',
                                            fontWeight: 700,
                                            cursor: 'pointer',
                                        }}
                                    >
                                        {copiedDossier ? <Check size={14} /> : <Copy size={14} />}
                                        <span>{copiedDossier ? "Copied!" : "Copy Dossier"}</span>
                                    </button>
                                </div>
                            </div>

                            {showDossier && (
                                <pre style={{
                                    padding: '1rem',
                                    background: 'var(--bg-deep)',
                                    borderRadius: '8px',
                                    fontSize: '0.75rem',
                                    color: 'var(--text-secondary)',
                                    fontFamily: 'JetBrains Mono, monospace',
                                    maxHeight: '220px',
                                    overflowY: 'auto',
                                    whiteSpace: 'pre-wrap',
                                    border: '1px solid var(--border-subtle)',
                                }}>
                                    {result.decision.chargeback_evidence}
                                </pre>
                            )}
                        </div>

                    </motion.div>
                )}

            </div>
        </div>
    );
};

export default TransactionScorer;
