"""
ZON Radiance - GPU Server Metrics Dashboard
Displays real-time metrics from bizon1 (8× NVIDIA H100 GPUs)

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

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
    }
    .stMetric {
        background-color: #0e1117;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #262730;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Data Fetching
# =============================================================================
@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client (cached)"""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@st.cache_data(ttl=30)  # Cache for 30 seconds
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
    # Header
    st.title("⚡ ZON Radiance - GPU Server Metrics")
    st.caption("bizon1 | 8× NVIDIA H100 80GB | Real-time monitoring")
    
    # Fetch data
    df = fetch_metrics(500)
    
    if df.empty:
        st.warning("No data available. Check Supabase connection.")
        st.info("Make sure SUPABASE_ANON_KEY is set in Streamlit secrets.")
        return
    
    # Get latest record
    latest = df.iloc[0]
    
    # =========================================================================
    # Row 1: Real-Time Overview (Key Metrics)
    # =========================================================================
    st.subheader("📊 Real-Time Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        power_pct = (latest['gpu_power_total'] / MAX_POWER_WATTS) * 100
        st.metric(
            label="⚡ Total GPU Power",
            value=f"{latest['gpu_power_total']:.0f}W",
            delta=f"{power_pct:.1f}% of max",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="🖥️ CPU Usage",
            value=f"{latest['cpu_percent']:.1f}%",
            delta=f"Load: {latest['load1']:.1f}"
        )
    
    with col3:
        st.metric(
            label="🧠 Memory Usage",
            value=f"{latest['mem_percent']:.1f}%",
            delta=f"{format_bytes(latest['mem_used_bytes'])} used"
        )
    
    with col4:
        st.metric(
            label="🎮 GPU Utilization",
            value=f"{latest['gpu_util_avg']:.1f}%",
            delta=f"Temp: {latest['gpu_temp_avg']:.1f}°C"
        )
    
    # =========================================================================
    # Row 2: Stats Cards
    # =========================================================================
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="⏱️ Server Uptime",
            value=format_uptime(latest['uptime_sec'])
        )
    
    with col2:
        total_records = get_record_count()
        st.metric(
            label="📈 Total Records",
            value=f"{total_records:,}"
        )
    
    with col3:
        daily_cost = calculate_daily_cost(latest['gpu_power_total'])
        st.metric(
            label="💰 Est. Daily Cost",
            value=f"${daily_cost:.2f}",
            delta=f"{(latest['gpu_power_total']/1000)*24:.1f} kWh/day"
        )
    
    with col4:
        st.metric(
            label="💾 Disk Usage",
            value=f"{latest['disk_root_percent']:.1f}%"
        )
    
    # =========================================================================
    # Row 3: Time Series Charts
    # =========================================================================
    st.divider()
    st.subheader("📈 Trends")
    
    # Prepare data for charts (reverse to chronological order)
    chart_df = df.sort_values('ts').tail(200)  # Last 200 records
    
    tab1, tab2, tab3 = st.tabs(["⚡ Power", "🌡️ Temperature", "📊 Resources"])
    
    with tab1:
        st.line_chart(
            chart_df.set_index('ts')['gpu_power_total'],
            use_container_width=True
        )
        st.caption("Total GPU Power Draw (Watts)")
    
    with tab2:
        st.line_chart(
            chart_df.set_index('ts')['gpu_temp_avg'],
            use_container_width=True
        )
        # Temperature warning
        if latest['gpu_temp_avg'] > 80:
            st.warning("⚠️ GPU temperature above 80°C!")
        st.caption("Average GPU Temperature (°C) — Danger zone: >80°C")
    
    with tab3:
        resource_df = chart_df.set_index('ts')[['cpu_percent', 'mem_percent', 'gpu_util_avg']]
        resource_df.columns = ['CPU %', 'Memory %', 'GPU Util %']
        st.line_chart(resource_df, use_container_width=True)
        st.caption("CPU, Memory, and GPU Utilization")
    
    # =========================================================================
    # Row 4: System Health
    # =========================================================================
    st.divider()
    st.subheader("🏥 System Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Load Average**")
        load_df = chart_df.set_index('ts')[['load1', 'load5', 'load15']]
        load_df.columns = ['1 min', '5 min', '15 min']
        st.line_chart(load_df, use_container_width=True)
    
    with col2:
        st.write("**Memory Breakdown**")
        mem_used_gb = latest['mem_used_bytes'] / (1024**3)
        mem_available_gb = latest['mem_available_bytes'] / (1024**3)
        mem_total_gb = latest['mem_total_bytes'] / (1024**3)
        
        st.progress(latest['mem_percent'] / 100)
        st.caption(f"Used: {mem_used_gb:.0f} GB / {mem_total_gb:.0f} GB ({mem_available_gb:.0f} GB available)")
    
    # =========================================================================
    # Footer
    # =========================================================================
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Last updated: {latest['ts']}")
    with col2:
        st.caption(f"Host: {latest['host']}")
    with col3:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # Auto-refresh every 30 seconds
    time.sleep(0.1)  # Small delay to prevent immediate rerun

if __name__ == "__main__":
    main()
