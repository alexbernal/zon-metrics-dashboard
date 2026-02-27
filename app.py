"""
ZON Radiance - GPU Server Metrics Dashboard
Displays real-time metrics from bizon1 (8× NVIDIA H100 GPUs)

Style: The Construct (Matrix green theme)
Data source: Supabase (sandbox_server_metrics table)
"""

import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import time

# =============================================================================
# Configuration - These use Supabase ANON key (safe to be public with RLS)
# =============================================================================
SUPABASE_URL = "https://npncfuqniawyzfrnivou.supabase.co"
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", "YOUR_ANON_KEY_HERE")

# H100 specs for gauge ranges
H100_TDP_WATTS = 700  # Per GPU
GPU_COUNT = 8
MAX_POWER_WATTS = H100_TDP_WATTS * GPU_COUNT  # 5600W theoretical max

# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title="ZON Radiance - GPU Metrics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# The Construct — Style Sheet (Matrix Green Theme)
# Ported from construct.css
# =============================================================================
CONSTRUCT_CSS = """
<style>
    /* ═══════════════════════════════════════════════════════════════
       The Construct — Streamlit Theme
       Matrix Chris · Oracle Nexus Window System
       ═══════════════════════════════════════════════════════════════ */

    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&display=swap');

    :root {
        --nexus-primary:   #00ff41;
        --nexus-secondary: #003b00;
        --nexus-bg:        #0a0f0a;
        --nexus-grid:      rgba(0, 255, 65, 0.03);
        --nexus-glow:      rgba(0, 255, 65, 0.3);
        --nexus-border:    rgba(0, 255, 65, 0.12);
        
        --color-ok:        #2ecc71;
        --color-warn:      #f1c40f;
        --color-error:     #ff5555;
        --color-info:      #8be9fd;
        --color-muted:     #555;
        --color-text:      #c0c0c0;
        --color-text-dim:  #888;
        --color-highlight: #f1fa8c;
        --color-purple:    #bd93f9;
        --color-cyan:      #8be9fd;
        
        --font-mono: 'Fira Code', 'SF Mono', Monaco, 'Cascadia Code', monospace;
        --font-system: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    }

    /* Main app background */
    .stApp {
        background: var(--nexus-bg) !important;
    }
    
    /* Grid overlay effect */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            linear-gradient(var(--nexus-grid) 1px, transparent 1px),
            linear-gradient(90deg, var(--nexus-grid) 1px, transparent 1px);
        background-size: 50px 50px;
        z-index: 0;
        pointer-events: none;
    }

    /* All text elements */
    .stApp, .stMarkdown, p, span, label, .stMetric, div {
        font-family: var(--font-mono) !important;
        color: var(--color-text) !important;
    }

    /* Main container */
    .main .block-container {
        padding-top: 2rem !important;
        max-width: 100% !important;
    }

    /* Headers - Nexus Primary with glow */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--nexus-primary) !important;
        font-family: var(--font-mono) !important;
        text-shadow: 0 0 10px var(--nexus-glow);
        font-weight: 700 !important;
    }

    h1 {
        font-size: 1.8em !important;
        margin-bottom: 4px !important;
    }

    h2, h3 {
        font-size: 1.1em !important;
        border-bottom: 1px solid #222;
        padding-bottom: 6px;
        margin-top: 1rem !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: rgba(0, 255, 65, 0.03) !important;
        border: 1px solid var(--nexus-border) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        transition: all 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        background: rgba(0, 255, 65, 0.06) !important;
        border-color: var(--nexus-primary) !important;
        box-shadow: 0 0 15px var(--nexus-glow);
    }

    [data-testid="stMetricLabel"] {
        color: var(--color-muted) !important;
        font-size: 0.72em !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--nexus-primary) !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        text-shadow: 0 0 8px var(--nexus-glow);
    }

    [data-testid="stMetricDelta"] {
        color: var(--color-text-dim) !important;
        font-size: 0.7em !important;
    }

    [data-testid="stMetricDelta"] svg {
        display: none;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 8px;
        border-bottom: 1px solid var(--nexus-border);
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(0, 255, 65, 0.05) !important;
        border: 1px solid var(--nexus-border) !important;
        border-radius: 6px 6px 0 0 !important;
        color: var(--color-text) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.8em !important;
        padding: 8px 16px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(0, 255, 65, 0.15) !important;
        border-color: var(--nexus-primary) !important;
        color: var(--nexus-primary) !important;
        box-shadow: 0 0 10px var(--nexus-glow);
    }

    /* Charts */
    [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid var(--nexus-border) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--nexus-secondary), var(--nexus-primary)) !important;
        box-shadow: 0 0 10px var(--nexus-glow);
    }

    .stProgress > div {
        background: rgba(0, 255, 65, 0.1) !important;
        border-radius: 4px;
    }

    /* Buttons */
    .stButton > button {
        background: rgba(0, 255, 65, 0.1) !important;
        border: 1px solid var(--nexus-border) !important;
        color: var(--nexus-primary) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.8em !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: rgba(0, 255, 65, 0.2) !important;
        border-color: var(--nexus-primary) !important;
        box-shadow: 0 0 15px var(--nexus-glow) !important;
        transform: translateY(-1px);
    }

    /* Divider */
    hr {
        border-color: var(--nexus-border) !important;
        margin: 20px 0 !important;
    }

    /* Caption text */
    .stCaption, small, figcaption {
        color: var(--color-muted) !important;
        font-size: 0.7em !important;
    }

    /* Warning boxes */
    .stAlert [data-testid="stNotificationContentWarning"] {
        background: rgba(241, 196, 15, 0.08) !important;
        border: 1px solid rgba(241, 196, 15, 0.3) !important;
    }

    /* Error boxes */
    .stAlert [data-testid="stNotificationContentError"] {
        background: rgba(255, 85, 85, 0.08) !important;
        border: 1px solid rgba(255, 85, 85, 0.3) !important;
    }

    /* Info boxes */
    .stAlert [data-testid="stNotificationContentInfo"] {
        background: rgba(139, 233, 253, 0.08) !important;
        border: 1px solid rgba(139, 233, 253, 0.3) !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: var(--nexus-border);
        border-radius: 2px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--nexus-primary);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Connection status indicator */
    .connection-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--color-ok);
        margin-right: 6px;
        animation: pulse 2s ease-in-out infinite;
    }

    .hud-status {
        display: flex;
        align-items: center;
        gap: 7px;
        font-size: 0.72em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--nexus-primary);
        margin-bottom: 10px;
    }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.4); }
        50% { box-shadow: 0 0 0 4px rgba(46, 204, 113, 0); }
    }

    /* Status colors */
    .status-ok { color: var(--color-ok) !important; }
    .status-warn { color: var(--color-warn) !important; }
    .status-error { color: var(--color-error) !important; }
    .text-primary { color: var(--nexus-primary) !important; }
    .text-muted { color: var(--color-muted) !important; }
    .text-cyan { color: var(--color-cyan) !important; }
    .text-purple { color: var(--color-purple) !important; }
</style>
"""

st.markdown(CONSTRUCT_CSS, unsafe_allow_html=True)

# =============================================================================
# Data Fetching
# =============================================================================
@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client (cached)"""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@st.cache_data(ttl=30)
def fetch_metrics(limit: int = 500):
    """Fetch latest metrics from Supabase"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("sandbox_server_metrics") \
            .select("*") \
            .order("ts", desc=True) \
            .limit(limit) \
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['ts'] = pd.to_datetime(df['ts'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_record_count():
    """Get total record count"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("sandbox_server_metrics") \
            .select("id", count="exact") \
            .execute()
        return response.count or 0
    except:
        return 0

# =============================================================================
# Helper Functions
# =============================================================================
def format_uptime(seconds: float) -> str:
    """Convert seconds to human-readable uptime"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    return f"{days}d {hours}h"

def format_bytes(bytes_val: float) -> str:
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"

def calculate_daily_cost(power_watts: float, rate_per_kwh: float = 0.12) -> float:
    """Calculate estimated daily electricity cost"""
    daily_kwh = (power_watts / 1000) * 24
    return daily_kwh * rate_per_kwh

# =============================================================================
# Dashboard Layout
# =============================================================================
def main():
    # HUD Header with connection indicator
    st.markdown("""
        <div class="hud-status">
            <span class="connection-dot"></span>
            <span>LIVE TELEMETRY</span>
            <span style="color: #555; margin-left: 10px;">bizon1</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.title("⚡ ZON RADIANCE")
    st.caption("8× NVIDIA H100 80GB · Real-time GPU Cluster Monitoring")
    
    # Fetch data
    df = fetch_metrics(500)
    
    if df.empty:
        st.warning("⚠ NO DATA STREAM")
        st.info("Check SUPABASE_ANON_KEY in Streamlit secrets and verify RLS policy is enabled.")
        return
    
    # Get latest record
    latest = df.iloc[0]
    
    # =========================================================================
    # Row 1: Real-Time Overview (Key Metrics)
    # =========================================================================
    st.markdown("### 📊 SYSTEM STATUS")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        power_pct = (latest['gpu_power_total'] / MAX_POWER_WATTS) * 100
        st.metric(
            label="⚡ GPU POWER",
            value=f"{latest['gpu_power_total']:.0f}W",
            delta=f"{power_pct:.1f}% capacity"
        )
    
    with col2:
        st.metric(
            label="🖥 CPU",
            value=f"{latest['cpu_percent']:.1f}%",
            delta=f"Load {latest['load1']:.1f}"
        )
    
    with col3:
        st.metric(
            label="🧠 MEMORY",
            value=f"{latest['mem_percent']:.1f}%",
            delta=format_bytes(latest['mem_used_bytes'])
        )
    
    with col4:
        temp_status = "🔥" if latest['gpu_temp_avg'] > 80 else "🌡"
        st.metric(
            label=f"{temp_status} GPU TEMP",
            value=f"{latest['gpu_temp_avg']:.1f}°C",
            delta=f"Util {latest['gpu_util_avg']:.0f}%"
        )
    
    # =========================================================================
    # Row 2: Stats Cards
    # =========================================================================
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="⏱ UPTIME",
            value=format_uptime(latest['uptime_sec'])
        )
    
    with col2:
        total_records = get_record_count()
        st.metric(
            label="📈 RECORDS",
            value=f"{total_records:,}"
        )
    
    with col3:
        daily_cost = calculate_daily_cost(latest['gpu_power_total'])
        st.metric(
            label="💰 DAILY COST",
            value=f"${daily_cost:.2f}",
            delta=f"{(latest['gpu_power_total']/1000)*24:.1f} kWh"
        )
    
    with col4:
        st.metric(
            label="💾 DISK",
            value=f"{latest['disk_root_percent']:.1f}%"
        )
    
    # =========================================================================
    # Row 3: Time Series Charts
    # =========================================================================
    st.divider()
    st.markdown("### 📈 TELEMETRY")
    
    # Prepare data for charts
    chart_df = df.sort_values('ts').tail(200)
    
    tab1, tab2, tab3 = st.tabs(["⚡ POWER", "🌡 THERMAL", "📊 RESOURCES"])
    
    with tab1:
        st.line_chart(
            chart_df.set_index('ts')['gpu_power_total'],
            use_container_width=True,
            color="#00ff41"
        )
        st.caption("Total GPU Power Draw (Watts) · Max Capacity: 5600W")
    
    with tab2:
        temp_color = "#ff5555" if latest['gpu_temp_avg'] > 75 else "#00ff41"
        st.line_chart(
            chart_df.set_index('ts')['gpu_temp_avg'],
            use_container_width=True,
            color=temp_color
        )
        if latest['gpu_temp_avg'] > 80:
            st.markdown('<p class="status-error">⚠ THERMAL WARNING: Temperature exceeds 80°C threshold</p>', unsafe_allow_html=True)
        st.caption("Average GPU Temperature (°C) · Throttle Threshold: 80°C")
    
    with tab3:
        resource_df = chart_df.set_index('ts')[['cpu_percent', 'mem_percent', 'gpu_util_avg']]
        resource_df.columns = ['CPU %', 'Memory %', 'GPU Util %']
        st.line_chart(resource_df, use_container_width=True)
        st.caption("System Resource Utilization Overview")
    
    # =========================================================================
    # Row 4: System Health
    # =========================================================================
    st.divider()
    st.markdown("### 🏥 DIAGNOSTICS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**LOAD AVERAGE**")
        load_df = chart_df.set_index('ts')[['load1', 'load5', 'load15']]
        load_df.columns = ['1 min', '5 min', '15 min']
        st.line_chart(load_df, use_container_width=True)
    
    with col2:
        st.markdown("**MEMORY ALLOCATION**")
        mem_used_gb = latest['mem_used_bytes'] / (1024**3)
        mem_total_gb = latest['mem_total_bytes'] / (1024**3)
        mem_available_gb = latest['mem_available_bytes'] / (1024**3)
        
        st.progress(latest['mem_percent'] / 100)
        st.caption(f"Used: {mem_used_gb:.0f} GB / {mem_total_gb:.0f} GB · Available: {mem_available_gb:.0f} GB")
    
    # =========================================================================
    # Footer
    # =========================================================================
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ts_str = latest['ts'].strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(latest['ts'], 'strftime') else str(latest['ts'])
        st.caption(f"📡 Last reading: {ts_str}")
    with col2:
        st.caption(f"🖥 Host: {latest['host']}")
    with col3:
        if st.button("🔄 REFRESH"):
            st.cache_data.clear()
            st.rerun()

if __name__ == "__main__":
    main()
