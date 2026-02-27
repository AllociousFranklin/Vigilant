import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { History as HistoryIcon, Filter, ExternalLink, Download, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { vigilantApi } from '../utils/api';

const History = () => {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const isFetchingRef = useRef(false);

    const fetchHistory = useCallback(async ({ silent = false } = {}) => {
        if (isFetchingRef.current) return;
        isFetchingRef.current = true;

        if (!silent) setLoading(true);
        try {
            const data = await vigilantApi.getHistory(page);
            setItems(data.items);
            setTotal(data.total);
        } catch (err) {
            console.error('Failed to fetch history:', err);
        } finally {
            if (!silent) setLoading(false);
            isFetchingRef.current = false;
        }
    }, [page]);

    useEffect(() => {
        fetchHistory();
    }, [fetchHistory]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            if (document.visibilityState === 'visible') {
                fetchHistory({ silent: true });
            }
        }, 5000);

        return () => clearInterval(intervalId);
    }, [fetchHistory]);

    const getSeverityStyle = (severity) => {
        switch (severity) {
            case 'CRITICAL': return { color: '#be123c', background: '#be123c15', border: '1px solid #be123c30' };
            case 'HIGH': return { color: 'var(--danger)', background: 'var(--danger-glow)', border: '1px solid var(--danger)30' };
            case 'MEDIUM': return { color: 'var(--warning)', background: 'var(--warning)15', border: '1px solid var(--warning)30' };
            default: return { color: 'var(--success)', background: 'var(--success)15', border: '1px solid var(--success)30' };
        }
    };

    return (
        <div style={{ padding: '6rem 0 4rem' }}>
            <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                    <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Detection <span style={{ color: 'var(--accent)' }}>Logs</span></h1>
                    <p style={{ color: 'var(--text-secondary)' }}>A historical audit of all artifacts processed by VIGILANT.</p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className="glass" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.25rem', color: 'var(--text-secondary)' }}>
                        <Filter size={18} />
                        Filter
                    </button>
                    <button className="glass" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.25rem', color: 'var(--text-secondary)' }}>
                        <Download size={18} />
                        Export CSV
                    </button>
                </div>
            </header>

            <div className="glass" style={{ overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>TIMESTAMP</th>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>CHANNEL</th>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>ARTIFACT PREVIEW</th>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>RISK SCORE</th>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>SEVERITY</th>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>LATENCY</th>
                            <th style={{ padding: '1.25rem 1.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.85rem' }}>ACTION</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="7" style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading history records...</td></tr>
                        ) : items.length === 0 ? (
                            <tr><td colSpan="7" style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No detections found in history.</td></tr>
                        ) : (
                            items.map((item, idx) => (
                                <tr key={item.scan_id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.2s' }} className="table-row-hover">
                                    <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                        {new Date(item.timestamp).toLocaleString()}
                                    </td>
                                    <td style={{ padding: '1.25rem 1.5rem' }}>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            padding: '0.2rem 0.6rem',
                                            background: 'var(--bg-surface)',
                                            borderRadius: '100px',
                                            textTransform: 'uppercase',
                                            color: 'var(--accent)'
                                        }}>
                                            {item.channel}
                                        </span>
                                    </td>
                                    <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {item.input_preview}
                                    </td>
                                    <td style={{ padding: '1.25rem 1.5rem', fontWeight: 700 }}>
                                        {item.risk_score}
                                    </td>
                                    <td style={{ padding: '1.25rem 1.5rem' }}>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            fontWeight: 700,
                                            padding: '0.3rem 0.8rem',
                                            borderRadius: '0.5rem',
                                            ...getSeverityStyle(item.severity)
                                        }}>
                                            {item.severity}
                                        </span>
                                    </td>
                                    <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                        {item.latency_ms}ms
                                    </td>
                                    <td style={{ padding: '1.25rem 1.5rem' }}>
                                        <button style={{ background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer' }}>
                                            <ExternalLink size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="glass"
                    style={{ padding: '0.75rem 1.5rem', opacity: page === 1 ? 0.5 : 1 }}
                >
                    Previous
                </button>
                <div className="flex-center" style={{ padding: '0 1rem', color: 'var(--text-secondary)' }}>Page {page}</div>
                <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={items.length < 20}
                    className="glass"
                    style={{ padding: '0.75rem 1.5rem', opacity: items.length < 20 ? 0.5 : 1 }}
                >
                    Next
                </button>
            </div>

            <style>{`
        .table-row-hover:hover {
          background: rgba(255, 255, 255, 0.02);
        }
      `}</style>
        </div>
    );
};

export default History;
