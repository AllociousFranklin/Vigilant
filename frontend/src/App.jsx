import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Scanner from './pages/Scanner';
import History from './pages/History';
import About from './pages/About';

function App() {
    const [activePage, setActivePage] = useState('scanner');

    return (
        <div style={{ minHeight: '100vh', position: 'relative' }}>
            <Navbar activePage={activePage} setActivePage={setActivePage} />

            <main className="container">
                {activePage === 'dashboard' && <Dashboard />}
                {activePage === 'scanner' && <Scanner />}
                {activePage === 'history' && <History />}
                {activePage === 'about' && <About />}
            </main>

            <footer style={{
                marginTop: '120px',
                padding: '2rem 0',
                borderTop: '1px solid var(--border-subtle)',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                letterSpacing: '0.03em',
            }}>
                <div className="container">
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginBottom: '0.75rem' }}>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>v2.0.0</span>
                        <span style={{ color: 'var(--border)' }}>•</span>
                        <span>VIGILANT AI Detection Core</span>
                        <span style={{ color: 'var(--border)' }}>•</span>
                        <span>Secure By Design</span>
                    </div>
                    <p>&copy; 2024 VIGILANT. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
}

export default App;
