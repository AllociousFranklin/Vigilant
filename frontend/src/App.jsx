import React, { useState } from 'react';
import Navbar from './components/Navbar';
import TransactionScorer from './pages/TransactionScorer';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Metrics from './pages/Metrics';

function App() {
    const [activePage, setActivePage] = useState('scorer');

    return (
        <div style={{ minHeight: '100vh', position: 'relative' }}>
            <Navbar activePage={activePage} setActivePage={setActivePage} />

            <main className="container">
                {activePage === 'scorer' && <TransactionScorer />}
                {activePage === 'dashboard' && <Dashboard />}
                {activePage === 'history' && <History />}
                {activePage === 'metrics' && <Metrics />}
            </main>

            <footer style={{
                marginTop: '100px',
                padding: '2rem 0',
                borderTop: '1px solid var(--border-subtle)',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                letterSpacing: '0.03em',
            }}>
                <div className="container">
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginBottom: '0.75rem' }}>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>v1.0.0</span>
                        <span style={{ color: 'var(--border)' }}>•</span>
                        <span>SENTINEL AI Risk Manager</span>
                        <span style={{ color: 'var(--border)' }}>•</span>
                        <span>Razorpay Buildathon Track 02</span>
                        <span style={{ color: 'var(--border)' }}>•</span>
                        <span>Strictly Defense-Only</span>
                    </div>
                    <p>&copy; 2026 SENTINEL. Defending Indian BFSI Merchant Margins.</p>
                </div>
            </footer>
        </div>
    );
}

export default App;
