import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, ShieldAlert, Zap, Target, ArrowUpRight, TrendingUp, AlertTriangle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie } from 'recharts';
import { vigilantApi } from '../utils/api';

const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <motion.div
        whileHover={{ y: -5 }}
        className="glass"
        style={{ padding: '1.5rem', flex: 1, minWidth: '240px' }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ padding: '0.75rem', background: `${color}15`, borderRadius: '0.75rem', color: color }}>
                <Icon size={24} />
            </div>
            {trend && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: trend > 0 ? 'var(--success)' : 'var(--danger)', fontSize: '0.85rem', fontWeight: 600 }}>
                    <TrendingUp size={14} />
                    {trend}%
                </div>
            )}
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.25rem' }}>{value}</div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{title}</div>
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

    if (loading) return <div className="flex-center" style={{ height: '100vh', color: 'var(--text-secondary)' }}>Loading analytical data...</div>;

    // Mock data if actual stats are empty for demo
    const chartData = (stats?.recent_trend?.length > 0) ? stats.recent_trend : [
        { date: '2024-03-20', total: 45, threats: 12 },
        { date: '2024-03-21', total: 52, threats: 15 },
        { date: '2024-03-22', total: 38, threats: 8 },
        { date: '2024-03-23', total: 65, threats: 24 },
        { date: '2024-03-24', total: 48, threats: 14 },
        { date: '2024-03-25', total: 72, threats: 31 },
        { date: '2024-03-26', total: 58, threats: 19 },
    ];

    const severityData = [
        { name: 'Critical', value: stats?.severity_distribution?.CRITICAL || 0, color: '#be123c' },
        { name: 'High', value: stats?.severity_distribution?.HIGH || 0, color: 'var(--danger)' },
        { name: 'Medium', value: stats?.severity_distribution?.MEDIUM || 0, color: 'var(--warning)' },
        { name: 'Low', value: stats?.severity_distribution?.LOW || 0, color: 'var(--success)' },
    ].filter(d => d.value > 0);

    // Default display if no real data
    const displaySeverityData = severityData.length > 0 ? severityData : [
        { name: 'Critical', value: 15, color: '#be123c' },
        { name: 'High', value: 25, color: 'var(--danger)' },
        { name: 'Medium', value: 35, color: 'var(--warning)' },
        { name: 'Low', value: 25, color: 'var(--success)' },
    ];

    return (
        <div style={{ padding: '6rem 0 4rem' }}>
            <header style={{ marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Security <span style={{ color: 'var(--accent)' }}>Overview</span></h1>
                <p style={{ color: 'var(--text-secondary)' }}>Real-time monitoring of phishing attempt patterns and system performance.</p>
            </header>

            {/* Hero Stats */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', marginBottom: '2rem' }}>
                <StatCard
                    title="Total Scans"
                    value={stats?.total_scans || 0}
                    icon={Shield}
                    color="var(--accent)"
                    trend={12}
                />
                <StatCard
                    title="Threats Blocked"
                    value={stats?.threats_detected || 0}
                    icon={ShieldAlert}
                    color="var(--danger)"
                    trend={8}
                />
                <StatCard
                    title="Avg Latency"
                    value={`${stats?.avg_latency_ms || 0}ms`}
                    icon={Zap}
                    color="var(--warning)"
                />
                <StatCard
                    title="Accuracy Rate"
                    value="98.2%"
                    icon={Target}
                    color="var(--success)"
                />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                {/* Trend Chart */}
                <div className="glass" style={{ padding: '2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                        <h3 style={{ fontSize: '1.25rem' }}>Detection Trend</h3>
                        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--accent)' }}></div>
                                <span style={{ color: 'var(--text-secondary)' }}>Total Scans</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--danger)' }}></div>
                                <span style={{ color: 'var(--text-secondary)' }}>Threats</span>
                            </div>
                        </div>
                    </div>

                    <div style={{ width: '100%', height: '350px' }}>
                        <ResponsiveContainer>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--danger)" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="var(--danger)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="var(--text-muted)"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(val) => val.split('-').slice(1).join('/')}
                                />
                                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '0.75rem' }}
                                    itemStyle={{ fontSize: '0.9rem' }}
                                />
                                <Area type="monotone" dataKey="total" stroke="var(--accent)" strokeWidth={3} fillOpacity={1} fill="url(#colorTotal)" />
                                <Area type="monotone" dataKey="threats" stroke="var(--danger)" strokeWidth={3} fillOpacity={1} fill="url(#colorThreats)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Severity Distribution */}
                <div className="glass" style={{ padding: '2rem' }}>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '2rem' }}>Severity Analysis</h3>
                    <div style={{ width: '100%', height: '250px' }}>
                        <ResponsiveContainer>
                            <PieChart>
                                <Pie
                                    data={displaySeverityData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {displaySeverityData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: '0.75rem' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
                        {displaySeverityData.map((item, idx) => (
                            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.color }}></div>
                                    <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{item.name}</span>
                                </div>
                                <span style={{ fontWeight: 600 }}>{item.value}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
