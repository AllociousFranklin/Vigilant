import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    History as HistoryIcon, Filter, Eye, FileText, CheckCircle2,
    XCircle, AlertTriangle, RefreshCw, X, Copy, Check
} from 'lucide-react';
import { sentinelApi } from '../utils/api';

const History = () => {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [riskFilter, setRiskFilter] = useState("");
    const [loading, setLoading] = useState(true);
    const [selectedDossier, setSelectedDossier] = useState(null);
    const [copied, setCopied] = useState(false);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const data = await sentinelApi.getTransactions(page, 15, riskFilter || null);
            setItems(data.items || []);
            setTotal(data.total || 0);
        } catch (err) {
            console.error("Failed to fetch history:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [page, riskFilter]);

    const handleFeedback = async (txnId, outcome) => {
        try {
            await sentinelApi.submitFeedback(txnId, outcome, "Submitted via Merchant Audit Trail");
            alert(`Recorded outcome: ${outcome} for transaction ${txnId}`);
            fetchHistory();
        } catch (err) {
            alert("Feedback submission failed: " + err.message);
        }
    };

    const openDossier = async (assessmentId) => {
        try {
            const data = await sentinelApi.getDisputeDossier(assessmentId);
            setSelectedDossier(data);
            setCopied(false);
        } catch (err) {
            alert("Failed to load dossier: " + err.message);
        }
    };

    const copyDossier = () => {
        if (selectedDossier?.dossier_text) {
            navigator.clipboard.writeText(selectedDossier.dossier_text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const getRiskColor = (lvl) => {
        if (lvl === 'CRITICAL') return '#FF1E56';
        if (lvl === 'HIGH') return 'var(--danger)';
        if (lvl === 'MEDIUM') return 'var(--warning)';
        return 'var(--success)';
    };

    return (
        <div style={{ paddingTop: '100px', paddingBottom: '80px', maxWidth: '1280px', margin: '0 auto' }}>
            
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'Outfit', marginBottom: '0.3rem' }}>
                        Merchant Audit Trail
                    </h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                        Forensic ledger of past transaction risk assessments and representment dossiers ({total} total).
                    </p>
                </div>

                {/* Filter */}
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <Filter size={16} color="var(--text-muted)" />
                    {["", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((lvl) => (
                        <button
                            key={lvl}
                            onClick={() => { setRiskFilter(lvl); setPage(1); }}
                            style={{
                                padding: '0.45rem 0.85rem',
                                borderRadius: '8px',
                                background: riskFilter === lvl ? 'var(--accent)' : 'var(--bg-card)',
                                color: riskFilter === lvl ? '#0A0F1C' : 'var(--text-secondary)',
                                border: '1px solid var(--border)',
                                fontSize: '0.8rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                            }}
                        >
                            {lvl || "ALL"}
                        </button>
                    ))}
                    <button
                        onClick={fetchHistory}
                        style={{
                            padding: '0.45rem',
                            borderRadius: '8px',
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border)',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                        }}
                    >
                        <RefreshCw size={14} className={loading ? "spinner" : ""} />
                    </button>
                </div>
            </div>

            {/* Table */}
            <div style={{
                background: 'var(--bg-card)',
                borderRadius: '16px',
                border: '1px solid var(--border-subtle)',
                overflow: 'hidden',
            }}>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                        <thead>
                            <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                                <th style={{ padding: '1rem' }}>Timestamp</th>
                                <th style={{ padding: '1rem' }}>Transaction ID</th>
                                <th style={{ padding: '1rem' }}>Merchant</th>
                                <th style={{ padding: '1rem' }}>Amount</th>
                                <th style={{ padding: '1rem' }}>Payment</th>
                                <th style={{ padding: '1rem' }}>Fraud / CB Score</th>
                                <th style={{ padding: '1rem' }}>Risk Level</th>
                                <th style={{ padding: '1rem' }}>Action</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>Evidence & Feedback</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.length === 0 ? (
                                <tr>
                                    <td colSpan="9" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                        {loading ? "Loading audit records..." : "No transactions recorded yet. Run tests from the Transaction Risk studio."}
                                    </td>
                                </tr>
                            ) : (
                                items.map((row) => (
                                    <tr
                                        key={row.assessment_id}
                                        style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.2s' }}
                                        onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'}
                                        onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                                    >
                                        <td style={{ padding: '1rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                            {row.timestamp ? row.timestamp.split('T')[0] : 'N/A'}
                                        </td>
                                        <td style={{ padding: '1rem', fontFamily: 'JetBrains Mono', fontWeight: 600, color: 'var(--text-primary)' }}>
                                            {row.assessment_id.slice(0, 12)}
                                        </td>
                                        <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                                            {row.merchant_id}
                                        </td>
                                        <td style={{ padding: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                            ₹{row.amount.toLocaleString('en-IN')}
                                        </td>
                                        <td style={{ padding: '1rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                            {row.payment_method}
                                        </td>
                                        <td style={{ padding: '1rem', fontFamily: 'JetBrains Mono' }}>
                                            <span style={{ color: getRiskColor(row.risk_level), fontWeight: 700 }}>
                                                {Math.round(row.fraud_score)}
                                            </span>
                                            <span style={{ color: 'var(--text-muted)' }}> / </span>
                                            <span style={{ color: 'var(--text-secondary)' }}>
                                                {Math.round(row.chargeback_score)}
                                            </span>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <span style={{
                                                fontSize: '0.7rem',
                                                fontWeight: 800,
                                                padding: '3px 8px',
                                                borderRadius: '4px',
                                                background: `${getRiskColor(row.risk_level)}15`,
                                                color: getRiskColor(row.risk_level),
                                                border: `1px solid ${getRiskColor(row.risk_level)}30`,
                                            }}>
                                                {row.risk_level}
                                            </span>
                                        </td>
                                        <td style={{ padding: '1rem', fontWeight: 700 }}>
                                            <span style={{
                                                color: row.recommended_action === 'BLOCK' ? 'var(--danger)' : row.recommended_action === 'REVIEW' ? 'var(--warning)' : 'var(--success)',
                                            }}>
                                                {row.recommended_action}
                                            </span>
                                        </td>
                                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                                                <button
                                                    onClick={() => openDossier(row.assessment_id)}
                                                    style={{
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '0.3rem',
                                                        padding: '0.35rem 0.65rem',
                                                        borderRadius: '6px',
                                                        background: 'rgba(0, 229, 255, 0.1)',
                                                        border: '1px solid rgba(0, 229, 255, 0.25)',
                                                        color: 'var(--accent)',
                                                        fontSize: '0.75rem',
                                                        cursor: 'pointer',
                                                    }}
                                                >
                                                    <FileText size={13} />
                                                    <span>Dossier</span>
                                                </button>

                                                <button
                                                    onClick={() => handleFeedback(row.assessment_id, "chargeback_won")}
                                                    title="Mark Chargeback Won"
                                                    style={{
                                                        padding: '0.35rem 0.65rem',
                                                        borderRadius: '6px',
                                                        background: 'rgba(22, 199, 132, 0.1)',
                                                        border: '1px solid rgba(22, 199, 132, 0.25)',
                                                        color: 'var(--success)',
                                                        fontSize: '0.75rem',
                                                        cursor: 'pointer',
                                                    }}
                                                >
                                                    Won
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1rem 1.5rem',
                    borderTop: '1px solid var(--border-subtle)',
                    background: 'rgba(15, 23, 42, 0.4)',
                }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Showing page {page} of {Math.max(Math.ceil(total / 15), 1)} ({total} records)
                    </span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                            disabled={page <= 1}
                            onClick={() => setPage(page - 1)}
                            style={{
                                padding: '0.35rem 0.75rem',
                                borderRadius: '6px',
                                background: 'var(--bg-surface)',
                                border: '1px solid var(--border)',
                                color: 'var(--text-secondary)',
                                fontSize: '0.8rem',
                                cursor: page <= 1 ? 'not-allowed' : 'pointer',
                            }}
                        >
                            Previous
                        </button>
                        <button
                            disabled={page >= Math.ceil(total / 15)}
                            onClick={() => setPage(page + 1)}
                            style={{
                                padding: '0.35rem 0.75rem',
                                borderRadius: '6px',
                                background: 'var(--bg-surface)',
                                border: '1px solid var(--border)',
                                color: 'var(--text-secondary)',
                                fontSize: '0.8rem',
                                cursor: page >= Math.ceil(total / 15) ? 'not-allowed' : 'pointer',
                            }}
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            {/* Dossier Modal */}
            {selectedDossier && (
                <div style={{
                    position: 'fixed',
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0, 0, 0, 0.8)',
                    backdropFilter: 'blur(8px)',
                    zIndex: 2000,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '2rem',
                }}>
                    <div style={{
                        background: 'var(--bg-card)',
                        width: '100%',
                        maxWidth: '800px',
                        borderRadius: '16px',
                        border: '1px solid var(--border)',
                        padding: '2rem',
                        position: 'relative',
                        maxHeight: '85vh',
                        display: 'flex',
                        flexDirection: 'column',
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <FileText size={22} color="var(--accent)" />
                                <div>
                                    <h3 style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'Outfit' }}>
                                        Formal Chargeback Evidence Dossier
                                    </h3>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        Case: {selectedDossier.assessment_id} • Amount: ₹{selectedDossier.amount}
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedDossier(null)}
                                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <pre style={{
                            flex: 1,
                            overflowY: 'auto',
                            background: 'var(--bg-deep)',
                            padding: '1.25rem',
                            borderRadius: '8px',
                            border: '1px solid var(--border-subtle)',
                            fontFamily: 'JetBrains Mono, monospace',
                            fontSize: '0.78rem',
                            color: 'var(--text-primary)',
                            whiteSpace: 'pre-wrap',
                            lineHeight: 1.5,
                        }}>
                            {selectedDossier.dossier_text}
                        </pre>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
                            <button
                                onClick={copyDossier}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    padding: '0.65rem 1.25rem',
                                    borderRadius: '8px',
                                    background: copied ? 'var(--success)' : 'var(--accent)',
                                    color: '#0A0F1C',
                                    border: 'none',
                                    fontSize: '0.85rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                }}
                            >
                                {copied ? <Check size={16} /> : <Copy size={16} />}
                                <span>{copied ? "Copied to Clipboard!" : "Copy Full Dossier"}</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
};

export default History;
