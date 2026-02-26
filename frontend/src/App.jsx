import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Scanner from './pages/Scanner';
import History from './pages/History';
import About from './pages/About';

function App() {
    const [activePage, setActivePage] = useState('scanner');

    return (
        <div style={{ minHeight: '100vh' }}>
            <Navbar activePage={activePage} setActivePage={setActivePage} />

            <main className="container">
                {activePage === 'dashboard' && <Dashboard />}
                {activePage === 'scanner' && <Scanner />}
                {activePage === 'history' && <History />}
                {activePage === 'about' && <About />}
            </main>

            <footer style={{
                marginTop: '4rem',
                padding: '3rem 0',
                borderTop: '1px solid var(--border)',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.9rem'
            }}>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginBottom: '1rem' }}>
                    <span>Version 1.0.0</span>
                    <span>•</span>
                    <span>VIGILANT AI Detection Core</span>
                    <span>•</span>
                    <span>Secure By Design</span>
                </div>
                <p>&copy; 2024 VIGILANT. All rights reserved.</p>
            </footer>
        </div>
    );
}

export default App;
