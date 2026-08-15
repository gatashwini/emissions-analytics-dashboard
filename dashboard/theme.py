"""Shared visual theme: CSS injection, color tokens, and Plotly template."""

import streamlit as st

# Palette --------------------------------------------------------------
BG = "#12181F"
PANEL = "#1B232C"
PANEL_ALT = "#212B35"
BORDER = "#2B3742"
TEXT = "#E8EDF2"
MUTED = "#8A97A6"
AMBER = "#E8A33D"
TEAL = "#2FA88A"

# Categorical trio used for gas-type identity (validated: lightness band,
# chroma floor, and CVD/normal-vision separation all pass in dark mode).
GAS_COLORS = {"CO2": TEAL, "CH4": "#3E7CB1", "N2O": "#B98B2E"}

# Single-hue sequential ramp (magnitude), anchored on the teal accent.
TEAL_SEQUENTIAL = ["#17352E", "#1E4A40", "#256653", "#2FA88A"]

FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
    "family=IBM+Plex+Mono:wght@400;500;600;700&display=swap"
)

_CSS = f"""
<style>
@import url('{FONT_IMPORT_URL}');

:root {{
    --bg: {BG};
    --panel: {PANEL};
    --panel-alt: {PANEL_ALT};
    --border: {BORDER};
    --text: {TEXT};
    --muted: {MUTED};
    --amber: {AMBER};
    --teal: {TEAL};
    --mono: 'IBM Plex Mono', 'Courier New', monospace;
    --sans: 'Inter', -apple-system, sans-serif;
}}

html, body, .stApp {{
    background-color: var(--bg);
    color: var(--text);
    font-family: var(--sans);
}}

/* Tighten default block spacing */
.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}}

h1, h2, h3, h4, h5 {{
    font-family: var(--sans);
    color: var(--text);
    font-weight: 600;
}}

p, span, label, div {{
    font-family: var(--sans);
}}

[data-testid="stCaptionContainer"], .stCaption {{
    color: var(--muted) !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: var(--panel);
    border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    letter-spacing: 0.02em;
}}

/* Dividers */
hr {{
    border-color: var(--border);
    margin: 0.75rem 0;
}}

.section-divider {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 0.9rem 0 1.4rem 0;
}}

/* Dashboard header */
.dash-header {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-top: 3px solid var(--teal);
    border-radius: 6px;
    padding: 16px 22px;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.dash-header-left {{
    display: flex;
    align-items: center;
    gap: 14px;
}}
.dash-header-icon {{
    font-size: 1.7rem;
    line-height: 1;
}}
.dash-title {{
    font-family: var(--sans);
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: 0.01em;
}}
.dash-subtitle {{
    font-family: var(--sans);
    font-size: 0.85rem;
    color: var(--muted);
    margin-top: 2px;
}}
.dash-status {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    color: var(--muted);
    text-transform: uppercase;
    white-space: nowrap;
}}
.dash-status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--teal);
    box-shadow: 0 0 0 3px rgba(47, 168, 138, 0.18);
}}

/* Metric panels */
.metric-panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 18px;
    height: 100%;
}}
.metric-label {{
    font-family: var(--sans);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 8px;
}}
.metric-value {{
    font-family: var(--mono);
    font-size: 1.65rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
}}

/* Plotly chart panels */
[data-testid="stPlotlyChart"] {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px;
}}

/* Dataframe panel */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
}}

/* Bordered containers (st.container(border=True)) — reuse the panel look */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: var(--panel);
    border-color: var(--border) !important;
    border-radius: 6px;
}}

/* Q&A answer readout */
.qa-answer {{
    margin-top: 10px;
    padding: 12px 14px;
    background: var(--panel-alt);
    border-left: 3px solid var(--teal);
    border-radius: 4px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 0.9rem;
    line-height: 1.5;
}}
.qa-answer.is-error {{
    border-left-color: var(--amber);
    color: var(--muted);
}}

/* Small amber flag badge (e.g. facility drill-down anomaly flag) */
.badge-amber {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: rgba(232, 163, 61, 0.14);
    border: 1px solid var(--amber);
    border-radius: 999px;
    color: var(--amber);
    font-family: var(--sans);
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
}}

/* Alerts (info / success / warning) */
[data-testid="stAlertContainer"] {{
    background-color: var(--panel-alt) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px;
}}
[data-testid="stAlertContainer"] p {{
    color: var(--text) !important;
    font-family: var(--sans);
}}

/* Sidebar section labels */
.sidebar-kicker {{
    font-family: var(--mono);
    font-size: 0.68rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 2px;
}}
</style>
"""


def inject_theme() -> None:
    """Inject global CSS overrides. Call once, immediately after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def section_divider() -> None:
    """A subtle, themed divider used in place of st.divider()."""
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)


def dashboard_header(title: str, subtitle: str, icon: str = "⛽") -> None:
    """Render a bordered header panel with an accent bar, in place of st.title()."""
    st.markdown(
        f"""
        <div class="dash-header">
            <div class="dash-header-left">
                <div class="dash-header-icon">{icon}</div>
                <div>
                    <div class="dash-title">{title}</div>
                    <div class="dash-subtitle">{subtitle}</div>
                </div>
            </div>
            <div class="dash-status">
                <span class="dash-status-dot"></span>
                <span>Live feed &middot; nominal</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_layout_defaults() -> dict:
    """Shared Plotly layout kwargs matching the dark control-room palette."""
    return dict(
        template="plotly_dark",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        title_font=dict(family="Inter, sans-serif", color=TEXT, size=15),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, color=MUTED),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, color=MUTED),
    )
