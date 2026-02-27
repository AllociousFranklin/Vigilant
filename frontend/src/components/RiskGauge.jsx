import React from 'react';
import { motion } from 'framer-motion';

const RiskGauge = ({ score }) => {
    // Map score to color
    const getColor = (s) => {
        if (s < 35) return 'var(--success)';
        if (s < 65) return 'var(--warning)';
        if (s < 85) return 'var(--danger)';
        return '#be123c'; // Extra dark red for CRITICAL
    };

    const getLabel = (s) => {
        if (s < 35) return 'LOW (Advisory)';
        if (s < 65) return 'MEDIUM (Suspicious)';
        if (s < 85) return 'HIGH (Malicious)';
        return 'CRITICAL (Severe Threat)';
    };

    const color = getColor(score);
    const label = getLabel(score);

    // SVG properties
    const size = 200;
    const strokeWidth = 15;
    const center = size / 2;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const dashOffset = circumference - (score / 100) * circumference;

    return (
        <div className="flex-center" style={{ flexDirection: 'column', gap: '1rem' }}>
            <div style={{ position: 'relative', width: size, height: size }}>
                {/* Background track */}
                <svg width={size} height={size}>
                    <circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="transparent"
                        stroke="var(--bg-surface)"
                        strokeWidth={strokeWidth}
                    />
                    {/* Animated score ring */}
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
                        transition={{ duration: 1.5, ease: "easeOut" }}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${center} ${center})`}
                        style={{}}
                    />
                </svg>

                {/* Score display */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <motion.span
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        style={{
                            fontSize: '3.5rem',
                            fontWeight: 700,
                            fontFamily: 'Outfit',
                            color: 'var(--text-primary)'
                        }}
                    >
                        {Math.round(score)}
                    </motion.span>
                    <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.8 }}
                        style={{
                            fontSize: '1rem',
                            fontWeight: 600,
                            color: color,
                            letterSpacing: '0.1em'
                        }}
                    >
                        {label} RISK
                    </motion.span>
                </div>
            </div>
        </div>
    );
};

export default RiskGauge;
