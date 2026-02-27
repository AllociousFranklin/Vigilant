import React from 'react';
import { Shield, Cpu, Layers, Zap, Search, BarChart3 } from 'lucide-react';

const ArchitectureLayer = ({ number, title, description, icon: Icon, color, details }) => (
    <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{
                width: '3.5rem', height: '3.5rem', borderRadius: '0.75rem',
                background: `${color}15`, color: color,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: `1px solid ${color}25`,
                fontSize: '1.25rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace',
            }}>
                {number}
            </div>
            <div style={{ flex: 1, width: '1px', background: `linear-gradient(${color}25, transparent)`, marginTop: '0.5rem' }} />
        </div>
        <div className="elevated-card" style={{ padding: '1.5rem', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <Icon size={20} color={color} />
                <h3 style={{ fontSize: '1.15rem' }}>{title}</h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem', lineHeight: 1.6 }}>{description}</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.6rem' }}>
                {details.map((detail, idx) => (
                    <div key={idx} style={{
                        padding: '0.65rem 0.85rem', background: 'var(--bg-deep)', borderRadius: '0.4rem',
                        border: '1px solid var(--border-subtle)', fontSize: '0.8rem', color: 'var(--text-secondary)',
                        fontFamily: 'JetBrains Mono, monospace', fontWeight: 500,
                    }}>
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
            number: 1, title: "Ingestion & Validation",
            description: "Secure entry point for multi-channel artifacts. Standardizes disparate inputs into a common analytical format.",
            icon: Search, color: "#22D3EE",
            details: ["URL Canonicalization", "Input Sanitization", "Channel Identification", "Deduplication Hash"]
        },
        {
            number: 2, title: "Normalization Engine",
            description: "Critical de-obfuscation layer that strips polymorphic camouflage used by zero-day attackers.",
            icon: Layers, color: "#FACC15",
            details: ["Punycode Decoding", "Homoglyph Mapping", "Short URL Expansion", "HTML Tag Stripping"]
        },
        {
            number: 3, title: "Feature Extraction",
            description: "Converts raw artifacts into a 25-dimension feature vector. Replaces static blacklists with behavioral signals.",
            icon: Cpu, color: "#a855f7",
            details: ["URL Entropy Analysis", "NLP Urgency Scoring", "Brand Similarity Check", "Structural Mismatches"]
        },
        {
            number: 4, title: "Detection Core",
            description: "Ensemble ML inference using XGBoost and Random Forest architectures for sub-100ms real-time scoring.",
            icon: Shield, color: "#EF4444",
            details: ["Weighted Ensemble", "Adaptive Scoring", "Graceful Degradation", "Risk Tiering"]
        },
        {
            number: 5, title: "Explainability Engine",
            description: "Translates complex ML outputs into human-readable risk factors that security teams can act upon.",
            icon: BarChart3, color: "#22C55E",
            details: ["Feature Ranking", "Reason Generation", "Confidence Scoring", "Enterprise Reporting"]
        }
    ];

    return (
        <div style={{ paddingTop: '120px', paddingBottom: '4rem', maxWidth: '900px', margin: '0 auto' }}>
            <header style={{ textAlign: 'center', marginBottom: '4rem' }}>
                <h1 style={{ fontSize: '2.25rem', marginBottom: '0.75rem' }}>
                    The <span style={{ color: 'var(--accent)' }}>VIGILANT</span> Architecture
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', maxWidth: '600px', margin: '0 auto', lineHeight: 1.6 }}>
                    A real-time, adaptive, and explainable defense system against modern phishing polymorphic attacks.
                </p>
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
