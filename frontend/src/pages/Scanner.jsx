import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Mail, MessageSquare, Link as LinkIcon, AlertTriangle, CheckCircle2, Loader2, ShieldAlert } from 'lucide-react';
import { vigilantApi } from '../utils/api';
import RiskGauge from '../components/RiskGauge';

const Scanner = () => {
    const [channel, setChannel] = useState('url');
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleScan = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        setLoading(true);
        setResult(null);
        setError(null);

        try {
            const payload = { channel };
            if (channel === 'url') payload.url = input;
            else payload.text = input;

            const data = await vigilantApi.scan(payload);
            setResult(data);
        } catch (err) {
            console.error(err);
            setError('Analysis failed. Please ensure the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    const channels = [
        { id: 'url', label: 'URL Site', icon: LinkIcon, placeholder: 'https://example-phishing.com' },
        { id: 'email', label: 'Email Text', icon: Mail, placeholder: 'Paste email content here...' },
        { id: 'sms', label: 'SMS / Message', icon: MessageSquare, placeholder: 'Paste suspicious message here...' },
    ];

    return (
        <div style={{ padding: '6rem 0 4rem' }}>
            <header style={{ textAlign: 'center', marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Live Threat <span style={{ color: 'var(--accent)' }}>Analysis</span></h1>
                <p style={{ color: 'var(--text-secondary)' }}>Identify zero-day phishing attempts across multiple channels in real-time.</p>
            </header>

            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                {/* Channel Selector */}
                <div className="glass" style={{ display: 'flex', gap: '0.5rem', padding: '0.4rem', marginBottom: '1.5rem' }}>
                    {channels.map((ch) => {
                        const Icon = ch.icon;
                        const isActive = channel === ch.id;
                        return (
                            <button
                                key={ch.id}
                                onClick={() => setChannel(ch.id)}
                                style={{
                                    flex: 1,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '0.75rem',
                                    padding: '1rem',
                                    borderRadius: '0.75rem',
                                    background: isActive ? 'var(--bg-surface)' : 'transparent',
                                    color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                                    border: 'none',
                                    fontSize: '0.95rem',
                                }}
                            >
                                <Icon size={20} />
                                <span>{ch.label}</span>
                            </button>
                        );
                    })}
                </div>

                {/* Input Form */}
                <form onSubmit={handleScan} className="glass" style={{ padding: '2rem', marginBottom: '2rem' }}>
                    <div style={{ position: 'relative' }}>
                        {channel === 'url' ? (
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={channels.find(c => c.id === 'url').placeholder}
                                style={{
                                    width: '100%',
                                    padding: '1.25rem 1.5rem',
                                    background: 'var(--bg-deep)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '1rem',
                                    color: 'var(--text-primary)',
                                    fontSize: '1.1rem',
                                    outline: 'none',
                                }}
                            />
                        ) : (
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={channels.find(c => c.id === channel).placeholder}
                                style={{
                                    width: '100%',
                                    minHeight: '200px',
                                    padding: '1.25rem 1.5rem',
                                    background: 'var(--bg-deep)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '1rem',
                                    color: 'var(--text-primary)',
                                    fontSize: '1.1rem',
                                    outline: 'none',
                                    resize: 'vertical',
                                }}
                            />
                        )}

                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            style={{
                                marginTop: '1.5rem',
                                width: '100%',
                                padding: '1.25rem',
                                background: 'linear-gradient(135deg, var(--accent), #0891b2)',
                                color: 'var(--bg-deep)',
                                borderRadius: '1rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.75rem',
                                fontSize: '1.1rem',
                                border: 'none',
                                boxShadow: '0 4px 20px rgba(34, 211, 238, 0.2)',
                                opacity: (loading || !input.trim()) ? 0.6 : 1,
                            }}
                        >
                            {loading ? <Loader2 className="spinner" size={24} /> : <Search size={22} />}
                            {loading ? 'Analyzing Artifact...' : 'Analyze Now'}
                        </button>
                    </div>
                    {error && <div style={{ color: 'var(--danger)', marginTop: '1rem', fontSize: '0.9rem', textAlign: 'center' }}>{error}</div>}
                </form>

                {/* Results Section */}
                <AnimatePresence>
                    {result && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="glass"
                            style={{ padding: '3rem', display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '3rem' }}
                        >
                            <div style={{ textAlign: 'center' }}>
                                <RiskGauge score={result.risk_score} />
                                <div style={{ marginTop: '2rem' }}>
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>ANALYSIS LATENCY</p>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--accent)' }}>{result.latency_ms}ms</div>
                                </div>
                            </div>

                            <div>
                                <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <ShieldAlert size={24} color="var(--accent)" />
                                    Risk Factors
                                </h3>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                    {result.reasons.length > 0 ? (
                                        result.reasons.map((reason, idx) => (
                                            <motion.div
                                                key={idx}
                                                initial={{ opacity: 0, x: 20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: idx * 0.1 }}
                                                className="glass"
                                                style={{ padding: '1rem 1.25rem', borderLeft: `4px solid ${result.is_phishing ? 'var(--danger)' : 'var(--success)'}` }}
                                            >
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                                    <span style={{ fontSize: '0.8rem', color: 'var(--accent)', fontWeight: 600, textTransform: 'uppercase' }}>{reason.category}</span>
                                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{Math.round(reason.confidence)}% confidence</span>
                                                </div>
                                                <p style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>{reason.reason}</p>
                                            </motion.div>
                                        ))
                                    ) : (
                                        <div className="flex-center" style={{ padding: '3rem', flexDirection: 'column', color: 'var(--text-secondary)' }}>
                                            <CheckCircle2 size={48} color="var(--success)" style={{ marginBottom: '1rem' }} />
                                            <p>No major risk factors detected.</p>
                                        </div>
                                    )}
                                </div>

                                <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                                    <button
                                        onClick={() => {
                                            setInput('');
                                            setResult(null);
                                        }}
                                        style={{
                                            flex: 1,
                                            padding: '1rem',
                                            background: 'transparent',
                                            border: '1px solid var(--border)',
                                            color: 'var(--text-secondary)',
                                            borderRadius: '0.75rem'
                                        }}
                                    >
                                        Clear Result
                                    </button>
                                    <button
                                        style={{
                                            flex: 1,
                                            padding: '1rem',
                                            background: 'var(--bg-surface)',
                                            border: 'none',
                                            color: 'var(--text-primary)',
                                            borderRadius: '0.75rem'
                                        }}
                                    >
                                        Flag False Positive
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <style>{`
        .spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
};

export default Scanner;
