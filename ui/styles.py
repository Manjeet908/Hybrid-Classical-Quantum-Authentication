"""
Quantum-themed custom CSS styles and UI token definitions.
"""

QUANTUM_CSS = """
<style>
    /* Global Background and Typography */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Outfit:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    code, pre, [class*="stCode"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Custom Header Banner */
    .quantum-hero {
        background: linear-gradient(135deg, rgba(16, 24, 48, 0.95) 0%, rgba(11, 15, 25, 0.95) 100%);
        border: 1px solid rgba(0, 245, 212, 0.25);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 245, 212, 0.08);
        backdrop-filter: blur(8px);
    }
    
    .quantum-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00f5d4 0%, #7b2cbf 50%, #f72585 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }

    .quantum-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 0;
    }

    /* Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(18, 24, 41, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 245, 212, 0.4);
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-sub {
        font-size: 0.8rem;
        margin-top: 4px;
    }

    /* Badges */
    .badge-secure {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warning {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.35);
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-compromised {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.35);
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* Pipeline Step Box */
    .pipeline-step {
        background: rgba(15, 23, 42, 0.6);
        border-left: 3px solid #00f5d4;
        border-radius: 0 10px 10px 0;
        padding: 12px 18px;
        margin-bottom: 12px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(18, 24, 41, 0.6) !important;
        border-radius: 8px !important;
    }
</style>
"""

def render_hero(title: str, subtitle: str) -> str:
    """Renders the top hero banner."""
    return f"""
    <div class="quantum-hero">
        <div class="quantum-title">⚛️ {title}</div>
        <div class="quantum-subtitle">{subtitle}</div>
    </div>
    """

def render_badge(status: str) -> str:
    """Renders a status badge."""
    status_upper = status.upper()
    if status_upper == "SECURE":
        return '<span class="badge-secure">● SECURE KEY ESTABLISHED</span>'
    elif status_upper == "WARNING":
        return '<span class="badge-warning">▲ ELEVATED NOISE / CAUTION</span>'
    else:
        return '<span class="badge-compromised">✖ EAVESDROPPER / COMPROMISED</span>'
