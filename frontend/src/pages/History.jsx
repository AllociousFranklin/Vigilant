import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Filter, ExternalLink, Download } from 'lucide-react';
import { vigilantApi } from '../utils/api';

const History = () => {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);

    useEffect(() => {
        const fetchHistory = async () => {
            setLoading(true);
            try {
                const data = await vigilantApi.getHistory(page);
                setItems(data.items);
                setTotal(data.total);
            } catch (err) {
                console.error('Failed to fetch history:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, [page]);

    const getSeverityStyle = (severity) => {
        switch (severity) {
            case 'CRITICAL': return { color: '#be123c', background: 'rgba(190, 18, 60, 0.1)', border: '1px solid rgba(190, 18, 60, 0.2)' };
            case 'HIGH': return { color: '#EF4444', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' };
            case 'MEDIUM': return { color: '#FACC15', background: 'rgba(250, 204, 21, 0.1)', border: '1px solid rgba(250, 204, 21, 0.2)' };
            default: return { color: '#22C55E', background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)' };
        }
    };

    return (
        <div style={{ paddingTop: '120px', paddingBottom: '4rem' }}>
            <header style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>
                        Threat <span style={{ color: 'var(--accent)' }}>Log</span>
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        A historical audit of all artifacts processed by VIGILANT.
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button className="elevated-card" style={{
                        display: 'flex', alignItems: 'center', gap: '0.4rem',
                        padding: '0.6rem 1rem', color: 'var(--text-secondary)',
                        fontSize: '0.8rem', border: '1px solid var(--border)',
                    }}>
                        <Filter size={14} /> Filter
                    </button>
                    <button className="elevated-card" style={{
                        display: 'flex', alignItems: 'center', gap: '0.4rem',
                        padding: '0.6rem 1rem', color: 'var(--text-secondary)',
                        fontSize: '0.8rem', border: '1px solid var(--border)',
                    }}>
                        <Download size={14} /> Export CSV
                    </button>
                </div>
            </header>

            <div className="elevated-card" style={{ overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
                            {['TIMESTAMP', 'CHANNEL', 'ARTIFACT PREVIEW', 'RISK SCORE', 'SEVERITY', 'LATENCY', 'ACTION'].map(h => (
                                <th key={h} style={{
                                    padding: '1rem 1.25rem', color: 'var(--text-muted)', fontWeight: 600,
                                    fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em',
                                }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="7" style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading history records...</td></tr>
                        ) : items.length === 0 ? (
                            <tr><td colSpan="7" style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No detections found in history.</td></tr>
                        ) : (
                            items.map((item) => (
                                <tr key={item.scan_id} style={{ borderBottom: '1px solid var(--border-subtle)' }} className="table-row-hover">
                                    <td style={{ padding: '1rem 1.25rem', fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>
                                        {new Date(item.timestamp).toLocaleString()}
                                    </td>
                                    <td style={{ padding: '1rem 1.25rem' }}>
                                        <span style={{
                                            fontSize: '0.65rem', padding: '0.2rem 0.5rem',
                                            background: 'var(--accent-dim)', borderRadius: '100px',
                                            textTransform: 'uppercase', color: 'var(--accent)',
                                            fontWeight: 600, letterSpacing: '0.05em',
                                        }}>{item.channel}</span>
                                    </td>
                                    <td style={{ padding: '1rem 1.25rem', fontSize: '0.8rem', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                                        {item.input_preview}
                                    </td>
                                    <td style={{ padding: '1rem 1.25rem', fontWeight: 700, fontSize: '0.9rem', fontFamily: 'JetBrains Mono, monospace' }}>
                                        {item.risk_score}
                                    </td>
                                    <td style={{ padding: '1rem 1.25rem' }}>
                                        <span style={{
                                            fontSize: '0.65rem', fontWeight: 700, padding: '0.2rem 0.6rem',
                                            borderRadius: '4px', fontFamily: 'JetBrains Mono, monospace',
                                            ...getSeverityStyle(item.severity)
                                        }}>{item.severity}</span>
                                    </td>
                                    <td style={{ padding: '1rem 1.25rem', fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
                                        {item.latency_ms}ms
                                    </td>
                                    <td style={{ padding: '1rem 1.25rem' }}>
                                        <button style={{ background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer', padding: '0.25rem' }}>
                                            <ExternalLink size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center', gap: '0.75rem', alignItems: 'center' }}>
                <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="elevated-card"
                    style={{ padding: '0.6rem 1.25rem', opacity: page === 1 ? 0.4 : 1, fontSize: '0.8rem', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}
                >
                    Previous
                </button>
                <div className="flex-center" style={{ padding: '0 1rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontFamily: 'JetBrains Mono, monospace' }}>
                    Page {page}
                </div>
                <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={items.length < 20}
                    className="elevated-card"
                    style={{ padding: '0.6rem 1.25rem', opacity: items.length < 20 ? 0.4 : 1, fontSize: '0.8rem', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default History;
