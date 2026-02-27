import React from 'react';
import { Shield, LayoutDashboard, Search, Clock, Layers, FileText } from 'lucide-react';

const Navbar = ({ activePage, setActivePage }) => {
    const navItems = [
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'scanner', label: 'Scanner' },
        { id: 'history', label: 'Threat Log' },
        { id: 'about', label: 'Architecture' },
    ];

    return (
        <nav style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            height: '80px',
            background: 'rgba(11, 15, 20, 0.85)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 3rem',
            zIndex: 1000,
        }}>
            {/* Left: Brand */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
            }}>
                <Shield size={26} color="var(--accent)" strokeWidth={2.5} />
                <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                    <span style={{
                        fontFamily: 'Outfit',
                        fontWeight: 700,
                        fontSize: '1.15rem',
                        letterSpacing: '0.15em',
                        color: 'var(--text-primary)'
                    }}>VIGILANT</span>
                    <span style={{
                        fontSize: '0.65rem',
                        color: 'var(--text-muted)',
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                    }}>Policy-Enforced AI Defense</span>
                </div>
            </div>

            {/* Center: Navigation */}
            <div style={{
                display: 'flex',
                gap: '0.25rem',
                alignItems: 'center',
            }}>
                {navItems.map((item) => {
                    const isActive = activePage === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActivePage(item.id)}
                            style={{
                                position: 'relative',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0.6rem 1.25rem',
                                borderRadius: '0.5rem',
                                background: 'transparent',
                                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                                border: 'none',
                                fontSize: '0.875rem',
                                fontWeight: isActive ? 600 : 500,
                                letterSpacing: '0.01em',
                                transition: 'color 0.2s ease',
                            }}
                        >
                            <span>{item.label}</span>
                            {/* Subtle cyan underline indicator */}
                            {isActive && (
                                <div style={{
                                    position: 'absolute',
                                    bottom: '-2px',
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    width: '60%',
                                    height: '2px',
                                    background: 'var(--accent)',
                                    borderRadius: '1px',
                                    boxShadow: '0 0 8px var(--accent-glow)',
                                }} />
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Right: Environment Badge */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 1rem',
                    background: 'var(--accent-dim)',
                    border: '1px solid rgba(34, 211, 238, 0.15)',
                    borderRadius: '100px',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    color: 'var(--accent)',
                    textTransform: 'uppercase',
                }}>
                    <span className="status-dot operational" style={{ width: '6px', height: '6px' }}></span>
                    Enterprise Console
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
