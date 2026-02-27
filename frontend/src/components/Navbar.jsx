import React, { useState, useEffect, useRef } from 'react';
import { Shield, LayoutDashboard, Search, Clock, Layers, FileText, ChevronDown } from 'lucide-react';

const Navbar = ({ activePage, setActivePage }) => {
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleBadgeClick = () => {
        if (activePage === 'dashboard') {
            setShowDropdown(!showDropdown);
        } else {
            setActivePage('dashboard');
        }
    };

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
            background: 'rgba(10, 15, 28, 0.92)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderBottom: '1px solid var(--border-subtle)',
            boxShadow: '0 1px 0 rgba(255, 255, 255, 0.04)',
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
                            className="nav-btn"
                            key={item.id}
                            onClick={() => setActivePage(item.id)}
                            style={{
                                position: 'relative',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '0.6rem 1.25rem',
                                borderRadius: '0.5rem',
                                background: isActive ? 'rgba(0, 229, 255, 0.04)' : 'transparent',
                                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                                border: 'none',
                                fontSize: '0.875rem',
                                fontWeight: isActive ? 600 : 500,
                                letterSpacing: '0.01em',
                                transition: 'color 0.15s ease-out, background 0.15s ease-out',
                                transform: 'none',
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

            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                position: 'relative'
            }} ref={dropdownRef}>
                <button
                    onClick={handleBadgeClick}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.4rem 1rem',
                        background: 'var(--accent-dim)',
                        border: '1px solid rgba(0, 229, 255, 0.12)',
                        borderRadius: '100px',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        letterSpacing: '0.08em',
                        color: 'var(--accent)',
                        textTransform: 'uppercase',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease-out',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0, 229, 255, 0.12)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'var(--accent-dim)'}
                >
                    <span className="status-dot operational"></span>
                    <span>Enterprise Console</span>
                    {activePage === 'dashboard' && (
                        <ChevronDown size={14} style={{
                            transform: showDropdown ? 'rotate(180deg)' : 'none',
                            transition: 'transform 0.2s ease'
                        }} />
                    )}
                </button>

                {/* System Status Dropdown */}
                {showDropdown && (
                    <div style={{
                        position: 'absolute',
                        top: '120%',
                        right: 0,
                        width: '240px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        borderRadius: '0.75rem',
                        padding: '1rem',
                        boxShadow: '0 12px 32px rgba(0,0,0,0.5)',
                        zIndex: 1001,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.75rem',
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>System Environment</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Production</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Policy Version</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>v4.0</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>SOC Mode</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: 700 }}>Active</span>
                        </div>
                    </div>
                )}
            </div>
        </nav>
    );
};

export default Navbar;
