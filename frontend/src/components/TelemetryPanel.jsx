import React from 'react';
import { Activity } from 'lucide-react';

const mockEvents = [
    { id: 1, label: 'Callback phishing — PayPal brand', action: 'BLOCKED', severity: 'critical', time: '2m ago' },
    { id: 2, label: 'Unicode spoof — microsoft[.]com', action: 'WARNED', severity: 'warning', time: '5m ago' },
    { id: 3, label: 'Zero-day document lure — .docx', action: 'FLAGGED', severity: 'critical', time: '12m ago' },
    { id: 4, label: 'SMS vishing attempt — toll notice', action: 'BLOCKED', severity: 'critical', time: '18m ago' },
    { id: 5, label: 'Legitimate login notification', action: 'ALLOWED', severity: 'safe', time: '24m ago' },
];

const TelemetryPanel = () => {
    const getActionColor = (action) => {
        switch (action) {
            case 'BLOCKED': return 'var(--danger)';
            case 'WARNED': return 'var(--warning)';
            case 'FLAGGED': return 'var(--warning)';
            case 'ALLOWED': return 'var(--success)';
            default: return 'var(--text-muted)';
        }
    };

    const getSeverityDotClass = (severity) => {
        switch (severity) {
            case 'critical': return 'critical';
            case 'warning': return 'warning';
            case 'safe': return 'operational';
            default: return 'operational';
        }
    };

    return (
        <div className="elevated-card" style={{ padding: '1.5rem', height: 'fit-content' }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                marginBottom: '1.25rem',
                paddingBottom: '1rem',
                borderBottom: '1px solid var(--border)',
            }}>
                <Activity size={16} color="var(--accent)" />
                <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    letterSpacing: '0.1em',
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                }}>Recent Threat Activity</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {mockEvents.map((event) => (
                    <div key={event.id} style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.75rem',
                        padding: '0.75rem',
                        background: 'var(--bg-deep)',
                        borderRadius: '0.5rem',
                        border: '1px solid var(--border-subtle)',
                        transition: 'border-color 0.2s ease',
                    }}>
                        <span
                            className={`status-dot ${getSeverityDotClass(event.severity)}`}
                            style={{ marginTop: '6px' }}
                        />
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{
                                fontSize: '0.8rem',
                                color: 'var(--text-primary)',
                                marginBottom: '0.25rem',
                                lineHeight: 1.4,
                            }}>
                                {event.label}
                            </div>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}>
                                <span style={{
                                    fontSize: '0.65rem',
                                    fontWeight: 700,
                                    letterSpacing: '0.06em',
                                    color: getActionColor(event.action),
                                    textTransform: 'uppercase',
                                    fontFamily: 'JetBrains Mono, monospace',
                                }}>
                                    {event.action}
                                </span>
                                <span style={{
                                    fontSize: '0.65rem',
                                    color: 'var(--text-muted)',
                                }}>
                                    {event.time}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TelemetryPanel;
