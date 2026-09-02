import React from 'react';
import { ShieldCheck, Activity, LineChart, History, Award, CheckCircle2 } from 'lucide-react';

const Navbar = ({ activePage, setActivePage }) => {
    const navItems = [
        { id: 'scorer', label: 'Transaction Risk', icon: ShieldCheck },
        { id: 'dashboard', label: 'Merchant Monitor', icon: Activity },
        { id: 'history', label: 'Audit Trail', icon: History },
        { id: 'metrics', label: 'Honest Metrics', icon: Award, badge: 'Track 02' },
    ];

    return (
        <nav style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: '76px',
            background: 'rgba(10, 15, 28, 0.94)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderBottom: '1px solid var(--border-subtle)',
            boxShadow: '0 1px 0 rgba(255, 255, 255, 0.04)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 2.5rem',
            zIndex: 1000,
        }}>
            {/* Left: Brand */}
            <div 
                onClick={() => setActivePage('scorer')}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.85rem',
                    cursor: 'pointer',
                }}
            >
                <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, #00E5FF 0%, #2563EB 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 20px rgba(0, 229, 255, 0.3)',
                }}>
                    <ShieldCheck size={26} color="#0A0F1C" strokeWidth={2.5} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                    <span style={{
                        fontFamily: 'Outfit',
                        fontWeight: 800,
                        fontSize: '1.25rem',
                        letterSpacing: '0.12em',
                        background: 'linear-gradient(90deg, #FFFFFF 0%, #00E5FF 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}>SENTINEL</span>
                    <span style={{
                        fontSize: '0.65rem',
                        color: 'var(--text-muted)',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        fontWeight: 600,
                    }}>Razorpay AI Risk Manager</span>
                </div>
            </div>

            {/* Center: Navigation */}
            <div style={{
                display: 'flex',
                gap: '0.35rem',
                alignItems: 'center',
                background: 'rgba(15, 23, 42, 0.6)',
                padding: '4px',
                borderRadius: '12px',
                border: '1px solid var(--border-subtle)',
            }}>
                {navItems.map((item) => {
                    const isActive = activePage === item.id;
                    const Icon = item.icon;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActivePage(item.id)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0.55rem 1.1rem',
                                borderRadius: '8px',
                                background: isActive ? 'linear-gradient(135deg, rgba(0, 229, 255, 0.15) 0%, rgba(37, 99, 235, 0.15) 100%)' : 'transparent',
                                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                                border: isActive ? '1px solid rgba(0, 229, 255, 0.3)' : '1px solid transparent',
                                fontSize: '0.85rem',
                                fontWeight: isActive ? 600 : 500,
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                            }}
                        >
                            <Icon size={16} />
                            <span>{item.label}</span>
                            {item.badge && (
                                <span style={{
                                    fontSize: '0.65rem',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    background: isActive ? 'var(--accent)' : 'rgba(0, 229, 255, 0.1)',
                                    color: isActive ? '#0A0F1C' : 'var(--accent)',
                                    fontWeight: 700,
                                }}>{item.badge}</span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Right: Security & Compliance Tag */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0.85rem',
                    borderRadius: '20px',
                    background: 'rgba(22, 199, 132, 0.08)',
                    border: '1px solid rgba(22, 199, 132, 0.25)',
                    fontSize: '0.75rem',
                    color: 'var(--success)',
                    fontWeight: 600,
                }}>
                    <CheckCircle2 size={14} />
                    <span>DEFENSE-ONLY (STRICT)</span>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
