"""
SportRadar Tennis Analytics Dashboard — v2.0
Premium analytics dashboard with dark theme, interactive Plotly charts,
and advanced analytics capabilities.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from tennis_analytics.config import get_settings
from tennis_analytics.database import (
    create_database_engine,
    get_table_counts,
    query_dataframe,
)
from tennis_analytics.pipeline import run_refresh
from tennis_analytics.queries import EXTRA_INSIGHT_QUERIES, REQUIRED_QUERIES, QuerySpec

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Tennis Analytics",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Settings & engine
# ---------------------------------------------------------------------------
settings = get_settings()


@st.cache_resource(show_spinner=False)
def get_engine(database_url: str):
    return create_database_engine(database_url)


engine = get_engine(settings.database_url)


@st.cache_data(ttl=300, show_spinner=False)
def run_query(database_url: str, sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    eng = create_database_engine(database_url)
    return query_dataframe(eng, sql, params)


def metric_value(sql: str, params: dict[str, Any] | None = None) -> Any:
    df = run_query(settings.database_url, sql, params)
    if df.empty:
        return 0
    return df.iloc[0, 0]


def selectable_values(sql: str, label: str = "All") -> list[str]:
    df = run_query(settings.database_url, sql)
    values = [str(v) for v in df.iloc[:, 0].dropna().tolist()]
    return [label] + values


# ---------------------------------------------------------------------------
# Import advanced queries (graceful fallback)
# ---------------------------------------------------------------------------
try:
    from tennis_analytics.queries import ADVANCED_QUERIES
except ImportError:
    ADVANCED_QUERIES = {}


# ---------------------------------------------------------------------------
# Plotly theme
# ---------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"

COLOR_PALETTE = [
    "#00d4ff", "#7c3aed", "#f59e0b", "#10b981", "#ef4444",
    "#ec4899", "#8b5cf6", "#06b6d4", "#f97316", "#14b8a6",
]

GRADIENT_COLORS = [
    ["#667eea", "#764ba2"],
    ["#00d4ff", "#0891b2"],
    ["#f59e0b", "#ef4444"],
    ["#10b981", "#059669"],
    ["#ec4899", "#8b5cf6"],
    ["#f97316", "#dc2626"],
    ["#06b6d4", "#3b82f6"],
    ["#a855f7", "#6366f1"],
]


def plotly_layout(**kwargs: Any) -> dict[str, Any]:
    """Standard dark layout for Plotly charts."""
    defaults = {
        "template": PLOTLY_TEMPLATE,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, sans-serif", "color": "#e2e8f0"},
        "margin": {"t": 40, "b": 40, "l": 40, "r": 40},
        "colorway": COLOR_PALETTE,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# Premium CSS Theme
# ---------------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ===== ROOT VARIABLES ===== */
:root {
    --bg-primary: #0a0a1a;
    --bg-secondary: #111128;
    --bg-card: rgba(255, 255, 255, 0.04);
    --bg-card-hover: rgba(255, 255, 255, 0.08);
    --border-color: rgba(255, 255, 255, 0.08);
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-cyan: #00d4ff;
    --accent-purple: #7c3aed;
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-cyan: linear-gradient(135deg, #00d4ff 0%, #0891b2 100%);
    --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
    --glass-bg: rgba(17, 17, 40, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
    --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.4);
    --shadow-glow-cyan: 0 0 30px rgba(0, 212, 255, 0.15);
    --shadow-glow-purple: 0 0 30px rgba(124, 58, 237, 0.15);
}

/* ===== GLOBAL ===== */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(10, 10, 26, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid var(--border-color) !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] .stRadio label {
    color: var(--text-secondary) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--accent-cyan) !important;
}

/* ===== METRIC CARDS ===== */
div[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-lg) !important;
}

div[data-testid="stMetric"]:hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--accent-cyan) !important;
    box-shadow: var(--shadow-glow-cyan) !important;
    transform: translateY(-2px) !important;
}

div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 800 !important;
    font-size: 2rem !important;
}

/* ===== GLASSMORPHISM CARDS ===== */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 1.8rem;
    box-shadow: var(--shadow-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    border-color: rgba(0, 212, 255, 0.3);
    box-shadow: var(--shadow-glow-cyan);
    transform: translateY(-2px);
}

/* ===== GRADIENT METRIC CARDS ===== */
.gradient-metric {
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    color: white;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.gradient-metric:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.gradient-metric::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
}

.gradient-metric .metric-icon {
    font-size: 2.2rem;
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.gradient-metric .metric-value {
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1.1;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.gradient-metric .metric-label {
    font-size: 0.78rem;
    font-weight: 500;
    opacity: 0.85;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.4rem;
}

.gradient-metric .metric-sub {
    font-size: 0.72rem;
    opacity: 0.65;
    margin-top: 0.2rem;
}

/* ===== PAGE TITLE ===== */
.page-title {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #f59e0b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
    letter-spacing: -0.02em;
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-weight: 400;
    margin-bottom: 1.5rem;
}

/* ===== SECTION HEADERS ===== */
.section-header {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 1.5rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent-cyan);
    display: inline-block;
}

/* ===== DATAFRAME / TABLES ===== */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-color) !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    background: var(--gradient-primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5) !important;
}

/* ===== DOWNLOAD BUTTONS ===== */
.stDownloadButton > button {
    background: rgba(0, 212, 255, 0.1) !important;
    color: var(--accent-cyan) !important;
    border: 1px solid var(--accent-cyan) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stDownloadButton > button:hover {
    background: rgba(0, 212, 255, 0.2) !important;
    transform: translateY(-1px) !important;
}

/* ===== INPUTS ===== */
.stSelectbox, .stTextInput, .stNumberInput, .stSlider {
    color: var(--text-primary) !important;
}

[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

.stTextInput > div > div > input {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

/* ===== EXPANDER ===== */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    padding: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

.stTabs [aria-selected="true"] {
    background: var(--gradient-primary) !important;
    color: white !important;
}

/* ===== DIVIDER ===== */
hr {
    border-color: var(--border-color) !important;
    margin: 1.5rem 0 !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--text-muted); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

/* ===== ANIMATIONS ===== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.animate-in {
    animation: fadeInUp 0.5s ease-out forwards;
}

/* ===== BADGE ===== */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-cyan { background: rgba(0,212,255,0.15); color: #00d4ff; }
.badge-purple { background: rgba(124,58,237,0.15); color: #a78bfa; }
.badge-green { background: rgba(16,185,129,0.15); color: #34d399; }
.badge-amber { background: rgba(245,158,11,0.15); color: #fbbf24; }
.badge-rose { background: rgba(244,63,94,0.15); color: #fb7185; }

/* ===== SIDEBAR BRANDING ===== */
.sidebar-brand {
    text-align: center;
    padding: 1.5rem 1rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.sidebar-brand .brand-icon {
    font-size: 3rem;
    margin-bottom: 0.3rem;
    filter: drop-shadow(0 4px 8px rgba(0,212,255,0.3));
}

.sidebar-brand .brand-title {
    font-size: 1.1rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
}

.sidebar-brand .brand-version {
    font-size: 0.65rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ===== QUALITY GAUGE ===== */
.quality-score {
    text-align: center;
    padding: 1rem;
}

.quality-score .score-value {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
}

.quality-score .score-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ===== INFO/WARNING BOXES ===== */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
}

/* ===== FOOTER ===== */
.sidebar-footer {
    padding: 1rem;
    text-align: center;
    border-top: 1px solid var(--border-color);
    margin-top: 1rem;
}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper components
# ---------------------------------------------------------------------------
def gradient_metric(
    icon: str, value: str | int, label: str, gradient_idx: int = 0, sub: str = "",
) -> str:
    """Render an animated gradient metric card."""
    colors = GRADIENT_COLORS[gradient_idx % len(GRADIENT_COLORS)]
    gradient = f"linear-gradient(135deg, {colors[0]} 0%, {colors[1]} 100%)"
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="gradient-metric animate-in" style="background: {gradient};">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value:,}</div>
        <div class="metric-label">{label}</div>
        {sub_html}
    </div>
    """


def section_header(text: str) -> None:
    """Render a styled section header."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def export_dataframe(df: pd.DataFrame, name: str) -> None:
    """Render CSV and JSON download buttons for a dataframe."""
    col1, col2 = st.columns([1, 1])
    with col1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"📥 Download CSV",
            csv_data,
            f"{name}.csv",
            "text/csv",
            key=f"csv_{name}_{id(df)}",
        )
    with col2:
        json_data = df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button(
            f"📥 Download JSON",
            json_data,
            f"{name}.json",
            "application/json",
            key=f"json_{name}_{id(df)}",
        )


def render_table(df: pd.DataFrame, *, height: int = 420, export_name: str = "") -> None:
    """Render a styled dataframe with optional export."""
    st.dataframe(df, use_container_width=True, height=height, hide_index=True)
    if export_name and not df.empty:
        export_dataframe(df, export_name)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-icon">🎾</div>
            <div class="brand-title">Tennis Analytics</div>
            <div class="brand-version">v2.0 • SportRadar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "📊 Overview",
            "🏆 Competitions",
            "👤 Competitors",
            "🌍 Venues",
            "🔬 SQL Analysis",
            "📈 Advanced Analytics",
            "✅ Data Quality",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    with st.expander("⚙️ Data Controls", expanded=False):
        st.caption("Refresh data from Sportradar API")
        api_key_input = st.text_input("API Key", type="password", label_visibility="collapsed", placeholder="Enter API key...")
        if st.button("🔄 Refresh Database", use_container_width=True):
            try:
                refresh_settings = get_settings(
                    api_key_override=api_key_input or None,
                    require_api_key=True,
                )
                with st.spinner("Fetching latest data..."):
                    result = run_refresh(refresh_settings)
                st.cache_data.clear()
                st.toast("✅ Database refreshed successfully!", icon="🎾")
                st.json(result.table_counts)
            except Exception as exc:
                st.error(str(exc))

    # Database stats
    st.markdown("---")
    try:
        counts = get_table_counts(engine)
        total_rows = sum(counts.values())
        st.caption(f"📊 **{total_rows:,}** total records")
        for table, count in counts.items():
            st.caption(f"  {table}: **{count:,}**")
    except Exception:
        st.caption("Database not ready")

    st.markdown(
        """
        <div class="sidebar-footer">
            <div style="font-size: 0.7rem; color: var(--text-muted);">
                Built with Streamlit + Plotly<br>
                <span style="color: var(--accent-cyan);">SportRadar Tennis API v3</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Guard: ensure database is ready
# ---------------------------------------------------------------------------
try:
    counts = get_table_counts(engine)
except Exception as exc:
    st.error(
        "The database is not ready. Run `python scripts/refresh_data.py` "
        "from the project folder, then reload."
    )
    st.exception(exc)
    st.stop()

if not counts.get("competitions") and not counts.get("competitor_rankings"):
    st.warning(
        "The database is empty. Use the sidebar refresh or run "
        "`python scripts/refresh_data.py`."
    )
    st.stop()

# =========================================================================
# PAGE: OVERVIEW
# =========================================================================
if page == "📊 Overview":
    st.markdown('<div class="page-title">Dashboard Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time tennis analytics powered by SportRadar API</div>', unsafe_allow_html=True)

    # --- Gradient Metric Cards ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(gradient_metric("🏆", counts.get("competitions", 0), "Competitions", 0), unsafe_allow_html=True)
    with c2:
        st.markdown(gradient_metric("🌍", counts.get("venues", 0), "Venues", 1), unsafe_allow_html=True)
    with c3:
        st.markdown(gradient_metric("👤", counts.get("competitors", 0), "Competitors", 2), unsafe_allow_html=True)
    with c4:
        n_countries = metric_value("SELECT COUNT(DISTINCT country) FROM competitors")
        st.markdown(gradient_metric("🌐", int(n_countries), "Countries", 3), unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(gradient_metric("📂", counts.get("categories", 0), "Categories", 4), unsafe_allow_html=True)
    with c6:
        st.markdown(gradient_metric("🏟️", counts.get("complexes", 0), "Complexes", 5), unsafe_allow_html=True)
    with c7:
        max_pts = metric_value("SELECT MAX(points) FROM competitor_rankings")
        st.markdown(gradient_metric("⭐", int(max_pts), "Highest Points", 6), unsafe_allow_html=True)
    with c8:
        stable = metric_value("SELECT COUNT(*) FROM competitor_rankings WHERE movement = 0")
        st.markdown(gradient_metric("📌", int(stable), "Stable Rankings", 7), unsafe_allow_html=True)

    st.markdown("---")

    # --- Charts Row ---
    left, right = st.columns(2)

    with left:
        section_header("Top Categories by Competition Count")
        df = run_query(settings.database_url, """
            SELECT cat.category_name, COUNT(*) AS competition_count
            FROM competitions AS c
            INNER JOIN categories AS cat ON c.category_id = cat.category_id
            GROUP BY cat.category_name
            ORDER BY competition_count DESC
            LIMIT 12;
        """)
        if not df.empty:
            fig = px.bar(
                df, x="competition_count", y="category_name", orientation="h",
                color="competition_count",
                color_continuous_scale=["#0891b2", "#00d4ff", "#7c3aed"],
                text="competition_count",
            )
            fig.update_layout(**plotly_layout(
                showlegend=False, height=420,
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
            ))
            fig.update_traces(textposition="outside", textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No competition data available.")

    with right:
        section_header("Countries by Competitor Count")
        df = run_query(settings.database_url, """
            SELECT cmp.country, COUNT(*) AS competitor_count
            FROM competitor_rankings AS cr
            INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
            GROUP BY cmp.country
            ORDER BY competitor_count DESC, cmp.country
            LIMIT 12;
        """)
        if not df.empty:
            fig = px.bar(
                df, x="competitor_count", y="country", orientation="h",
                color="competitor_count",
                color_continuous_scale=["#059669", "#10b981", "#f59e0b"],
                text="competitor_count",
            )
            fig.update_layout(**plotly_layout(
                showlegend=False, height=420,
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
            ))
            fig.update_traces(textposition="outside", textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No competitor data available.")

    # --- Competition type donut + gender donut ---
    st.markdown("---")
    left2, right2 = st.columns(2)
    with left2:
        section_header("Competition Types")
        df = run_query(settings.database_url, """
            SELECT type, COUNT(*) AS count FROM competitions GROUP BY type ORDER BY count DESC;
        """)
        if not df.empty:
            fig = px.pie(df, values="count", names="type", hole=0.55, color_discrete_sequence=COLOR_PALETTE)
            fig.update_layout(**plotly_layout(height=350, showlegend=True, legend={"orientation": "h", "y": -0.1}))
            fig.update_traces(textinfo="percent+label", textfont_size=12)
            st.plotly_chart(fig, use_container_width=True)

    with right2:
        section_header("Gender Distribution")
        df = run_query(settings.database_url, """
            SELECT gender, COUNT(*) AS count FROM competitions GROUP BY gender ORDER BY count DESC;
        """)
        if not df.empty:
            fig = px.pie(df, values="count", names="gender", hole=0.55, color_discrete_sequence=COLOR_PALETTE[2:])
            fig.update_layout(**plotly_layout(height=350, showlegend=True, legend={"orientation": "h", "y": -0.1}))
            fig.update_traces(textinfo="percent+label", textfont_size=12)
            st.plotly_chart(fig, use_container_width=True)

    # --- API Sync Log ---
    section_header("Latest API Sync")
    sync_df = run_query(settings.database_url, """
        SELECT endpoint, source_generated_at, fetched_at, status_code, row_count
        FROM api_sync_log ORDER BY fetched_at DESC, endpoint;
    """)
    render_table(sync_df, height=150)


# =========================================================================
# PAGE: COMPETITIONS
# =========================================================================
elif page == "🏆 Competitions":
    st.markdown('<div class="page-title">Competition Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Filter, analyze, and explore tennis competitions worldwide</div>', unsafe_allow_html=True)

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        category = st.selectbox("Category", selectable_values(
            "SELECT DISTINCT category_name FROM categories ORDER BY category_name"
        ))
    with f2:
        comp_type = st.selectbox("Type", selectable_values(
            "SELECT DISTINCT type FROM competitions ORDER BY type"
        ))
    with f3:
        gender = st.selectbox("Gender", selectable_values(
            "SELECT DISTINCT gender FROM competitions ORDER BY gender"
        ))
    with f4:
        level = st.selectbox("Level", selectable_values(
            "SELECT DISTINCT COALESCE(level, 'Unspecified') AS level FROM competitions ORDER BY level"
        ))

    params = {
        "category": category, "type": comp_type, "gender": gender,
        "level": level, "limit": 100, "offset": 0,
    }
    comp_df = run_query(settings.database_url, """
        SELECT c.competition_id, c.competition_name, cat.category_name,
               c.type, c.gender, COALESCE(c.level, 'Unspecified') AS level, c.parent_id
        FROM competitions AS c
        INNER JOIN categories AS cat ON c.category_id = cat.category_id
        WHERE (:category = 'All' OR cat.category_name = :category)
          AND (:type = 'All' OR c.type = :type)
          AND (:gender = 'All' OR c.gender = :gender)
          AND (:level = 'All' OR COALESCE(c.level, 'Unspecified') = :level)
        ORDER BY cat.category_name, c.competition_name
        LIMIT :limit OFFSET :offset;
    """, params)

    st.caption(f"Showing **{len(comp_df)}** competitions")
    render_table(comp_df, export_name="competitions")

    st.markdown("---")

    # Distribution charts
    left, right = st.columns(2)
    with left:
        section_header("Type Distribution")
        type_df = run_query(settings.database_url, """
            SELECT type, COUNT(*) AS count FROM competitions GROUP BY type ORDER BY count DESC;
        """)
        if not type_df.empty:
            fig = px.bar(type_df, x="type", y="count", color="type",
                         color_discrete_sequence=COLOR_PALETTE, text="count")
            fig.update_layout(**plotly_layout(height=320, showlegend=False))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        section_header("Category Treemap")
        tree_df = run_query(settings.database_url, """
            SELECT cat.category_name, c.type, COUNT(*) AS count
            FROM competitions AS c
            INNER JOIN categories AS cat ON c.category_id = cat.category_id
            GROUP BY cat.category_name, c.type
            ORDER BY count DESC;
        """)
        if not tree_df.empty:
            fig = px.treemap(tree_df, path=["category_name", "type"], values="count",
                             color="count", color_continuous_scale="Viridis")
            fig.update_layout(**plotly_layout(height=320, coloraxis_showscale=False))
            st.plotly_chart(fig, use_container_width=True)

    # Hierarchy
    section_header("Competition Hierarchy")
    hier_df = run_query(settings.database_url, """
        SELECT parent.competition_name AS parent_competition,
               COUNT(child.competition_id) AS sub_competition_count
        FROM competitions AS parent
        INNER JOIN competitions AS child ON child.parent_id = parent.competition_id
        GROUP BY parent.competition_id, parent.competition_name
        ORDER BY sub_competition_count DESC, parent.competition_name
        LIMIT 20;
    """)
    if not hier_df.empty:
        fig = px.bar(hier_df, x="sub_competition_count", y="parent_competition", orientation="h",
                     color="sub_competition_count", color_continuous_scale=["#7c3aed", "#ec4899"],
                     text="sub_competition_count")
        fig.update_layout(**plotly_layout(
            height=min(400, 50 + len(hier_df) * 30), showlegend=False,
            yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
        ))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)


# =========================================================================
# PAGE: COMPETITORS
# =========================================================================
elif page == "👤 Competitors":
    st.markdown('<div class="page-title">Competitor Rankings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Doubles competitor rankings, search, and analysis</div>', unsafe_allow_html=True)

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        search = st.text_input("🔍 Search competitor", placeholder="Enter name...")
    with f2:
        league = st.selectbox("Ranking", selectable_values(
            "SELECT DISTINCT ranking_name FROM competitor_rankings ORDER BY ranking_name"
        ))
    with f3:
        country = st.selectbox("Country", selectable_values(
            "SELECT DISTINCT country FROM competitors ORDER BY country"
        ))

    f4, f5, f6 = st.columns(3)
    max_rank = int(metric_value("SELECT MAX(rank) FROM competitor_rankings") or 1)
    max_pts = int(metric_value("SELECT MAX(points) FROM competitor_rankings") or 0)
    with f4:
        rank_range = st.slider("Rank range", 1, max_rank, (1, min(100, max_rank)))
    with f5:
        min_points = st.slider("Min points", 0, max_pts, 0, step=50)
    with f6:
        movement = st.selectbox("Movement", ["All", "Stable", "Climbers ↑", "Fallers ↓"])

    movement_filter = {
        "All": "1 = 1",
        "Stable": "cr.movement = 0",
        "Climbers ↑": "cr.movement > 0",
        "Fallers ↓": "cr.movement < 0",
    }[movement]

    comp_sql = f"""
        SELECT cmp.name, cmp.country, cmp.country_code, cr.ranking_name,
               cr.ranking_gender, cr.rank, cr.points, cr.movement, cr.competitions_played
        FROM competitor_rankings AS cr
        INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
        WHERE (:league = 'All' OR cr.ranking_name = :league)
          AND (:country = 'All' OR cmp.country = :country)
          AND (:search = '' OR LOWER(cmp.name) LIKE :search_like)
          AND cr.rank BETWEEN :min_rank AND :max_rank
          AND cr.points >= :min_points
          AND {movement_filter}
        ORDER BY cr.ranking_name, cr.rank, cr.points DESC, cmp.name
        LIMIT 500;
    """
    comp_params = {
        "league": league, "country": country,
        "search": search.strip().lower(), "search_like": f"%{search.strip().lower()}%",
        "min_rank": int(rank_range[0]), "max_rank": int(rank_range[1]),
        "min_points": int(min_points),
    }
    comp_df = run_query(settings.database_url, comp_sql, comp_params)

    st.caption(f"Showing **{len(comp_df)}** competitors")
    render_table(comp_df, export_name="competitors")

    if not comp_df.empty:
        st.markdown("---")

        # Competitor detail card
        section_header("Competitor Spotlight")
        selected = st.selectbox("Select competitor", comp_df["name"].tolist())
        row = comp_df[comp_df["name"] == selected].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏅 Rank", f"#{int(row['rank'])}")
        c2.metric("⭐ Points", f"{int(row['points']):,}")
        c3.metric("📈 Movement", f"{int(row['movement']):+d}")
        c4.metric("🎾 Played", int(row["competitions_played"]))

        st.markdown("---")

        # Charts
        left, right = st.columns(2)
        with left:
            section_header("Rank vs Points Scatter")
            fig = px.scatter(
                comp_df, x="rank", y="points", color="country",
                hover_name="name", size="competitions_played",
                color_discrete_sequence=COLOR_PALETTE,
                size_max=15,
            )
            fig.update_layout(**plotly_layout(height=400, showlegend=False))
            st.plotly_chart(fig, use_container_width=True)

        with right:
            section_header("Top Movers")
            movers = comp_df.nlargest(15, "movement", keep="first") if (comp_df["movement"] > 0).any() else comp_df.head(15)
            fig = px.bar(
                movers, x="movement", y="name", orientation="h",
                color="movement", color_continuous_scale=["#ef4444", "#fbbf24", "#10b981"],
                text="movement",
            )
            fig.update_layout(**plotly_layout(
                height=400, showlegend=False,
                yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
            ))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)


# =========================================================================
# PAGE: VENUES
# =========================================================================
elif page == "🌍 Venues":
    st.markdown('<div class="page-title">Venue & Complex Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Explore tennis venues, complexes, and geographic coverage</div>', unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        v_country = st.selectbox("Country", selectable_values(
            "SELECT DISTINCT country_name FROM venues ORDER BY country_name"
        ))
    with f2:
        v_complex = st.selectbox("Complex", selectable_values(
            "SELECT DISTINCT complex_name FROM complexes ORDER BY complex_name"
        ))

    venues_df = run_query(settings.database_url, """
        SELECT v.venue_id, v.venue_name, v.city_name, v.country_name,
               v.country_code, v.timezone, cx.complex_name
        FROM venues AS v
        INNER JOIN complexes AS cx ON v.complex_id = cx.complex_id
        WHERE (:country = 'All' OR v.country_name = :country)
          AND (:complex_name = 'All' OR cx.complex_name = :complex_name)
        ORDER BY v.country_name, v.city_name, cx.complex_name, v.venue_name
        LIMIT 200;
    """, {"country": v_country, "complex_name": v_complex})

    st.caption(f"Showing **{len(venues_df)}** venues")
    render_table(venues_df, export_name="venues")

    st.markdown("---")

    left, right = st.columns(2)
    with left:
        section_header("Venues by Country")
        country_df = run_query(settings.database_url, """
            SELECT country_name, COUNT(*) AS venue_count
            FROM venues GROUP BY country_name
            ORDER BY venue_count DESC LIMIT 20;
        """)
        if not country_df.empty:
            fig = px.bar(country_df, x="venue_count", y="country_name", orientation="h",
                         color="venue_count", color_continuous_scale=["#06b6d4", "#0891b2", "#00d4ff"],
                         text="venue_count")
            fig.update_layout(**plotly_layout(
                height=450, showlegend=False,
                yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
            ))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        section_header("Timezone Distribution")
        tz_df = run_query(settings.database_url, """
            SELECT timezone, COUNT(*) AS venue_count, COUNT(DISTINCT country_name) AS countries
            FROM venues GROUP BY timezone ORDER BY venue_count DESC LIMIT 15;
        """)
        if not tz_df.empty:
            fig = px.bar(tz_df, x="venue_count", y="timezone", orientation="h",
                         color="countries", color_continuous_scale=["#7c3aed", "#ec4899"],
                         text="venue_count")
            fig.update_layout(**plotly_layout(
                height=450, showlegend=False,
                yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
            ))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # Multi-venue complexes
    section_header("Multi-Venue Complexes")
    multi_df = run_query(settings.database_url, """
        SELECT cx.complex_name, COUNT(v.venue_id) AS venue_count
        FROM complexes AS cx
        INNER JOIN venues AS v ON v.complex_id = cx.complex_id
        GROUP BY cx.complex_id, cx.complex_name
        HAVING COUNT(v.venue_id) > 1
        ORDER BY venue_count DESC, cx.complex_name LIMIT 20;
    """)
    render_table(multi_df, height=280, export_name="multi_venue_complexes")


# =========================================================================
# PAGE: SQL ANALYSIS
# =========================================================================
elif page == "🔬 SQL Analysis":
    st.markdown('<div class="page-title">SQL Analysis Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Execute required SQL queries and explore additional insights</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Required Queries", "💡 Insight Queries"])

    with tab1:
        section_name = st.selectbox("Analysis Section", list(REQUIRED_QUERIES))
        query_titles = [q.title for q in REQUIRED_QUERIES[section_name]]
        query_title = st.selectbox("Query", query_titles)
        query_spec = next(q for q in REQUIRED_QUERIES[section_name] if q.title == query_title)

        params: dict[str, Any] = {}
        if query_spec.params:
            st.markdown("**Query Parameters**")
            cols = st.columns(len(query_spec.params))
            for col, param in zip(cols, query_spec.params):
                default = (query_spec.default_params or {}).get(param, "")
                params[param] = col.text_input(param, value=str(default))

        with st.expander("📝 SQL", expanded=False):
            st.code(query_spec.sql.strip(), language="sql")

        result_df = run_query(settings.database_url, query_spec.sql, params)
        render_table(result_df, height=460, export_name=f"query_{query_title[:30]}")

    with tab2:
        extra_title = st.selectbox("Insight Query", list(EXTRA_INSIGHT_QUERIES))
        extra_spec = EXTRA_INSIGHT_QUERIES[extra_title]
        with st.expander("📝 SQL", expanded=False):
            st.code(extra_spec.sql.strip(), language="sql")
        result_df = run_query(settings.database_url, extra_spec.sql)
        render_table(result_df, height=400, export_name=f"insight_{extra_title[:30]}")


# =========================================================================
# PAGE: ADVANCED ANALYTICS
# =========================================================================
elif page == "📈 Advanced Analytics":
    st.markdown('<div class="page-title">Advanced Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Deep-dive statistical analysis and correlations</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌐 Country Power", "📊 Distribution", "📈 Movement", "🏟️ Coverage"
    ])

    with tab1:
        section_header("Country Power Rankings")
        power_df = run_query(settings.database_url, """
            SELECT cmp.country, COUNT(*) AS competitors,
                   SUM(cr.points) AS total_points,
                   ROUND(AVG(cr.points), 1) AS avg_points,
                   MIN(cr.rank) AS best_rank,
                   ROUND(SUM(cr.points) * 1.0 / NULLIF(MIN(cr.rank), 0), 1) AS power_index
            FROM competitor_rankings AS cr
            INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
            GROUP BY cmp.country
            HAVING COUNT(*) >= 2
            ORDER BY power_index DESC;
        """)
        if not power_df.empty:
            render_table(power_df, height=300, export_name="country_power")

            fig = px.scatter(
                power_df, x="avg_points", y="competitors",
                size="total_points", color="power_index",
                hover_name="country", text="country",
                color_continuous_scale=["#0891b2", "#00d4ff", "#7c3aed", "#f59e0b"],
                size_max=50,
            )
            fig.update_layout(**plotly_layout(
                height=500,
                xaxis_title="Average Points",
                yaxis_title="Number of Competitors",
                coloraxis_colorbar_title="Power Index",
            ))
            fig.update_traces(textposition="top center", textfont_size=10)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        section_header("Points Distribution Analysis")
        dist_df = run_query(settings.database_url, """
            SELECT cr.points, cr.rank, cmp.country, cmp.name, cr.ranking_name
            FROM competitor_rankings AS cr
            INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
            ORDER BY cr.rank;
        """)
        if not dist_df.empty:
            left, right = st.columns(2)
            with left:
                fig = px.histogram(
                    dist_df, x="points", nbins=30, color_discrete_sequence=["#00d4ff"],
                    marginal="box",
                )
                fig.update_layout(**plotly_layout(height=400, xaxis_title="Points", yaxis_title="Count"))
                st.plotly_chart(fig, use_container_width=True)

            with right:
                fig = px.scatter(
                    dist_df, x="rank", y="points", color="ranking_name",
                    hover_name="name", color_discrete_sequence=COLOR_PALETTE,
                    opacity=0.7,
                )
                fig.update_layout(**plotly_layout(height=400, xaxis_title="Rank", yaxis_title="Points"))
                st.plotly_chart(fig, use_container_width=True)

        section_header("Type × Gender Cross-Tab")
        cross_df = run_query(settings.database_url, """
            SELECT type, gender, COUNT(*) AS count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM competitions), 1) AS pct
            FROM competitions GROUP BY type, gender ORDER BY count DESC;
        """)
        if not cross_df.empty:
            fig = px.sunburst(cross_df, path=["type", "gender"], values="count",
                              color="count", color_continuous_scale="Viridis")
            fig.update_layout(**plotly_layout(height=450, coloraxis_showscale=False))
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        section_header("Ranking Movement Analysis")
        move_df = run_query(settings.database_url, """
            SELECT cmp.name, cmp.country, cr.rank, cr.points, cr.movement,
                   cr.competitions_played, cr.ranking_name,
                   CASE WHEN cr.movement > 0 THEN 'Climber'
                        WHEN cr.movement < 0 THEN 'Faller'
                        ELSE 'Stable' END AS category
            FROM competitor_rankings AS cr
            INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
            ORDER BY ABS(cr.movement) DESC LIMIT 100;
        """)
        if not move_df.empty:
            # Movement distribution
            cat_counts = move_df["category"].value_counts().reset_index()
            cat_counts.columns = ["category", "count"]
            cat_colors = {"Climber": "#10b981", "Faller": "#ef4444", "Stable": "#f59e0b"}
            fig = px.pie(
                cat_counts, values="count", names="category",
                color="category", color_discrete_map=cat_colors,
                hole=0.5,
            )
            fig.update_layout(**plotly_layout(height=350))
            fig.update_traces(textinfo="percent+label+value")
            st.plotly_chart(fig, use_container_width=True)

            # Top movers table
            section_header("Biggest Movers")
            render_table(move_df.head(30), height=350, export_name="movement_leaders")

    with tab4:
        section_header("Venue Geographic Coverage")
        geo_df = run_query(settings.database_url, """
            SELECT v.country_name, v.country_code,
                   COUNT(DISTINCT v.venue_id) AS venues,
                   COUNT(DISTINCT v.city_name) AS cities,
                   COUNT(DISTINCT cx.complex_id) AS complexes,
                   COUNT(DISTINCT v.timezone) AS timezones
            FROM venues AS v
            INNER JOIN complexes AS cx ON v.complex_id = cx.complex_id
            GROUP BY v.country_name, v.country_code
            ORDER BY venues DESC;
        """)
        if not geo_df.empty:
            render_table(geo_df, height=300, export_name="geographic_coverage")

            fig = px.choropleth(
                geo_df, locations="country_code",
                color="venues", hover_name="country_name",
                color_continuous_scale=["#0a0a1a", "#0891b2", "#00d4ff", "#7c3aed"],
                projection="natural earth",
            )
            fig.update_layout(**plotly_layout(
                height=450,
                geo={"bgcolor": "rgba(0,0,0,0)", "lakecolor": "rgba(0,0,0,0)",
                     "landcolor": "#1a1a2e", "showframe": False, "coastlinecolor": "#333"},
                coloraxis_colorbar_title="Venues",
            ))
            st.plotly_chart(fig, use_container_width=True)

        section_header("Category Depth")
        depth_df = run_query(settings.database_url, """
            SELECT cat.category_name,
                   COUNT(c.competition_id) AS total,
                   COUNT(CASE WHEN c.parent_id IS NULL THEN 1 END) AS root,
                   COUNT(CASE WHEN c.parent_id IS NOT NULL THEN 1 END) AS sub,
                   COUNT(DISTINCT c.type) AS types,
                   COUNT(DISTINCT c.gender) AS genders
            FROM categories AS cat
            INNER JOIN competitions AS c ON c.category_id = cat.category_id
            GROUP BY cat.category_name
            ORDER BY total DESC;
        """)
        if not depth_df.empty:
            fig = px.bar(depth_df, x="category_name", y=["root", "sub"],
                         color_discrete_sequence=["#00d4ff", "#7c3aed"],
                         barmode="stack", text_auto=True)
            fig.update_layout(**plotly_layout(
                height=400, xaxis_tickangle=-45,
                xaxis_title="", yaxis_title="Competitions",
                legend_title="Type",
            ))
            st.plotly_chart(fig, use_container_width=True)


# =========================================================================
# PAGE: DATA QUALITY
# =========================================================================
elif page == "✅ Data Quality":
    st.markdown('<div class="page-title">Data Quality Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Monitor data integrity, freshness, and completeness</div>', unsafe_allow_html=True)

    # Try to run quality checks
    try:
        from tennis_analytics.quality import run_quality_checks as run_checks, PASS, WARN, FAIL

        report = run_checks(engine, freshness_warning_days=getattr(settings, "quality_warning_days", 7))

        # Score display
        c1, c2, c3, c4 = st.columns(4)
        score_color = "#10b981" if report.score >= 80 else ("#f59e0b" if report.score >= 50 else "#ef4444")
        with c1:
            st.markdown(f"""
                <div class="glass-card quality-score">
                    <div class="score-value" style="color: {score_color};">{report.score}</div>
                    <div class="score-label">Quality Score</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.metric("✅ Passed", report.passed)
        with c3:
            st.metric("⚠️ Warnings", report.warnings)
        with c4:
            st.metric("❌ Failed", report.failed)

        st.markdown("---")

        # Detailed checks table
        section_header("Quality Check Results")
        check_data = []
        for check in report.checks:
            status_icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(check.status, "❓")
            check_data.append({
                "Status": f"{status_icon} {check.status.upper()}",
                "Check": check.name,
                "Observed": str(check.observed),
                "Expected": check.expected,
                "Details": check.details,
            })
        checks_df = pd.DataFrame(check_data)
        render_table(checks_df, height=500, export_name="quality_report")

        # Visual breakdown
        st.markdown("---")
        left, right = st.columns(2)
        with left:
            section_header("Check Status Breakdown")
            status_counts = pd.DataFrame([
                {"Status": "Passed", "Count": report.passed, "Color": "#10b981"},
                {"Status": "Warnings", "Count": report.warnings, "Color": "#f59e0b"},
                {"Status": "Failed", "Count": report.failed, "Color": "#ef4444"},
            ])
            fig = px.pie(
                status_counts, values="Count", names="Status",
                color="Status",
                color_discrete_map={"Passed": "#10b981", "Warnings": "#f59e0b", "Failed": "#ef4444"},
                hole=0.6,
            )
            fig.update_layout(**plotly_layout(height=350))
            fig.update_traces(textinfo="percent+value")
            st.plotly_chart(fig, use_container_width=True)

        with right:
            section_header("Table Row Counts")
            row_data = [{"Table": t, "Rows": c} for t, c in counts.items()]
            row_df = pd.DataFrame(row_data)
            fig = px.bar(row_df, x="Rows", y="Table", orientation="h",
                         color="Rows", color_continuous_scale=["#0891b2", "#00d4ff"],
                         text="Rows")
            fig.update_layout(**plotly_layout(
                height=350, showlegend=False,
                yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
            ))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as exc:
        st.error(f"Quality checks could not be run: {exc}")
        st.info("Run `python scripts/run_quality_checks.py` from the command line to generate a report.")
