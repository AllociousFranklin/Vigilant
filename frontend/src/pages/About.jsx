import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Cpu, Layers, Zap, Search, BarChart3, Lock, MessageSquare } from 'lucide-react';

const ArchitectureLayer = ({ number, title, description, icon: Icon, color, details }) => (
    <div style={{ display: 'flex', gap: '2rem', marginBottom: '3rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{
                width: '4rem',
                height: '4rem',
                borderRadius: '1rem',
                background: `${color}15`,
                color: color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `1px solid ${color}30`,
                fontSize: '1.5rem',
                fontWeight: 700,
                fontFamily: 'Outfit'
            }}>
                {number}
            </div>
            <div style={{ flex: 1, width: '2px', background: `linear-gradient(${color}30, transparent)`, marginTop: '0.5rem' }}></div>
        </div>
        <div className="glass" style={{ padding: '2rem', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <Icon size={24} color={color} />
                <h3 style={{ fontSize: '1.5rem' }}>{title}</h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', marginBottom: '1.5rem' }}>{description}</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                {details.map((detail, idx) => (
                    <div key={idx} style={{ padding: '1rem', background: 'var(--bg-deep)', borderRadius: '0.75rem', border: '1px solid var(--border)', fontSize: '0.9rem' }}>
                        {detail}
                    </div>
                ))}
            </div>
        </div>
    </div>
);

const About = () => {
    const layers = [
        {
            number: 1,
            title: "Ingestion & Validation",
            description: "Secure entry point for multi-channel artifacts. Standardizes disparate inputs into a common analytical format.",
            icon: Search,
            color: "var(--accent)",
            details: ["URL Canonicalization", "Input Sanitization", "Channel Identification", "Deduplication Hash"]
        },
        {
            number: 2,
            title: "Normalization Engine",
            description: "Critical de-obfuscation layer that strips polymorphic camouflage used by zero-day attackers.",
            icon: Layers,
            color: "var(--warning)",
            details: ["Punycode Decoding", "Homoglyph Mapping", "Short URL Expansion", "HTML Tag Stripping"]
        },
        {
            number: 3,
            title: "Feature Extraction",
            description: "Converts raw artifacts into a 25-dimension feature vector. This replaces static blacklists with behavioral signals.",
            icon: Cpu,
            color: "#a855f7",
            details: ["URL Entropy Analysis", "NLP Urgency Scoring", "Brand Similarity Check", "Structural Mismatches"]
        },
        {
            number: 4,
            title: "Detection Core",
            description: "Ensemble ML inference using XGBoost and Random Forest architectures for sub-100ms real-time scoring.",
            icon: Shield,
            color: "var(--danger)",
            details: ["Weighted Ensemble", "Adaptive Scoring", "Graceful Degradation", "Risk Tiering"]
        },
        {
            number: 5,
            title: "Explainability Engine",
            description: "Translates complex ML outputs into human-readable risk factors that security teams can act upon.",
            icon: BarChart3,
            color: "var(--success)",
            details: ["Feature Ranking", "Reason Generation", "Confidence Scoring", "Enterprise Reporting"]
        }
    ];

    return (
        <div style={{ padding: '6rem 0 4rem', maxWidth: '1000px', margin: '0 auto' }}>
            <header style={{ textAlign: 'center', marginBottom: '4rem' }}>
                <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>The <span style={{ color: 'var(--accent)' }}>VIGILANT</span> Architecture</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem' }}>A real-time, adaptive, and explainable defense system against modern phishing polymorphic attacks.</p>
            </header>

            <div style={{ position: 'relative' }}>
                {layers.map((layer, index) => (
                    <ArchitectureLayer key={index} {...layer} />
                ))}
            </div>
        </div>
    );
};

export default About;
