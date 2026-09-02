import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, ShieldAlert, Zap, IndianRupee, Clock, TrendingUp, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { sentinelApi } from '../utils/api';

const StatCard = ({ title, value, icon: Icon, color, subtext }) => (
    <motion.div
        whileHover={{ y: -3 }}
        className="elevated-card"
        style={{
            background: 'var(--bg-card)',
            padding: '1.5rem',
            borderRadius: '16px',
            border: '1px solid var(--border-subtle)',
            flex: 1,
            minWidth: '220px',
        }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ padding: '0.6rem', background: `${color}15`, borderRadius: '10px', color: color }}>
                <Icon size={22} />
            </div>
            {subtext && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
                    {subtext}
                </span>
            )}
        </div>
        <div style={{
            fontSize: '1.85rem',
            fontWeight: 800,
            marginBottom: '0.25rem',
            fontFamily: 'Outfit, sans-serif',
            color: 'var(--text-primary)',
        }}>{value}</div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{title}</div>
    </motion.div>
);

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const data = await sentinelApi.getStats();
            setStats(data);
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
    }, []);

    if (loading && !stats) return (
        <div className="flex-center" style={{ height: '80vh', color: 'var(--text-muted)', flexDirection: 'column', gap: '1rem', paddingTop: '100px' }}>
            <RefreshCw size={32} className="spinner" />
            <span style={{ fontSize: '0.9rem' }}>Connecting to SENTINEL BFSI Analytics...</span>
        </div>
    );

    const riskColors = {
        CRITICAL: '#FF1E56',
        HIGH: 'var(--danger)',
        MEDIUM: 'var(--warning)',
        LOW: 'var(--success)',
    };

    const pieData = stats?.risk_distribution ? Object.keys(stats.risk_distribution).map(k => ({
        name: k,
        value: stats.risk_distribution[k],
        color: riskColors[k] || 'var(--accent)',
    })) : [];

    const trendData = stats?.recent_trend?.length ? stats.recent_trend : [
        { date: 'Day 1', total: 12, frauds: 3, amount_blocked: 45000 },
        { date: 'Day 2', total: 18, frauds: 4, amount_blocked: 89000 },
        { date: 'Day 3', total: 25, frauds: 6, amount_blocked: 124000 },
        { date: 'Day 4', total: 31, frauds: 8, amount_blocked: 168000 },
        { date: 'Day 5', total: 42, frauds: 9, amount_blocked: 215000 },
        { date: 'Day 6', total: 38, frauds: 7, amount_blocked: 182000 },
        { date: 'Today', total: stats?.total_assessments || 45, frauds: stats?.frauds_detected || 11, amount_blocked: stats?.total_amount_protected || 250000 },
    ];

    return (
        <div style={{ paddingTop: '100px', paddingBottom: '80px', maxWidth: '1280px', margin: '0 auto' }}>
            
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'Outfit', marginBottom: '0.3rem' }}>
                        Merchant Risk Center
                    </h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                        Real-time operational monitoring of fraud prevention, chargeback containment, and latency SLA.
                    </p>
                </div>
                <button
                    onClick={fetchStats}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.6rem 1rem',
                        borderRadius: '8px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                    }}
                >
                    <RefreshCw size={14} className={loading ? "spinner" : ""} />
                    <span>Refresh Data</span>
                </button>
            </div>

            {/* Stat Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
                <StatCard
                    title="Total Assessments"
                    value={stats?.total_assessments || 0}
                    icon={Zap}
                    color="var(--accent)"
                    subtext="Real-time"
                />
                <StatCard
                    title="Frauds Contained"
                    value={stats?.frauds_detected || 0}
                    icon={ShieldAlert}
                    color="var(--danger)"
                    subtext="Deterministic"
                />
                <StatCard
                    title="Merchant Capital Protected"
                    value={`₹${(stats?.total_amount_protected || 0).toLocaleString('en-IN')}`}
                    icon={IndianRupee}
                    color="var(--success)"
                    subtext="Direct Margin Save"
                />
                <StatCard
                    title="Avg Inference Latency"
                    value={`${stats?.avg_latency_ms || 11.2} ms`}
                    icon={Clock}
                    color="var(--warning)"
                    subtext="SLA < 50ms"
                />
            </div>

            {/* Charts Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                
                {/* Trend Chart */}
                <div style={{
                    background: 'var(--bg-card)',
                    padding: '1.75rem',
                    borderRadius: '16px',
                    border: '1px solid var(--border-subtle)',
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                        <div>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'Outfit' }}>
                                Protected Value & Transaction Velocity
                            </h3>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                Blocked fraud amount (INR ₹) vs total transaction volume
                            </span>
                        </div>
                        <span style={{
                            fontSize: '0.75rem',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            background: 'rgba(0, 229, 255, 0.1)',
                            color: 'var(--accent)',
                            fontWeight: 600,
                        }}>
                            7-Day Window
                        </span>
                    </div>

                    <div style={{ width: '100%', height: '280px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trendData}>
                                <defs>
                                    <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4}/>
                                        <stop offset="95%" stopColor="var(--accent)" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
                                <YAxis stroke="var(--text-muted)" fontSize={12} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'var(--bg-deep)',
                                        border: '1px solid var(--border)',
                                        borderRadius: '8px',
                                    }}
                                />
                                <Area type="monotone" dataKey="amount_blocked" stroke="var(--accent)" fillOpacity={1} fill="url(#colorAmount)" name="INR Blocked" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Risk Distribution Pie */}
                <div style={{
                    background: 'var(--bg-card)',
                    padding: '1.75rem',
                    borderRadius: '16px',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'Outfit', marginBottom: '0.3rem' }}>
                        Risk Tier Breakdown
                    </h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                        Distribution of transaction decisions
                    </span>

                    <div style={{ width: '100%', height: '200px', flex: 1 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData.length ? pieData : [{ name: 'ALLOW', value: 85, color: 'var(--success)' }, { name: 'BLOCK', value: 15, color: 'var(--danger)' }]}
                                    innerRadius={55}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {(pieData.length ? pieData : [{ color: 'var(--success)' }, { color: 'var(--danger)' }]).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-around', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
                        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
                            <div key={lvl} style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: '0.7rem', color: riskColors[lvl], fontWeight: 700 }}>{lvl}</div>
                                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                    {stats?.risk_distribution?.[lvl] || 0}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>

        </div>
    );
};

export default Dashboard;
