import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, Mail, MessageSquare, Link as LinkIcon, AlertTriangle, CheckCircle2,
    Loader2, ShieldAlert, Info, ShieldCheck, ShieldX, Activity, Zap, Target,
    Lock, Radio, ChevronRight
} from 'lucide-react';
import { vigilantApi } from '../utils/api';
import RiskGauge from '../components/RiskGauge';
import TelemetryPanel from '../components/TelemetryPanel';

/* ───── Stage Loading Stages ───── */
const ANALYSIS_STAGES = [
    { label: 'Executing Detection Stage…', duration: 800 },
    { label: 'Applying Policy Assessment…', duration: 700 },
    { label: 'Decision Engine Finalizing…', duration: 600 },
];

/* ───── System Status Indicators ───── */
const SystemStatusStrip = () => {
    const indicators = [
        { label: 'Detection Engine', status: 'Operational', ok: true },
        { label: 'Policy Layer', status: 'Enforced', ok: true },
        { label: 'Model Confidence', status: 'Stable', ok: true },
        { label: 'SOC Sync', status: 'Active', ok: true },
    ];
    return (
        <div className="elevated-card" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '1px',
            overflow: 'hidden',
            marginBottom: '80px',
        }}>
            {indicators.map((ind, i) => (
                <div key={i} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '1rem 1.25rem',
                    background: 'var(--bg-card)',
                }}>
                    <span className={`status-dot ${ind.ok ? 'operational' : 'critical'}`} />
                    <div>
                        <div style={{
                            fontSize: '0.7rem',
                            color: 'var(--text-muted)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                            fontWeight: 600,
                            marginBottom: '2px',
                        }}>{ind.label}</div>
                        <div style={{
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            color: ind.ok ? 'var(--success)' : 'var(--danger)',
                        }}>{ind.status}</div>
                    </div>
                </div>
            ))}
        </div>
    );
};

/* ───── Enterprise Result Console ───── */
const ResultConsole = ({ result }) => {
    if (!result) return null;

    const getDecisionColor = (action) => {
        if (!action) return 'var(--text-muted)';
        const a = action.toUpperCase();
        if (a.includes('BLOCK') || a.includes('HARD')) return 'var(--danger)';
        if (a.includes('WARN') || a.includes('SOFT')) return 'var(--warning)';
        return 'var(--success)';
    };

    const getDecisionLabel = (action) => {
        if (!action) return 'UNKNOWN';
        const a = action.toUpperCase();
        if (a.includes('BLOCK') || a.includes('HARD')) return 'BLOCKED';
        if (a.includes('WARN') || a.includes('SOFT')) return 'WARNED';
        return 'SAFE';
    };

    const decisionAction = result.decision?.recommended_action || (result.is_phishing ? 'HARD_BLOCK' : 'ALLOW');
    const decisionColor = getDecisionColor(decisionAction);
    const decisionLabel = getDecisionLabel(decisionAction);

    const severityLabel = result.assessment?.final_severity || (result.risk_score >= 85 ? 'CRITICAL' : result.risk_score >= 65 ? 'HIGH' : result.risk_score >= 35 ? 'MEDIUM' : 'LOW');

    return (
        <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            style={{ marginTop: '2rem' }}
        >
            {/* SUMMARY PANEL */}
            <div className="elevated-card" style={{
                padding: '2rem',
                marginBottom: '1rem',
                display: 'grid',
                gridTemplateColumns: 'auto 1fr',
                gap: '2.5rem',
                alignItems: 'center',
            }}>
                <RiskGauge score={result.risk_score} />

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: '0.4rem' }}>
                            Threat Type
                        </div>
                        <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                            {result.is_phishing ? 'Phishing Detected' : 'No Threat Identified'}
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: '0.4rem' }}>
                            Signal Strength
                        </div>
                        <div style={{
                            fontSize: '1rem', fontWeight: 600,
                            color: result.risk_score >= 65 ? 'var(--danger)' : result.risk_score >= 35 ? 'var(--warning)' : 'var(--success)',
                        }}>
                            {result.risk_score >= 65 ? 'Strong' : result.risk_score >= 35 ? 'Moderate' : 'Weak'}
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: '0.4rem' }}>
                            Policy Severity Floor
                        </div>
                        <div style={{
                            display: 'inline-block',
                            padding: '0.2rem 0.6rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            fontFamily: 'JetBrains Mono, monospace',
                            background: severityLabel === 'CRITICAL' ? 'rgba(239, 68, 68, 0.15)' :
                                severityLabel === 'HIGH' ? 'rgba(239, 68, 68, 0.1)' :
                                    severityLabel === 'MEDIUM' ? 'var(--warning-dim)' : 'var(--success-dim)',
                            color: severityLabel === 'CRITICAL' || severityLabel === 'HIGH' ? 'var(--danger)' :
                                severityLabel === 'MEDIUM' ? 'var(--warning)' : 'var(--success)',
                        }}>
                            {severityLabel}
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: '0.4rem' }}>
                            Analysis Latency
                        </div>
                        <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent)', fontFamily: 'JetBrains Mono, monospace' }}>
                            {result.latency_ms}ms
                        </div>
                    </div>
                </div>
            </div>

            {/* Two-column bottom section */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                {/* DETECTION SIGNALS PANEL */}
                <div className="elevated-card" style={{ padding: '1.5rem' }}>
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                        marginBottom: '1.25rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border)',
                    }}>
                        <Radio size={14} color="var(--accent)" />
                        <span style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            Detection Signals
                        </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                        {result.reasons && result.reasons.length > 0 ? (
                            result.reasons.map((reason, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, x: 12 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.08 }}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: '0.6rem',
                                        padding: '0.75rem',
                                        background: 'var(--bg-deep)',
                                        borderRadius: '0.4rem',
                                        borderLeft: `3px solid ${reason.signal_strength === 'STRONG' ? 'var(--danger)' :
                                            reason.signal_strength === 'MODERATE' ? 'var(--warning)' : 'var(--success)'}`,
                                    }}
                                >
                                    <div style={{ flex: 1 }}>
                                        <div style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem',
                                        }}>
                                            <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                                {reason.category}
                                            </span>
                                            <span style={{
                                                fontSize: '0.6rem', fontWeight: 700, padding: '0.15rem 0.4rem', borderRadius: '3px',
                                                fontFamily: 'JetBrains Mono, monospace',
                                                background: reason.signal_strength === 'STRONG' ? 'var(--danger-dim)' :
                                                    reason.signal_strength === 'MODERATE' ? 'var(--warning-dim)' : 'var(--success-dim)',
                                                color: reason.signal_strength === 'STRONG' ? 'var(--danger)' :
                                                    reason.signal_strength === 'MODERATE' ? 'var(--warning)' : 'var(--success)',
                                            }}>
                                                {reason.signal_strength}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                                            {reason.reason}
                                        </div>
                                    </div>
                                </motion.div>
                            ))
                        ) : (
                            <div className="flex-center" style={{ padding: '2rem', flexDirection: 'column', color: 'var(--text-secondary)' }}>
                                <CheckCircle2 size={32} color="var(--success)" style={{ marginBottom: '0.5rem' }} />
                                <span style={{ fontSize: '0.85rem' }}>No malicious signals detected.</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* ASSESSMENT + DECISION PANEL */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Assessment */}
                    <div className="elevated-card" style={{ padding: '1.5rem' }}>
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            marginBottom: '1.25rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border)',
                        }}>
                            <Target size={14} color="var(--secondary-accent)" />
                            <span style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                                Assessment
                            </span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>ML Risk Evaluation</span>
                                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                                    {result.risk_score}/100
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Policy Override Status</span>
                                <span style={{
                                    fontSize: '0.75rem', fontWeight: 600, padding: '0.15rem 0.5rem', borderRadius: '3px',
                                    background: result.assessment?.policy_override ? 'var(--warning-dim)' : 'var(--success-dim)',
                                    color: result.assessment?.policy_override ? 'var(--warning)' : 'var(--success)',
                                    fontFamily: 'JetBrains Mono, monospace',
                                }}>
                                    {result.assessment?.policy_override ? 'OVERRIDE ACTIVE' : 'NONE'}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Severity Escalation</span>
                                <span style={{
                                    fontSize: '0.75rem', fontWeight: 600, padding: '0.15rem 0.5rem', borderRadius: '3px',
                                    background: result.assessment?.escalated ? 'var(--danger-dim)' : 'var(--accent-dim)',
                                    color: result.assessment?.escalated ? 'var(--danger)' : 'var(--accent)',
                                    fontFamily: 'JetBrains Mono, monospace',
                                }}>
                                    {result.assessment?.escalated ? 'ESCALATED' : 'STANDARD'}
                                </span>
                            </div>
                            {result.assessment?.confidence_band && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Confidence Band</span>
                                    <span style={{
                                        fontSize: '0.75rem', fontWeight: 600, padding: '0.15rem 0.5rem', borderRadius: '3px',
                                        background: result.assessment.confidence_band === 'HIGH_CONFIDENCE' ? 'var(--success-dim)' :
                                            result.assessment.confidence_band === 'MIXED_SIGNALS' ? 'var(--warning-dim)' : 'var(--danger-dim)',
                                        color: result.assessment.confidence_band === 'HIGH_CONFIDENCE' ? 'var(--success)' :
                                            result.assessment.confidence_band === 'MIXED_SIGNALS' ? 'var(--warning)' : 'var(--danger)',
                                        fontFamily: 'JetBrains Mono, monospace',
                                    }}>
                                        {result.assessment.confidence_band.replace(/_/g, ' ')}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* FINAL DECISION */}
                    <div className="elevated-card" style={{
                        padding: '2rem',
                        textAlign: 'center',
                        borderColor: decisionColor === 'var(--danger)' ? 'rgba(239, 68, 68, 0.3)' :
                            decisionColor === 'var(--warning)' ? 'rgba(250, 204, 21, 0.3)' : 'rgba(34, 197, 94, 0.3)',
                    }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                            Final Decision
                        </div>
                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
                            style={{
                                fontSize: '2.25rem',
                                fontWeight: 700,
                                fontFamily: 'Outfit, sans-serif',
                                color: decisionColor,
                                letterSpacing: '0.1em',
                                textShadow: `0 0 30px ${decisionColor === 'var(--danger)' ? 'rgba(239, 68, 68, 0.3)' :
                                    decisionColor === 'var(--warning)' ? 'rgba(250, 204, 21, 0.3)' : 'rgba(34, 197, 94, 0.3)'}`,
                            }}
                        >
                            {decisionLabel}
                        </motion.div>
                        {result.decision?.enforcement_mode && (
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.5rem', fontFamily: 'JetBrains Mono, monospace' }}>
                                Mode: {result.decision.enforcement_mode}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Disclaimer */}
            <div style={{
                marginTop: '1rem', display: 'flex', gap: '0.6rem', alignItems: 'flex-start',
                padding: '1rem', background: 'var(--secondary-accent-dim)', borderRadius: '0.5rem',
                border: '1px solid rgba(59, 130, 246, 0.15)',
            }}>
                <Info size={16} color="var(--secondary-accent)" style={{ flexShrink: 0, marginTop: '1px' }} />
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                    <strong>Disclaimer:</strong> This assessment is generated by an automated system. A LOW severity score means no known malicious signatures were found; it does not guarantee the content is safe.
                </p>
            </div>

            {/* Action buttons */}
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem' }}>
                <button
                    onClick={() => window.dispatchEvent(new CustomEvent('vigilant-clear-result'))}
                    style={{
                        flex: 1, padding: '0.85rem',
                        background: 'transparent', border: '1px solid var(--border)',
                        color: 'var(--text-secondary)', borderRadius: '0.5rem',
                        fontSize: '0.85rem',
                    }}
                >
                    Clear Result
                </button>
                <button
                    style={{
                        flex: 1, padding: '0.85rem',
                        background: 'var(--bg-surface)', border: '1px solid var(--border)',
                        color: 'var(--text-primary)', borderRadius: '0.5rem',
                        fontSize: '0.85rem',
                    }}
                >
                    Flag False Positive
                </button>
            </div>
        </motion.div>
    );
};

/* ───── Main Scanner Component ───── */
const Scanner = () => {
    const [channel, setChannel] = useState('url');
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [stageIndex, setStageIndex] = useState(-1);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const handleClear = () => {
            setInput('');
            setResult(null);
        };
        window.addEventListener('vigilant-clear-result', handleClear);
        return () => window.removeEventListener('vigilant-clear-result', handleClear);
    }, []);

    const runStagedLoading = () => {
        return new Promise((resolve) => {
            let currentStage = 0;
            setStageIndex(currentStage);

            const advanceStage = () => {
                currentStage++;
                if (currentStage < ANALYSIS_STAGES.length) {
                    setStageIndex(currentStage);
                    setTimeout(advanceStage, ANALYSIS_STAGES[currentStage].duration);
                } else {
                    resolve();
                }
            };
            setTimeout(advanceStage, ANALYSIS_STAGES[0].duration);
        });
    };

    const handleScan = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        setLoading(true);
        setResult(null);
        setError(null);
        setStageIndex(0);

        try {
            // Run staged loading animation AND the API call concurrently
            const [, data] = await Promise.all([
                runStagedLoading(),
                (async () => {
                    const payload = { channel };
                    if (channel === 'url') payload.url = input;
                    else payload.text = input;
                    return vigilantApi.scan(payload);
                })(),
            ]);
            setResult(data);
        } catch (err) {
            console.error(err);
            setError('Analysis failed. Please ensure the backend is running.');
        } finally {
            setLoading(false);
            setStageIndex(-1);
        }
    };

    const channels = [
        {
            id: 'url', label: 'URL Site', icon: LinkIcon,
            descriptor: 'Structural & entropy analysis',
            placeholder: 'https://example-phishing.com',
        },
        {
            id: 'email', label: 'Email Text', icon: Mail,
            descriptor: 'Semantic lifecycle modeling',
            placeholder: 'Paste email content here...',
        },
        {
            id: 'sms', label: 'SMS Message', icon: MessageSquare,
            descriptor: 'Social engineering pattern detection',
            placeholder: 'Paste suspicious message here...',
        },
    ];

    return (
        <div style={{ paddingTop: '120px', paddingBottom: '4rem' }}>
            {/* ──── HERO ──── */}
            <header style={{ textAlign: 'center', marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.75rem', marginBottom: '0.75rem', lineHeight: 1.2 }}>
                    Live Threat <span style={{ color: 'var(--accent)' }}>Intelligence</span> Console
                </h1>
                <p style={{
                    color: 'var(--text-secondary)',
                    fontSize: '1.1rem',
                    maxWidth: '700px',
                    margin: '0 auto',
                    lineHeight: 1.6,
                }}>
                    Real-time zero-day phishing detection across URL, email, SMS, and browser traffic using policy-enforced AI.
                </p>
            </header>

            {/* ──── SYSTEM STATUS STRIP ──── */}
            <SystemStatusStrip />

            {/* ──── MAIN CONTENT ──── */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 280px',
                gap: '1.5rem',
                alignItems: 'start',
            }}>
                {/* Left: Threat Input Module */}
                <div>
                    {/* Section header */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.35rem' }}>Threat Input Module</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Submit structured input for multi-stage phishing assessment.
                        </p>
                    </div>

                    {/* Channel Tabs */}
                    <div className="elevated-card" style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '1px',
                        overflow: 'hidden',
                        marginBottom: '1rem',
                    }}>
                        {channels.map((ch) => {
                            const Icon = ch.icon;
                            const isActive = channel === ch.id;
                            return (
                                <button
                                    key={ch.id}
                                    onClick={() => { setChannel(ch.id); setInput(''); setResult(null); }}
                                    style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: '0.35rem',
                                        padding: '1.1rem 0.75rem',
                                        background: isActive ? 'var(--bg-surface)' : 'var(--bg-card)',
                                        color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                                        border: 'none',
                                        borderBottom: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                                        fontSize: '0.85rem',
                                        transition: 'all 0.2s ease',
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <Icon size={16} />
                                        <span style={{ fontWeight: 600 }}>{ch.label}</span>
                                    </div>
                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                                        {ch.descriptor}
                                    </span>
                                </button>
                            );
                        })}
                    </div>

                    {/* Input Form */}
                    <form onSubmit={handleScan} className="elevated-card" style={{ padding: '1.5rem' }}>
                        {channel === 'url' ? (
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={channels.find(c => c.id === 'url').placeholder}
                                className="console-input"
                            />
                        ) : (
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={channels.find(c => c.id === channel).placeholder}
                                className="console-input"
                                style={{ minHeight: '180px', resize: 'vertical' }}
                            />
                        )}

                        {/* Analyze Button with staged loading */}
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            style={{
                                marginTop: '1rem',
                                width: '100%',
                                padding: '1rem',
                                background: loading ? 'var(--bg-surface)' : 'var(--accent)',
                                color: loading ? 'var(--accent)' : 'var(--bg-deep)',
                                borderRadius: '0.5rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.75rem',
                                fontSize: '0.95rem',
                                border: loading ? '1px solid var(--accent)' : 'none',
                                opacity: (!loading && !input.trim()) ? 0.5 : 1,
                                letterSpacing: '0.02em',
                            }}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="spinner" size={18} />
                                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.85rem' }}>
                                        {stageIndex >= 0 && stageIndex < ANALYSIS_STAGES.length
                                            ? ANALYSIS_STAGES[stageIndex].label
                                            : 'Processing…'}
                                    </span>
                                </>
                            ) : (
                                <>
                                    <Search size={18} />
                                    Analyze Threat
                                </>
                            )}
                        </button>

                        {error && (
                            <div style={{
                                color: 'var(--danger)', marginTop: '0.75rem',
                                fontSize: '0.8rem', textAlign: 'center',
                                padding: '0.5rem', background: 'var(--danger-dim)', borderRadius: '0.4rem',
                            }}>
                                {error}
                            </div>
                        )}
                    </form>

                    {/* Result Console */}
                    <AnimatePresence>
                        {result && <ResultConsole result={result} />}
                    </AnimatePresence>
                </div>

                {/* Right: SOC Telemetry Side Panel */}
                <TelemetryPanel />
            </div>
        </div>
    );
};

export default Scanner;
