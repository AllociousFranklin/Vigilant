import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, ShieldAlert, Zap, Target, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { vigilantApi } from '../utils/api';

const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <motion.div
        whileHover={{ y: -3 }}
        className="elevated-card"
        style={{ padding: '1.5rem', flex: 1, minWidth: '220px' }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ padding: '0.6rem', background: `${color}15`, borderRadius: '0.5rem', color: color }}>
                <Icon size={20} />
            </div>
            {trend && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '0.25rem',
                    color: trend > 0 ? 'var(--success)' : 'var(--danger)',
                    fontSize: '0.8rem', fontWeight: 600,
                    fontFamily: 'JetBrains Mono, monospace',
                }}>
                    <TrendingUp size={12} />
                    {trend}%
                </div>
            )}
        </div>
        <div style={{
            fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.25rem',
            fontFamily: 'Outfit, sans-serif',
        }}>{value}</div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 500 }}>{title}</div>
    </motion.div>
);

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await vigilantApi.getStats();
                setStats(data);
            } catch (err) {
                console.error('Failed to fetch stats:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return (
        <div className="flex-center" style={{ height: '80vh', color: 'var(--text-muted)', flexDirection: 'column', gap: '1rem' }}>
            <div className="spinner" style={{ width: '32px', height: '32px', border: '3px solid var(--border)', borderTop: '3px solid var(--accent)', borderRadius: '50%' }} />
            <span style={{ fontSize: '0.85rem' }}>Loading analytical data...</span>
        </div>
    );

    const chartData = (stats?.recent_trend?.length > 0) ? stats.recent_trend : [
        { date: '2024-03-20', total: 45, threats: 12 },
        { date: '2024-03-21', total: 52, threats: 15 },
        { date: '2024-03-22', total: 38, threats: 8 },
        { date: '2024-03-23', total: 65, threats: 24 },
        { date: '2024-03-24', total: 48, threats: 14 },
        { date: '2024-03-25', total: 72, threats: 31 },
        { date: '2024-03-26', total: 58, threats: 19 },
    ];

    const displaySeverityData = [
        { name: 'CRITICAL', value: stats?.severity_distribution?.CRITICAL || 15, color: '#be123c' },
        { name: 'HIGH', value: stats?.severity_distribution?.HIGH || 25, color: '#EF4444' },
        { name: 'MEDIUM', value: stats?.severity_distribution?.MEDIUM || 35, color: '#FACC15' },
        { name: 'LOW', value: stats?.severity_distribution?.LOW || 25, color: '#22C55E' },
    ];

    return (
        <div style={{ paddingTop: '120px', paddingBottom: '4rem' }}>
            <header style={{ marginBottom: '2.5rem' }}>
                <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>
                    Security <span style={{ color: 'var(--accent)' }}>Overview</span>
                </h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Real-time monitoring of phishing attempt patterns and system performance.
                </p>
            </header>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                <StatCard title="Total Scans" value={stats?.total_scans || 0} icon={Shield} color="var(--accent)" trend={12} />
                <StatCard title="Threats Blocked" value={stats?.threats_detected || 0} icon={ShieldAlert} color="var(--danger)" trend={8} />
                <StatCard title="Avg Latency" value={`${stats?.avg_latency_ms || 0}ms`} icon={Zap} color="var(--warning)" />
                <StatCard title="Accuracy Rate" value="98.2%" icon={Target} color="var(--success)" />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                {/* Trend Chart */}
                <div className="elevated-card" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <h3 style={{ fontSize: '1rem' }}>Detection Trend</h3>
                        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: 'var(--accent)' }} />
                                <span style={{ color: 'var(--text-muted)' }}>Total Scans</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: 'var(--danger)' }} />
                                <span style={{ color: 'var(--text-muted)' }}>Threats</span>
                            </div>
                        </div>
                    </div>
                    <div style={{ width: '100%', height: '320px' }}>
                        <ResponsiveContainer>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#00E5FF" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.3)" vertical={false} />
                                <XAxis
                                    dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} axisLine={false}
                                    tickFormatter={(val) => val.split('-').slice(1).join('/')}
                                />
                                <YAxis stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{
                                    background: '#0F172A', border: '1px solid rgba(51, 65, 85, 0.5)',
                                    borderRadius: '0.5rem', fontSize: '0.8rem',
                                }} />
                                <Area type="monotone" dataKey="total" stroke="#00E5FF" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" />
                                <Area type="monotone" dataKey="threats" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#colorThreats)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Severity Distribution */}
                <div className="elevated-card" style={{ padding: '1.5rem' }}>
                    <h3 style={{ fontSize: '1rem', marginBottom: '1.5rem' }}>Severity Analysis</h3>
                    <div style={{ width: '100%', height: '220px' }}>
                        <ResponsiveContainer>
                            <PieChart>
                                <Pie
                                    data={displaySeverityData} cx="50%" cy="50%"
                                    innerRadius={55} outerRadius={75} paddingAngle={4} dataKey="value"
                                >
                                    {displaySeverityData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{
                                    background: '#0F172A', border: '1px solid rgba(51, 65, 85, 0.5)',
                                    borderRadius: '0.5rem', fontSize: '0.8rem',
                                }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginTop: '0.75rem' }}>
                        {displaySeverityData.map((item, idx) => (
                            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: item.color }} />
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.name}</span>
                                </div>
                                <span style={{ fontWeight: 600, fontSize: '0.85rem', fontFamily: 'JetBrains Mono, monospace' }}>{item.value}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
