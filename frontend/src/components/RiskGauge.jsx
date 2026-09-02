import React from 'react';
import { motion } from 'framer-motion';

const RiskGauge = ({ score = 0, title = "Risk Score", size = 180 }) => {
    const getColor = (s) => {
        if (s < 30) return 'var(--success)';
        if (s < 60) return 'var(--warning)';
        if (s < 85) return 'var(--danger)';
        return '#FF1E56';
    };

    const getLabel = (s) => {
        if (s < 30) return 'LOW RISK';
        if (s < 60) return 'MEDIUM RISK';
        if (s < 85) return 'HIGH RISK';
        return 'CRITICAL FRAUD';
    };

    const color = getColor(score);
    const label = getLabel(score);

    const strokeWidth = 14;
    const center = size / 2;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const dashOffset = circumference - (Math.min(Math.max(score, 0), 100) / 100) * circumference;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ position: 'relative', width: size, height: size }}>
                <svg width={size} height={size}>
                    <circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="transparent"
                        stroke="rgba(255, 255, 255, 0.06)"
                        strokeWidth={strokeWidth}
                    />
                    <motion.circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="transparent"
                        stroke={color}
                        strokeWidth={strokeWidth}
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: dashOffset }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${center} ${center})`}
                    />
                </svg>

                {/* Score text overlay */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}>
                    <motion.span
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        style={{
                            fontSize: size > 160 ? '2.4rem' : '1.8rem',
                            fontWeight: 800,
                            fontFamily: 'Outfit, sans-serif',
                            color: 'var(--text-primary)',
                            lineHeight: 1,
                        }}
                    >
                        {Math.round(score)}
                    </motion.span>
                    <span style={{
                        fontSize: '0.7rem',
                        color: 'var(--text-muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.1em',
                        marginTop: '4px',
                    }}>
                        / 100
                    </span>
                </div>
            </div>

            <div style={{ textAlign: 'center' }}>
                <div style={{
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: color,
                    letterSpacing: '0.05em',
                }}>
                    {label}
                </div>
                <div style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginTop: '2px',
                }}>
                    {title}
                </div>
            </div>
        </div>
    );
};

export default RiskGauge;
