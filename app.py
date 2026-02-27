"""
ZON-Radiance GPU Metrics Dashboard
Construct CSS Theme (Matrix Green)
3-Tab Layout: Data Center | Servers | Wiki
"""

import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import time

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

SUPABASE_URL = "https://npncfuqniawyzfrnivou.supabase.co"
TABLE_NAME = "sandbox_server_metrics"
REFRESH_INTERVAL = 30
ELECTRICITY_RATE = 0.12  # $/kWh

# ═══════════════════════════════════════════════════════════════
# Construct CSS Theme (Matrix Green)
# ═══════════════════════════════════════════════════════════════

CONSTRUCT_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
    
    :root {
        --nexus-primary: #00ff41;
        --nexus-secondary: #003b00;
        --nexus-bg: #0a0f0a;
        --nexus-glow: rgba(0, 255, 65, 0.3);
        --nexus-border: rgba(0, 255, 65, 0.12);
        --color-ok: #2ecc71;
        --color-warn: #f1c40f;
        --color-error: #ff5555;
        --color-info: #8be9fd;
        --color-muted: #555;
        --color-text: #c0c0c0;
        --color-cyan: #8be9fd;
        --color-purple: #bd93f9;
        --color-orange: #f97316;
        --color-pink: #ff79c6;
        --color-yellow: #f1fa8c;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: var(--nexus-bg);
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            linear-gradient(rgba(0, 255, 65, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 65, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        z-index: 0;
        pointer-events: none;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #050805 !important;
        border-right: 1px solid var(--nexus-border) !important;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: var(--nexus-primary) !important;
        font-size: 0.9em;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .sidebar-title {
        color: var(--nexus-primary);
        font-size: 1.5em;
        font-weight: 700;
        text-align: center;
        padding: 20px 0;
        border-bottom: 1px solid var(--nexus-border);
        margin-bottom: 20px;
        text-shadow: 0 0 10px var(--nexus-glow);
    }
    
    .dashboard-title {
        color: var(--nexus-primary);
        font-size: 2em;
        font-weight: 700;
        margin-bottom: 4px;
        text-shadow: 0 0 10px var(--nexus-glow);
    }
    
    .dashboard-subtitle {
        color: var(--color-muted);
        font-size: 0.85em;
        margin-bottom: 20px;
    }
    
    .section-heading {
        color: var(--nexus-primary);
        font-size: 1.1em;
        margin: 20px 0 10px 0;
        border-bottom: 1px solid #222;
        padding-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    .metric-card {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid var(--nexus-border);
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        height: 100%;
    }
    
    .metric-card-large {
        background: rgba(0, 255, 65, 0.05);
        border: 1px solid var(--nexus-border);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-label {
        color: var(--color-muted);
        font-size: 0.7em;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    
    .metric-value {
        color: var(--nexus-primary);
        font-size: 1.6em;
        font-weight: 700;
    }
    
    .metric-value-xl {
        color: var(--nexus-primary);
        font-size: 2.5em;
        font-weight: 700;
    }
    
    .metric-value-sm {
        color: var(--nexus-primary);
        font-size: 1.2em;
        font-weight: 700;
    }
    
    .metric-delta {
        font-size: 0.75em;
        margin-top: 5px;
    }
    
    .metric-sub {
        font-size: 0.7em;
        color: var(--color-muted);
        margin-top: 3px;
    }
    
    .delta-up { color: var(--color-warn); }
    .delta-down { color: var(--color-ok); }
    .delta-flat { color: var(--color-muted); }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-healthy { background: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-warning { background: rgba(241, 196, 15, 0.2); color: #f1c40f; border: 1px solid #f1c40f; }
    .status-critical { background: rgba(255, 85, 85, 0.2); color: #ff5555; border: 1px solid #ff5555; }
    
    .status-idle { background: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-light { background: rgba(139, 233, 253, 0.2); color: #8be9fd; border: 1px solid #8be9fd; }
    .status-moderate { background: rgba(241, 196, 15, 0.2); color: #f1c40f; border: 1px solid #f1c40f; }
    .status-heavy { background: rgba(249, 115, 22, 0.2); color: #f97316; border: 1px solid #f97316; }
    .status-thermal { background: rgba(255, 85, 85, 0.2); color: #ff5555; border: 1px solid #ff5555; }
    
    .thermal-optimal { color: #22c55e; }
    .thermal-normal { color: #eab308; }
    .thermal-high { color: #f97316; }
    .thermal-critical { color: #ef4444; }
    
    .text-cyan { color: var(--color-cyan); }
    .text-purple { color: var(--color-purple); }
    .text-orange { color: var(--color-orange); }
    .text-pink { color: var(--color-pink); }
    .text-yellow { color: var(--color-yellow); }
    .text-ok { color: var(--color-ok); }
    .text-warn { color: var(--color-warn); }
    .text-error { color: var(--color-error); }
    
    .server-card {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--nexus-border);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .server-card.online {
        border-left: 3px solid #2ecc71;
    }
    
    .wiki-section {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--nexus-border);
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .wiki-section h3 {
        color: var(--nexus-primary);
        margin-bottom: 15px;
        border-bottom: 1px solid #222;
        padding-bottom: 8px;
    }
    
    .wiki-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85em;
    }
    
    .wiki-table th {
        background: rgba(0, 255, 65, 0.1);
        color: var(--nexus-primary);
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid var(--nexus-border);
    }
    
    .wiki-table td {
        padding: 10px;
        border-bottom: 1px solid #1a1a1a;
        color: var(--color-text);
    }
    
    .wiki-table tr:hover {
        background: rgba(0, 255, 65, 0.05);
    }
    
    .glossary-term {
        color: var(--color-cyan);
        font-weight: 600;
    }
    
    .code-block {
        background: #0d0d0d;
        border: 1px solid #222;
        border-radius: 4px;
        padding: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85em;
        color: var(--color-text);
        overflow-x: auto;
    }
    
    [data-testid="stMetricValue"] {
        color: var(--nexus-primary) !important;
    }
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase_client():
    api_key = st.secrets.get("SUPABASE_ANON_KEY", "")
    if not api_key:
        st.error("SUPABASE_ANON_KEY not found in secrets")
        st.stop()
    return create_client(SUPABASE_URL, api_key)


def fetch_all_metrics(limit: int = 500) -> pd.DataFrame:
    client = get_supabase_client()
    response = client.table(TABLE_NAME).select("*").order("ts", desc=True).limit(limit).execute()
    if not response.data:
        return pd.DataFrame()
    df = pd.DataFrame(response.data)
    df['ts'] = pd.to_datetime(df['ts'])
    return df


def fetch_server_metrics(host: str, limit: int = 200) -> pd.DataFrame:
    client = get_supabase_client()
    response = client.table(TABLE_NAME).select("*").eq("host", host).order("ts", desc=True).limit(limit).execute()
    if not response.data:
        return pd.DataFrame()
    df = pd.DataFrame(response.data)
    df['ts'] = pd.to_datetime(df['ts'])
    return df


def get_server_list(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    return sorted(df['host'].unique().tolist())


def format_uptime(seconds: float) -> str:
    if not seconds:
        return "N/A"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h"


def format_bytes(bytes_val: float, precision: int = 1) -> str:
    if bytes_val is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.{precision}f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.{precision}f} PB"


def safe_get(d: dict, key: str, default=0):
    val = d.get(key, default)
    return default if val is None else val


def get_delta_indicator(current: float, previous: float, unit: str = "", inverse: bool = False) -> str:
    if previous is None or pd.isna(previous) or current is None or pd.isna(current):
        return '<span class="delta-flat">━ N/A</span>'
    diff = current - previous
    if abs(diff) < 0.01:
        return f'<span class="delta-flat">━ 0.0{unit}</span>'
    if diff > 0:
        css_class = "delta-down" if inverse else "delta-up"
        arrow = "▲"
    else:
        css_class = "delta-up" if inverse else "delta-down"
        arrow = "▼"
    return f'<span class="{css_class}">{arrow} {abs(diff):.1f}{unit}</span>'


def classify_system_state(metrics: dict) -> tuple[str, str]:
    gpu_util = metrics.get('gpu_util_avg', 0) or 0
    cpu_percent = metrics.get('cpu_percent', 0) or 0
    gpu_temp = metrics.get('gpu_temp_avg', 0) or 0
    if gpu_temp > 83:
        return 'THERMAL LIMITED', 'status-thermal'
    if gpu_util > 80:
        return 'HEAVY LOAD', 'status-heavy'
    if gpu_util > 30:
        return 'MODERATE LOAD', 'status-moderate'
    if gpu_util > 5 or cpu_percent > 20:
        return 'LIGHT LOAD', 'status-light'
    return 'IDLE', 'status-idle'


def get_fleet_health(df: pd.DataFrame) -> tuple[str, str]:
    if df.empty:
        return 'UNKNOWN', 'status-warning'
    latest_per_server = df.groupby('host').first()
    avg_temp = latest_per_server['gpu_temp_avg'].mean()
    max_temp = latest_per_server['gpu_temp_avg'].max()
    if max_temp > 85:
        return 'CRITICAL', 'status-critical'
    if max_temp > 75 or avg_temp > 70:
        return 'WARNING', 'status-warning'
    return 'HEALTHY', 'status-healthy'


def calculate_dynamic_range(data: list, padding_percent: float = 0.1, min_range: float = 10) -> tuple[float, float]:
    if not data:
        return 0, 100
    data_clean = [x for x in data if x is not None and not pd.isna(x)]
    if not data_clean:
        return 0, 100
    min_val, max_val = min(data_clean), max(data_clean)
    data_range = max_val - min_val
    if data_range < min_range:
        mean_val = (min_val + max_val) / 2
        return mean_val - min_range / 2, mean_val + min_range / 2
    padding = data_range * padding_percent
    return min_val - padding, max_val + padding


# ═══════════════════════════════════════════════════════════════
# Chart Functions
# ═══════════════════════════════════════════════════════════════

def create_power_chart(df: pd.DataFrame):
    import plotly.graph_objects as go
    df_chart = df.sort_values('ts')
    y_min, y_max = calculate_dynamic_range(df_chart['gpu_power_total'].tolist(), min_range=20)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_chart['ts'], y=df_chart['gpu_power_total'], mode='lines', name='GPU Power', line=dict(color='#00ff41', width=2), fill='tozeroy', fillcolor='rgba(0, 255, 65, 0.1)'))
    if len(df_chart) >= 5:
        fig.add_trace(go.Scatter(x=df_chart['ts'], y=df_chart['gpu_power_total'].rolling(5).mean(), mode='lines', name='5-Pt Avg', line=dict(color='#8be9fd', width=1, dash='dash')))
    
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)', margin=dict(l=50, r=20, t=30, b=50), height=280, yaxis=dict(range=[y_min, y_max], title='W', gridcolor='rgba(0, 255, 65, 0.1)'), xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)'), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def create_thermal_chart(df: pd.DataFrame):
    import plotly.graph_objects as go
    df_chart = df.sort_values('ts')
    y_min, y_max = calculate_dynamic_range(df_chart['gpu_temp_avg'].tolist(), min_range=10)
    y_min, y_max = max(30, y_min), min(95, y_max)
    
    fig = go.Figure()
    if y_max > 60:
        fig.add_hrect(y0=60, y1=min(75, y_max), fillcolor="rgba(234, 179, 8, 0.1)", line_width=0)
    if y_max > 75:
        fig.add_hrect(y0=75, y1=min(85, y_max), fillcolor="rgba(249, 115, 22, 0.1)", line_width=0)
    fig.add_trace(go.Scatter(x=df_chart['ts'], y=df_chart['gpu_temp_avg'], mode='lines', name='Temp', line=dict(color='#f97316', width=2), fill='tozeroy', fillcolor='rgba(249, 115, 22, 0.1)'))
    fig.add_trace(go.Scatter(x=df_chart['ts'], y=85 - df_chart['gpu_temp_avg'], mode='lines', name='Headroom', line=dict(color='#22c55e', width=1, dash='dot'), yaxis='y2'))
    
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)', margin=dict(l=50, r=50, t=30, b=50), height=280, yaxis=dict(range=[y_min, y_max], title='°C', gridcolor='rgba(0, 255, 65, 0.1)'), yaxis2=dict(title='Headroom', overlaying='y', side='right', range=[0, 55]), xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)'), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def create_utilization_chart(df: pd.DataFrame):
    import plotly.graph_objects as go
    df_chart = df.sort_values('ts')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_chart['ts'], y=df_chart['cpu_percent'], mode='lines', name='CPU', line=dict(color='#8be9fd', width=2)))
    fig.add_trace(go.Scatter(x=df_chart['ts'], y=df_chart['gpu_util_avg'], mode='lines', name='GPU', line=dict(color='#bd93f9', width=2)))
    fig.add_trace(go.Scatter(x=df_chart['ts'], y=df_chart['mem_percent'], mode='lines', name='Mem', line=dict(color='#f1fa8c', width=2)))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)', margin=dict(l=50, r=20, t=30, b=50), height=280, yaxis=dict(range=[0, 100], title='%', gridcolor='rgba(0, 255, 65, 0.1)'), xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)'), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def create_fleet_power_chart(df: pd.DataFrame):
    import plotly.graph_objects as go
    df_agg = df.groupby(df['ts'].dt.floor('30s')).agg({'gpu_power_total': 'sum', 'host': 'nunique'}).reset_index().sort_values('ts')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_agg['ts'], y=df_agg['gpu_power_total'], mode='lines', name='Fleet Power', line=dict(color='#00ff41', width=2), fill='tozeroy', fillcolor='rgba(0, 255, 65, 0.1)'))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)', margin=dict(l=50, r=20, t=30, b=50), height=300, yaxis=dict(title='W', gridcolor='rgba(0, 255, 65, 0.1)'), xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)'), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


# ═══════════════════════════════════════════════════════════════
# TAB 1: DATA CENTER OVERVIEW
# ═══════════════════════════════════════════════════════════════

def render_data_center_tab(df: pd.DataFrame):
    st.markdown('<div class="dashboard-title">🏢 ZON-RADIANCE DATA CENTER</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Aggregate Fleet Metrics • Real-Time Monitoring</div>', unsafe_allow_html=True)
    
    if df.empty:
        st.error("No data available")
        return
    
    servers = get_server_list(df)
    latest_per_server = df.groupby('host').first().reset_index()
    fleet_status, fleet_class = get_fleet_health(df)
    
    # Fleet Summary
    st.markdown('<div class="section-heading">📊 Fleet Summary</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-card-large"><div class="metric-label">Total Servers</div><div class="metric-value-xl">{len(servers)}</div><div class="metric-sub">active</div></div>', unsafe_allow_html=True)
    with col2:
        total_gpus = latest_per_server['gpu_count'].sum()
        st.markdown(f'<div class="metric-card-large"><div class="metric-label">Total GPUs</div><div class="metric-value-xl text-purple">{int(total_gpus)}</div><div class="metric-sub">H100</div></div>', unsafe_allow_html=True)
    with col3:
        total_power = latest_per_server['gpu_power_total'].sum()
        st.markdown(f'<div class="metric-card-large"><div class="metric-label">Total Power</div><div class="metric-value-xl text-yellow">{total_power:.0f}W</div><div class="metric-sub">{total_power/1000:.2f} kW</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card-large"><div class="metric-label">Fleet Status</div><div style="margin-top: 10px;"><span class="status-badge {fleet_class}">{fleet_status}</span></div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Aggregate Metrics
    st.markdown('<div class="section-heading">⚡ Aggregate Metrics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg GPU Temp</div><div class="metric-value text-orange">{latest_per_server["gpu_temp_avg"].mean():.1f}°C</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg CPU</div><div class="metric-value text-cyan">{latest_per_server["cpu_percent"].mean():.1f}%</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg GPU Util</div><div class="metric-value text-purple">{latest_per_server["gpu_util_avg"].mean():.1f}%</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Avg Memory</div><div class="metric-value">{latest_per_server["mem_percent"].mean():.1f}%</div></div>', unsafe_allow_html=True)
    with col5:
        total_mem_tb = latest_per_server['mem_total_bytes'].sum() / (1024**4)
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total RAM</div><div class="metric-value text-cyan">{total_mem_tb:.1f}TB</div></div>', unsafe_allow_html=True)
    with col6:
        avg_headroom = 85 - latest_per_server['gpu_temp_avg'].mean()
        st.markdown(f'<div class="metric-card"><div class="metric-label">Thermal Headroom</div><div class="metric-value text-ok">{avg_headroom:.1f}°C</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Cost
    st.markdown('<div class="section-heading">💰 Cost & Efficiency</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    total_kw = total_power / 1000
    cost_hr = total_kw * ELECTRICITY_RATE
    
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cost/Hour</div><div class="metric-value text-yellow">${cost_hr:.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cost/Day</div><div class="metric-value text-yellow">${cost_hr*24:.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cost/Month</div><div class="metric-value text-yellow">${cost_hr*24*30:.0f}</div></div>', unsafe_allow_html=True)
    with col4:
        total_util = latest_per_server['cpu_percent'].sum() + latest_per_server['gpu_util_avg'].sum()
        per = total_power / max(1, total_util)
        st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet PER</div><div class="metric-value">{per:.1f}</div><div class="metric-sub">W/%util</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Fleet Power Chart
    st.markdown('<div class="section-heading">📈 Fleet Power Over Time</div>', unsafe_allow_html=True)
    st.plotly_chart(create_fleet_power_chart(df), use_container_width=True, config={'displayModeBar': False})
    
    # Server List
    st.markdown('<div class="section-heading">🖥️ Server Status</div>', unsafe_allow_html=True)
    for _, server in latest_per_server.iterrows():
        host = server['host']
        state, state_class = classify_system_state(server.to_dict())
        st.markdown(f'''<div class="server-card online"><div style="display: flex; justify-content: space-between; align-items: center;"><div><span style="color: var(--nexus-primary); font-weight: 700; font-size: 1.1em;">{host}</span><span style="color: var(--color-muted); margin-left: 15px;">{safe_get(server, "gpu_count", 8)}× H100</span><span style="color: var(--color-muted); margin-left: 15px;">Up: {format_uptime(safe_get(server, "uptime_sec"))}</span></div><div><span class="status-badge {state_class}">{state}</span></div></div><div style="display: flex; gap: 30px; margin-top: 10px; font-size: 0.9em;"><span>Power: <span style="color: var(--nexus-primary);">{safe_get(server, "gpu_power_total"):.0f}W</span></span><span>Temp: <span style="color: var(--color-orange);">{safe_get(server, "gpu_temp_avg"):.1f}°C</span></span><span>CPU: <span style="color: var(--color-cyan);">{safe_get(server, "cpu_percent"):.1f}%</span></span><span>GPU: <span style="color: var(--color-purple);">{safe_get(server, "gpu_util_avg"):.1f}%</span></span><span>Mem: <span style="color: var(--color-yellow);">{safe_get(server, "mem_percent"):.1f}%</span></span></div></div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2: SERVERS
# ═══════════════════════════════════════════════════════════════

def render_servers_tab(df: pd.DataFrame):
    servers = get_server_list(df)
    if not servers:
        st.error("No servers found")
        return
    
    st.markdown('<div class="section-heading">🖥️ Select Server</div>', unsafe_allow_html=True)
    selected_server = st.selectbox("Server:", servers, label_visibility="collapsed")
    
    server_df = fetch_server_metrics(selected_server, limit=200)
    if server_df.empty:
        st.error(f"No data for {selected_server}")
        return
    
    latest = server_df.iloc[0].to_dict()
    previous = server_df.iloc[1].to_dict() if len(server_df) > 1 else None
    
    st.markdown(f'<div class="dashboard-title">📊 {selected_server}</div>', unsafe_allow_html=True)
    
    ts = latest.get('ts')
    if isinstance(ts, str):
        ts = pd.to_datetime(ts)
    state_label, state_class = classify_system_state(latest)
    
    st.markdown(f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;"><span style="color: var(--color-muted);">Last: {ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"}</span><span class="status-badge {state_class}">{state_label}</span></div>', unsafe_allow_html=True)
    
    # Primary Metrics
    st.markdown('<div class="section-heading">📡 Primary Metrics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        p = safe_get(latest, 'gpu_power_total')
        d = get_delta_indicator(p, safe_get(previous, 'gpu_power_total') if previous else None, 'W')
        st.markdown(f'<div class="metric-card"><div class="metric-label">GPU Power</div><div class="metric-value">{p:.1f}W</div><div class="metric-delta">{d}</div></div>', unsafe_allow_html=True)
    with col2:
        t = safe_get(latest, 'gpu_temp_avg')
        d = get_delta_indicator(t, safe_get(previous, 'gpu_temp_avg') if previous else None, '°C')
        st.markdown(f'<div class="metric-card"><div class="metric-label">GPU Temp</div><div class="metric-value text-orange">{t:.1f}°C</div><div class="metric-delta">{d}</div></div>', unsafe_allow_html=True)
    with col3:
        c = safe_get(latest, 'cpu_percent')
        d = get_delta_indicator(c, safe_get(previous, 'cpu_percent') if previous else None, '%')
        st.markdown(f'<div class="metric-card"><div class="metric-label">CPU</div><div class="metric-value text-cyan">{c:.1f}%</div><div class="metric-delta">{d}</div></div>', unsafe_allow_html=True)
    with col4:
        m = safe_get(latest, 'mem_percent')
        d = get_delta_indicator(m, safe_get(previous, 'mem_percent') if previous else None, '%')
        st.markdown(f'<div class="metric-card"><div class="metric-label">Memory</div><div class="metric-value text-yellow">{m:.1f}%</div><div class="metric-delta">{d}</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-label">GPU Util</div><div class="metric-value text-purple">{safe_get(latest, "gpu_util_avg"):.1f}%</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="metric-card"><div class="metric-label">GPU Mem</div><div class="metric-value text-cyan">{safe_get(latest, "gpu_mem_used_avg"):.0f}MB</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Optimizer Metrics
    st.markdown('<div class="section-heading">🧠 Optimizer Metrics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        util = max(1, safe_get(latest, 'cpu_percent') + safe_get(latest, 'gpu_util_avg'))
        per = safe_get(latest, 'gpu_power_total') / util
        st.markdown(f'<div class="metric-card"><div class="metric-label">PER</div><div class="metric-value-sm">{per:.1f}</div><div class="metric-sub">W/%</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Headroom</div><div class="metric-value-sm text-ok">{85 - safe_get(latest, "gpu_temp_avg"):.1f}°C</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cost/Hr</div><div class="metric-value-sm text-yellow">${(safe_get(latest, "gpu_power_total") / 1000) * ELECTRICITY_RATE:.3f}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Load 1m</div><div class="metric-value-sm text-pink">{safe_get(latest, "load1"):.1f}</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Disk</div><div class="metric-value-sm">{safe_get(latest, "disk_root_percent"):.1f}%</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Memory
    st.markdown('<div class="section-heading">💾 Memory & Swap</div>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total RAM</div><div class="metric-value-sm">{format_bytes(safe_get(latest, "mem_total_bytes"))}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Used</div><div class="metric-value-sm text-orange">{format_bytes(safe_get(latest, "mem_used_bytes"))}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Available</div><div class="metric-value-sm text-ok">{format_bytes(safe_get(latest, "mem_available_bytes"))}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Swap Total</div><div class="metric-value-sm">{format_bytes(safe_get(latest, "swap_total_bytes"))}</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Swap Used</div><div class="metric-value-sm text-cyan">{format_bytes(safe_get(latest, "swap_used_bytes"))}</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Swap %</div><div class="metric-value-sm text-ok">{safe_get(latest, "swap_percent"):.1f}%</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Network
    st.markdown('<div class="section-heading">🌐 Network</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Received</div><div class="metric-value-sm text-ok">{format_bytes(safe_get(latest, "net_recv_bps"))}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Sent</div><div class="metric-value-sm text-error">{format_bytes(safe_get(latest, "net_send_bps"))}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    st.markdown('<div class="section-heading">⚡ Power</div>', unsafe_allow_html=True)
    st.plotly_chart(create_power_chart(server_df), use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('<div class="section-heading">🌡️ Thermal</div>', unsafe_allow_html=True)
    st.plotly_chart(create_thermal_chart(server_df), use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('<div class="section-heading">📊 Utilization</div>', unsafe_allow_html=True)
    st.plotly_chart(create_utilization_chart(server_df), use_container_width=True, config={'displayModeBar': False})
    
    # System Info
    st.markdown('<div class="section-heading">ℹ️ System</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Uptime", format_uptime(safe_get(latest, 'uptime_sec')))
    with col2:
        st.metric("Records", f"{len(server_df):,}")
    with col3:
        st.metric("GPUs", f"{safe_get(latest, 'gpu_count', 8)}× H100")
    with col4:
        st.metric("Load 5m/15m", f"{safe_get(latest, 'load5'):.1f}/{safe_get(latest, 'load15'):.1f}")


# ═══════════════════════════════════════════════════════════════
# TAB 3: WIKI
# ═══════════════════════════════════════════════════════════════

def render_wiki_tab():
    st.markdown('<div class="dashboard-title">📚 ZON-RADIANCE WIKI</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Data Dictionary • Glossary • User Guide</div>', unsafe_allow_html=True)
    
    wiki_section = st.radio("Navigate:", ["📖 Overview", "📊 Data Dictionary", "📝 Glossary", "🎯 User Guide", "⚙️ Optimizer"], horizontal=True, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if wiki_section == "📖 Overview":
        st.markdown('''<div class="wiki-section"><h3>🌞 What is ZON-Radiance?</h3><p style="color: var(--color-text); line-height: 1.8;"><strong>ZON-Radiance</strong> is an intelligent power optimization system for GPU data centers. It monitors server metrics, learns energy patterns, and automatically tunes configurations to reduce power waste without sacrificing performance.</p><br><p style="color: var(--nexus-primary); font-style: italic; padding: 10px; background: rgba(0,255,65,0.05); border-radius: 4px;">"Radiance watches your data center servers, learns what's wasting energy, and automatically tunes them to use less power — without hurting performance."</p></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🏗️ System Architecture</h3><table class="wiki-table"><tr><th>Component</th><th>Role</th><th>Description</th></tr><tr><td><span class="glossary-term">🔍 Probe</span></td><td>Eyes & Hands</td><td>Agent on each server collecting metrics and applying tuning.</td></tr><tr><td><span class="glossary-term">🧠 Orchestrator</span></td><td>The Brain</td><td>Cloud service coordinating probes and running optimizers.</td></tr><tr><td><span class="glossary-term">📊 Dashboard</span></td><td>The Window</td><td>This interface - real-time visualization with controls.</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>📈 Dashboard Tabs</h3><table class="wiki-table"><tr><th>Tab</th><th>Purpose</th><th>Features</th></tr><tr><td><span class="glossary-term">🏢 Data Center</span></td><td>Fleet overview</td><td>Aggregate metrics, total power, costs, server grid</td></tr><tr><td><span class="glossary-term">🖥️ Servers</span></td><td>Individual deep-dive</td><td>28 metrics per server, charts, breakdowns</td></tr><tr><td><span class="glossary-term">📚 Wiki</span></td><td>Documentation</td><td>Data dictionary, glossary, guides</td></tr></table></div>''', unsafe_allow_html=True)
    
    elif wiki_section == "📊 Data Dictionary":
        st.markdown('''<div class="wiki-section"><h3>⚡ Power Metrics</h3><table class="wiki-table"><tr><th>Metric</th><th>Column</th><th>Unit</th><th>Description</th></tr><tr><td><span class="glossary-term">GPU Power Total</span></td><td><code>gpu_power_total</code></td><td>W</td><td>Sum of power across all GPUs</td></tr><tr><td><span class="glossary-term">GPU Power Avg</span></td><td><code>gpu_power_avg</code></td><td>W</td><td>Average power per GPU</td></tr><tr><td><span class="glossary-term">Total System Power</span></td><td><code>total_power_watts</code></td><td>W</td><td>Total system power</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🌡️ Thermal</h3><table class="wiki-table"><tr><th>Metric</th><th>Column</th><th>Unit</th><th>Zones</th></tr><tr><td><span class="glossary-term">GPU Temp Avg</span></td><td><code>gpu_temp_avg</code></td><td>°C</td><td>🟢 &lt;60 | 🟡 60-75 | 🟠 75-85 | 🔴 &gt;85</td></tr></table><p style="color: var(--color-text); margin-top: 15px; font-size: 0.9em;">H100 throttles at ~83°C. Thermal Headroom = 85°C - current temp.</p></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🖥️ CPU & Memory</h3><table class="wiki-table"><tr><th>Metric</th><th>Column</th><th>Unit</th></tr><tr><td><span class="glossary-term">CPU Percent</span></td><td><code>cpu_percent</code></td><td>%</td></tr><tr><td><span class="glossary-term">Load 1m/5m/15m</span></td><td><code>load1, load5, load15</code></td><td>Load</td></tr><tr><td><span class="glossary-term">Memory Percent</span></td><td><code>mem_percent</code></td><td>%</td></tr><tr><td><span class="glossary-term">Memory Total/Used/Avail</span></td><td><code>mem_*_bytes</code></td><td>Bytes</td></tr><tr><td><span class="glossary-term">Swap %/Used</span></td><td><code>swap_*</code></td><td>%, Bytes</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🎮 GPU</h3><table class="wiki-table"><tr><th>Metric</th><th>Column</th><th>Unit</th></tr><tr><td><span class="glossary-term">GPU Count</span></td><td><code>gpu_count</code></td><td>Count</td></tr><tr><td><span class="glossary-term">GPU Util Avg</span></td><td><code>gpu_util_avg</code></td><td>%</td></tr><tr><td><span class="glossary-term">GPU Mem Used</span></td><td><code>gpu_mem_used_avg</code></td><td>MB</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🌐 Network & Disk</h3><table class="wiki-table"><tr><th>Metric</th><th>Column</th><th>Unit</th></tr><tr><td><span class="glossary-term">Net Recv/Send</span></td><td><code>net_recv_bps, net_send_bps</code></td><td>Bytes</td></tr><tr><td><span class="glossary-term">Disk Root %</span></td><td><code>disk_root_percent</code></td><td>%</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>ℹ️ Metadata</h3><table class="wiki-table"><tr><th>Metric</th><th>Column</th><th>Type</th></tr><tr><td><span class="glossary-term">Timestamp</span></td><td><code>ts</code></td><td>ISO 8601</td></tr><tr><td><span class="glossary-term">Host</span></td><td><code>host</code></td><td>String</td></tr><tr><td><span class="glossary-term">Uptime</span></td><td><code>uptime_sec</code></td><td>Seconds</td></tr></table></div>''', unsafe_allow_html=True)
    
    elif wiki_section == "📝 Glossary":
        st.markdown('''<div class="wiki-section"><h3>📝 Key Terms</h3><table class="wiki-table"><tr><th>Term</th><th>Definition</th></tr><tr><td><span class="glossary-term">PER</span></td><td>Power Efficiency Ratio = power / (cpu% + gpu%). Lower is better.</td></tr><tr><td><span class="glossary-term">Thermal Headroom</span></td><td>85°C - current temp. Below 10°C is concerning.</td></tr><tr><td><span class="glossary-term">Thermal Throttling</span></td><td>Auto-reduction of GPU clocks at ~83-85°C to prevent damage.</td></tr><tr><td><span class="glossary-term">Load Average</span></td><td>Processes waiting for CPU. Above core count = saturation.</td></tr><tr><td><span class="glossary-term">Fleet</span></td><td>All servers managed by ZON-Radiance.</td></tr><tr><td><span class="glossary-term">Probe</span></td><td>Data collection agent on each server.</td></tr><tr><td><span class="glossary-term">Orchestrator</span></td><td>Central brain running optimizations.</td></tr><tr><td><span class="glossary-term">Policy</span></td><td>Rules constraining what Radiance can optimize.</td></tr><tr><td><span class="glossary-term">H100</span></td><td>NVIDIA flagship GPU. 80GB HBM3, up to 700W TDP.</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🎨 Status Indicators</h3><table class="wiki-table"><tr><th>Status</th><th>Meaning</th><th>Action</th></tr><tr><td><span class="status-badge status-idle">IDLE</span></td><td>GPU &lt;5%</td><td>Consider consolidation if persistent</td></tr><tr><td><span class="status-badge status-light">LIGHT</span></td><td>GPU 5-30%</td><td>Normal operation</td></tr><tr><td><span class="status-badge status-moderate">MODERATE</span></td><td>GPU 30-80%</td><td>Monitor temps</td></tr><tr><td><span class="status-badge status-heavy">HEAVY</span></td><td>GPU &gt;80%</td><td>Ensure cooling</td></tr><tr><td><span class="status-badge status-thermal">THERMAL</span></td><td>Temp &gt;83°C</td><td>⚠️ Check cooling now</td></tr></table></div>''', unsafe_allow_html=True)
    
    elif wiki_section == "🎯 User Guide":
        st.markdown('''<div class="wiki-section"><h3>🏢 Using Data Center Tab</h3><p style="color: var(--color-text);">Answers: <em>"How is my entire fleet performing?"</em></p><ol style="color: var(--color-text); line-height: 2;"><li><strong>Fleet Summary</strong> — Total servers, GPUs, power, health status</li><li><strong>Aggregate Metrics</strong> — Fleet-wide averages</li><li><strong>Cost & Efficiency</strong> — Real-time cost projections and PER</li><li><strong>Fleet Power Chart</strong> — Historical power consumption</li><li><strong>Server Status Grid</strong> — At-a-glance status of each server</li></ol><p style="color: var(--nexus-primary); margin-top: 15px;">💡 Watch Fleet PER — lower values mean better efficiency!</p></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🖥️ Using Servers Tab</h3><p style="color: var(--color-text);">Answers: <em>"What's happening on this specific server?"</em></p><ol style="color: var(--color-text); line-height: 2;"><li><strong>Server Selector</strong> — Choose a server</li><li><strong>Primary Metrics</strong> — Power, temp, CPU, memory with deltas</li><li><strong>Optimizer Metrics</strong> — PER, headroom, cost, load</li><li><strong>Memory & Swap</strong> — Detailed breakdown</li><li><strong>Historical Charts</strong> — Power, thermal, utilization trends</li></ol><p style="color: var(--nexus-primary); margin-top: 15px;">💡 Rising temps with stable utilization = possible cooling issue!</p></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>⚠️ Alert Thresholds</h3><table class="wiki-table"><tr><th>Metric</th><th>🟢 Normal</th><th>🟡 Warning</th><th>🔴 Critical</th></tr><tr><td>GPU Temp</td><td>&lt;60°C</td><td>60-80°C</td><td>&gt;80°C</td></tr><tr><td>Headroom</td><td>&gt;25°C</td><td>10-25°C</td><td>&lt;10°C</td></tr><tr><td>Swap</td><td>&lt;10%</td><td>10-50%</td><td>&gt;50%</td></tr><tr><td>Disk</td><td>&lt;70%</td><td>70-85%</td><td>&gt;85%</td></tr></table></div>''', unsafe_allow_html=True)
    
    elif wiki_section == "⚙️ Optimizer":
        st.markdown('''<div class="wiki-section"><h3>🧠 Optimization Loop</h3><p style="color: var(--color-text);">ZON-Radiance continuously optimizes through:</p><div class="code-block">Collect → Analyze → Experiment → Validate → Apply/Rollback → Repeat</div><ol style="color: var(--color-text); line-height: 2; margin-top: 15px;"><li><strong>Collect</strong> — Probes gather data every 30s</li><li><strong>Analyze</strong> — Global Optimizer identifies inefficient servers</li><li><strong>Experiment</strong> — Local Optimizer tests changes</li><li><strong>Validate</strong> — Confirm savings without performance loss</li><li><strong>Apply</strong> — Successful optimizations become policies</li></ol></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🎯 Key Optimization Metrics</h3><table class="wiki-table"><tr><th>Metric</th><th>Formula</th><th>Goal</th></tr><tr><td><span class="glossary-term">PER</span></td><td>power / (cpu% + gpu%)</td><td>Minimize</td></tr><tr><td><span class="glossary-term">Thermal Headroom</span></td><td>85°C - temp</td><td>Maximize</td></tr><tr><td><span class="glossary-term">Cost/Hour</span></td><td>kW × $0.12</td><td>Minimize</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>📋 What Radiance Can Tune</h3><table class="wiki-table"><tr><th>Parameter</th><th>Effect</th><th>Trade-off</th></tr><tr><td>GPU Power Limit</td><td>Caps max draw</td><td>Less power but lower peak</td></tr><tr><td>GPU Clocks</td><td>Adjust speeds</td><td>Less power, less throughput</td></tr><tr><td>Fan Curves</td><td>Cooling aggression</td><td>Better temps, more power/noise</td></tr><tr><td>Workload Scheduling</td><td>Consolidate to fewer GPUs</td><td>Better efficiency, may add latency</td></tr></table></div>''', unsafe_allow_html=True)
        
        st.markdown('''<div class="wiki-section"><h3>🛡️ Safety Policies</h3><ul style="color: var(--color-text); line-height: 2;"><li>✅ Temperature Guard — Never exceed 83°C</li><li>✅ Performance Floor — Maintain minimum throughput</li><li>✅ Rollback on Failure — Auto-revert bad changes</li><li>✅ Human Approval — Major changes need confirmation</li><li>✅ Audit Trail — All changes logged</li></ul></div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    st.set_page_config(page_title="ZON-Radiance", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
    st.markdown(CONSTRUCT_CSS, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div class="sidebar-title">⚡ ZON-RADIANCE</div>', unsafe_allow_html=True)
        tab = st.radio("Navigation", ["🏢 Data Center", "🖥️ Servers", "📚 Wiki"], label_visibility="collapsed")
        st.markdown("---")
        st.markdown(f'<div style="color: var(--color-muted); font-size: 0.8em; padding: 10px;"><strong>Refresh:</strong> {REFRESH_INTERVAL}s<br><strong>Source:</strong> Supabase<br><strong>Theme:</strong> Construct</div>', unsafe_allow_html=True)
    
    with st.spinner("Loading..."):
        df = fetch_all_metrics(500)
    
    if tab == "🏢 Data Center":
        render_data_center_tab(df)
    elif tab == "🖥️ Servers":
        render_servers_tab(df)
    elif tab == "📚 Wiki":
        render_wiki_tab()
    
    if tab != "📚 Wiki":
        time.sleep(REFRESH_INTERVAL)
        st.rerun()


if __name__ == "__main__":
    main()
