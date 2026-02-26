import React from 'react';
import { Shield, LayoutDashboard, Search, History, Info } from 'lucide-react';

const Navbar = ({ activePage, setActivePage }) => {
    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'scanner', label: 'Scanner', icon: Search },
        { id: 'history', label: 'History', icon: History },
        { id: 'about', label: 'About', icon: Info },
    ];

    return (
        <nav className="glass" style={{
            position: 'fixed',
            top: '1.5rem',
            left: '50%',
            transform: 'translateX(-50%)',
            width: 'max-content',
            padding: '0.5rem',
            display: 'flex',
            gap: '0.5rem',
            zIndex: 1000,
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                padding: '0 1rem',
                marginRight: '0.5rem',
                borderRight: '1px solid var(--border)',
            }}>
                <Shield size={24} color="var(--accent)" style={{ marginRight: '0.75rem' }} />
                <span style={{
                    fontFamily: 'Outfit',
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    color: 'var(--text-primary)'
                }}>VIGILANT</span>
            </div>

            {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;

                return (
                    <button
                        key={item.id}
                        onClick={() => setActivePage(item.id)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.6rem 1.2rem',
                            borderRadius: '0.75rem',
                            background: isActive ? 'var(--accent)' : 'transparent',
                            color: isActive ? 'var(--bg-deep)' : 'var(--text-secondary)',
                            border: 'none',
                            fontSize: '0.9rem',
                        }}
                    >
                        <Icon size={18} />
                        <span>{item.label}</span>
                    </button>
                );
            })}
        </nav>
    );
};

export default Navbar;
