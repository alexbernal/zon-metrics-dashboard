"""
ZON-Radiance GPU Metrics Dashboard
Construct CSS Theme (Matrix Green)
Full metrics display - all 28 available columns
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
REFRESH_INTERVAL = 30  # seconds
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
    
    .latest-card {
        background: rgba(0, 255, 65, 0.05);
        border: 1px solid var(--nexus-border);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .latest-timestamp {
        color: var(--nexus-primary);
        font-size: 0.9em;
        margin-bottom: 15px;
    }
    
    .metric-card {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid var(--nexus-border);
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        height: 100%;
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
    
    [data-testid="stMetricValue"] {
        color: var(--nexus-primary) !important;
    }
    
    .mini-chart {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--nexus-border);
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client with anon key."""
    api_key = st.secrets.get("SUPABASE_ANON_KEY", "")
    if not api_key:
        st.error("⚠️ SUPABASE_ANON_KEY not found in secrets")
        st.stop()
    return create_client(SUPABASE_URL, api_key)


def fetch_metrics(limit: int = 200) -> pd.DataFrame:
    """Fetch metrics from Supabase, latest first."""
    client = get_supabase_client()
    response = client.table(TABLE_NAME).select("*").order("ts", desc=True).limit(limit).execute()
    
    if not response.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response.data)
    df['ts'] = pd.to_datetime(df['ts'])
    return df


def format_uptime(seconds: float) -> str:
    """Format uptime seconds to human readable."""
    if not seconds:
        return "N/A"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_bytes(bytes_val: float, precision: int = 1) -> str:
    """Format bytes to human readable."""
    if bytes_val is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.{precision}f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.{precision}f} PB"


def format_bps(bps: float) -> str:
    """Format bits per second to human readable."""
    if bps is None:
        return "N/A"
    for unit in ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']:
        if abs(bps) < 1000.0:
            return f"{bps:.1f} {unit}"
        bps /= 1000.0
    return f"{bps:.1f} Pbps"


def get_delta_indicator(current: float, previous: float, unit: str = "", inverse: bool = False) -> str:
    """Generate delta indicator HTML."""
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
    """Classify system state based on metrics."""
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


def get_thermal_class(temp: float) -> str:
    """Get CSS class for thermal zone."""
    if temp is None:
        return ''
    if temp < 60:
        return 'thermal-optimal'
    elif temp < 75:
        return 'thermal-normal'
    elif temp < 85:
        return 'thermal-high'
    return 'thermal-critical'


def calculate_dynamic_range(data: list, padding_percent: float = 0.1, min_range: float = 10) -> tuple[float, float]:
    """Calculate dynamic Y-axis range for charts."""
    if not data or len(data) == 0:
        return 0, 100
    
    data_clean = [x for x in data if x is not None and not pd.isna(x)]
    if not data_clean:
        return 0, 100
    
    min_val = min(data_clean)
    max_val = max(data_clean)
    data_range = max_val - min_val
    
    if data_range < min_range:
        mean_val = (min_val + max_val) / 2
        return mean_val - min_range / 2, mean_val + min_range / 2
    else:
        padding = data_range * padding_percent
        return min_val - padding, max_val + padding


def safe_get(d: dict, key: str, default=0):
    """Safely get a value from dict, returning default if None."""
    val = d.get(key, default)
    return default if val is None else val


# ═══════════════════════════════════════════════════════════════
# Chart Functions
# ═══════════════════════════════════════════════════════════════

def create_power_chart(df: pd.DataFrame):
    """Create power metrics chart with dynamic scaling."""
    import plotly.graph_objects as go
    
    df_chart = df.sort_values('ts')
    y_min, y_max = calculate_dynamic_range(df_chart['gpu_power_total'].tolist(), min_range=20)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=df_chart['gpu_power_total'],
        mode='lines',
        name='GPU Power (Total)',
        line=dict(color='#00ff41', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 65, 0.1)'
    ))
    
    if len(df_chart) >= 5:
        rolling_avg = df_chart['gpu_power_total'].rolling(window=5).mean()
        fig.add_trace(go.Scatter(
            x=df_chart['ts'],
            y=rolling_avg,
            mode='lines',
            name='5-Point Avg',
            line=dict(color='#8be9fd', width=1, dash='dash')
        ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=20, t=30, b=50),
        height=280,
        yaxis=dict(range=[y_min, y_max], title='Watts', gridcolor='rgba(0, 255, 65, 0.1)', tickformat='.0f'),
        xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        showlegend=True
    )
    
    return fig


def create_thermal_chart(df: pd.DataFrame):
    """Create thermal metrics chart with zone coloring."""
    import plotly.graph_objects as go
    
    df_chart = df.sort_values('ts')
    y_min, y_max = calculate_dynamic_range(df_chart['gpu_temp_avg'].tolist(), min_range=10)
    y_min = max(30, y_min)
    y_max = min(95, y_max)
    
    fig = go.Figure()
    
    if y_max > 60:
        fig.add_hrect(y0=60, y1=min(75, y_max), fillcolor="rgba(234, 179, 8, 0.1)", line_width=0)
    if y_max > 75:
        fig.add_hrect(y0=75, y1=min(85, y_max), fillcolor="rgba(249, 115, 22, 0.1)", line_width=0)
    if y_max > 85:
        fig.add_hrect(y0=85, y1=y_max, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0)
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=df_chart['gpu_temp_avg'],
        mode='lines',
        name='GPU Temp (Avg)',
        line=dict(color='#f97316', width=2),
        fill='tozeroy',
        fillcolor='rgba(249, 115, 22, 0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=85 - df_chart['gpu_temp_avg'],
        mode='lines',
        name='Thermal Headroom',
        line=dict(color='#22c55e', width=1, dash='dot'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=50, t=30, b=50),
        height=280,
        yaxis=dict(range=[y_min, y_max], title='Temperature (°C)', gridcolor='rgba(0, 255, 65, 0.1)', tickformat='.1f'),
        yaxis2=dict(title='Headroom (°C)', overlaying='y', side='right', range=[0, 55], gridcolor='rgba(0, 0, 0, 0)'),
        xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def create_cpu_gpu_chart(df: pd.DataFrame):
    """Create CPU and GPU utilization chart."""
    import plotly.graph_objects as go
    
    df_chart = df.sort_values('ts')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['cpu_percent'],
        mode='lines', name='CPU %',
        line=dict(color='#8be9fd', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['gpu_util_avg'],
        mode='lines', name='GPU Util %',
        line=dict(color='#bd93f9', width=2)
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=20, t=30, b=50),
        height=250,
        yaxis=dict(range=[0, 100], title='Utilization %', gridcolor='rgba(0, 255, 65, 0.1)'),
        xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def create_memory_chart(df: pd.DataFrame):
    """Create memory utilization chart."""
    import plotly.graph_objects as go
    
    df_chart = df.sort_values('ts')
    y_min, y_max = calculate_dynamic_range(df_chart['mem_percent'].tolist(), min_range=5)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['mem_percent'],
        mode='lines', name='Memory %',
        line=dict(color='#f1fa8c', width=2),
        fill='tozeroy', fillcolor='rgba(241, 250, 140, 0.1)'
    ))
    
    # GPU Memory (scaled to percentage of typical max ~80GB per GPU)
    if 'gpu_mem_used_avg' in df_chart.columns:
        gpu_mem_pct = (df_chart['gpu_mem_used_avg'] / 81920) * 100  # 80GB = 81920MB
        fig.add_trace(go.Scatter(
            x=df_chart['ts'], y=gpu_mem_pct,
            mode='lines', name='GPU Mem %',
            line=dict(color='#bd93f9', width=2, dash='dash')
        ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=20, t=30, b=50),
        height=250,
        yaxis=dict(range=[0, max(y_max, 25)], title='Memory %', gridcolor='rgba(0, 255, 65, 0.1)'),
        xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def create_load_chart(df: pd.DataFrame):
    """Create load average chart with all three averages."""
    import plotly.graph_objects as go
    
    df_chart = df.sort_values('ts')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['load1'],
        mode='lines', name='Load 1m',
        line=dict(color='#ff79c6', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['load5'],
        mode='lines', name='Load 5m',
        line=dict(color='#ffb86c', width=1.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['load15'],
        mode='lines', name='Load 15m',
        line=dict(color='#6272a4', width=1)
    ))
    
    y_min, y_max = calculate_dynamic_range(df_chart['load1'].tolist(), min_range=5)
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=20, t=30, b=50),
        height=250,
        yaxis=dict(range=[max(0, y_min), y_max], title='Load Average', gridcolor='rgba(0, 255, 65, 0.1)'),
        xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


def create_network_chart(df: pd.DataFrame):
    """Create network I/O chart."""
    import plotly.graph_objects as go
    
    df_chart = df.sort_values('ts')
    
    # Calculate rate of change (derivative) since values are cumulative
    df_chart = df_chart.copy()
    df_chart['net_recv_rate'] = df_chart['net_recv_bps'].diff() / df_chart['ts'].diff().dt.total_seconds()
    df_chart['net_send_rate'] = df_chart['net_send_bps'].diff() / df_chart['ts'].diff().dt.total_seconds()
    
    # Filter out negative values (counter resets) and extreme outliers
    df_chart.loc[df_chart['net_recv_rate'] < 0, 'net_recv_rate'] = None
    df_chart.loc[df_chart['net_send_rate'] < 0, 'net_send_rate'] = None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['net_recv_rate'] / 1e6,  # Convert to MB/s
        mode='lines', name='Recv (MB/s)',
        line=dict(color='#50fa7b', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_chart['ts'], y=df_chart['net_send_rate'] / 1e6,  # Convert to MB/s
        mode='lines', name='Send (MB/s)',
        line=dict(color='#ff5555', width=2)
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=20, t=30, b=50),
        height=250,
        yaxis=dict(title='MB/s', gridcolor='rgba(0, 255, 65, 0.1)'),
        xaxis=dict(gridcolor='rgba(0, 255, 65, 0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


# ═══════════════════════════════════════════════════════════════
# Main Dashboard
# ═══════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="ZON-Radiance Metrics",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown(CONSTRUCT_CSS, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="dashboard-title">⚡ ZON-RADIANCE METRICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">bizon1 • 8× NVIDIA H100 • Real-Time Monitoring • All 28 Metrics</div>', unsafe_allow_html=True)
    
    # Fetch data
    with st.spinner("Loading metrics..."):
        df = fetch_metrics(200)
    
    if df.empty:
        st.error("No data available. Check Supabase connection and RLS policies.")
        st.stop()
    
    latest = df.iloc[0].to_dict()
    previous = df.iloc[1].to_dict() if len(df) > 1 else None
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 1: LATEST READING (TOP)
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">📡 Latest Reading</div>', unsafe_allow_html=True)
    
    ts = latest.get('ts')
    if isinstance(ts, str):
        ts = pd.to_datetime(ts)
    time_ago = datetime.now(ts.tzinfo) - ts if ts else None
    time_ago_str = f"{int(time_ago.total_seconds())} seconds ago" if time_ago else "N/A"
    
    state_label, state_class = classify_system_state(latest)
    
    col_ts, col_state = st.columns([3, 1])
    with col_ts:
        st.markdown(f'''
            <div class="latest-timestamp">
                🕐 {ts.strftime("%Y-%m-%d %H:%M:%S UTC") if ts else "N/A"} 
                <span style="color: #555;">({time_ago_str})</span>
            </div>
        ''', unsafe_allow_html=True)
    with col_state:
        st.markdown(f'<span class="status-badge {state_class}">{state_label}</span>', unsafe_allow_html=True)
    
    # Primary metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        power = safe_get(latest, 'gpu_power_total')
        prev_power = safe_get(previous, 'gpu_power_total') if previous else None
        delta = get_delta_indicator(power, prev_power, 'W')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Power</div>
                <div class="metric-value">{power:.1f}W</div>
                <div class="metric-delta">{delta}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        temp = safe_get(latest, 'gpu_temp_avg')
        prev_temp = safe_get(previous, 'gpu_temp_avg') if previous else None
        delta = get_delta_indicator(temp, prev_temp, '°C')
        thermal_class = get_thermal_class(temp)
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Temp</div>
                <div class="metric-value {thermal_class}">{temp:.1f}°C</div>
                <div class="metric-delta">{delta}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        cpu = safe_get(latest, 'cpu_percent')
        prev_cpu = safe_get(previous, 'cpu_percent') if previous else None
        delta = get_delta_indicator(cpu, prev_cpu, '%')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">CPU</div>
                <div class="metric-value">{cpu:.1f}%</div>
                <div class="metric-delta">{delta}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        mem = safe_get(latest, 'mem_percent')
        prev_mem = safe_get(previous, 'mem_percent') if previous else None
        delta = get_delta_indicator(mem, prev_mem, '%')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Memory</div>
                <div class="metric-value">{mem:.1f}%</div>
                <div class="metric-delta">{delta}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        gpu_util = safe_get(latest, 'gpu_util_avg')
        prev_gpu = safe_get(previous, 'gpu_util_avg') if previous else None
        delta = get_delta_indicator(gpu_util, prev_gpu, '%')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Util</div>
                <div class="metric-value text-purple">{gpu_util:.1f}%</div>
                <div class="metric-delta">{delta}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col6:
        gpu_mem = safe_get(latest, 'gpu_mem_used_avg')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Mem</div>
                <div class="metric-value text-cyan">{gpu_mem:.0f}MB</div>
                <div class="metric-sub">per GPU avg</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 2: RADIANCE OPTIMIZER METRICS
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">🧠 Radiance Optimizer Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        power = safe_get(latest, 'gpu_power_total')
        cpu = safe_get(latest, 'cpu_percent')
        gpu_util = safe_get(latest, 'gpu_util_avg')
        total_util = max(1, cpu + gpu_util)
        per = power / total_util
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Power Efficiency Ratio</div>
                <div class="metric-value-sm">{per:.1f}</div>
                <div class="metric-sub">W per % util</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        temp = safe_get(latest, 'gpu_temp_avg')
        headroom = 85 - temp
        headroom_class = 'thermal-optimal' if headroom > 30 else ('thermal-normal' if headroom > 15 else ('thermal-high' if headroom > 5 else 'thermal-critical'))
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Thermal Headroom</div>
                <div class="metric-value-sm {headroom_class}">{headroom:.1f}°C</div>
                <div class="metric-sub">until throttle</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        power = safe_get(latest, 'gpu_power_total')
        cost_per_hour = (power / 1000) * ELECTRICITY_RATE
        cost_per_day = cost_per_hour * 24
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Energy Cost</div>
                <div class="metric-value-sm text-yellow">${cost_per_hour:.2f}/hr</div>
                <div class="metric-sub">${cost_per_day:.2f}/day</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        load1 = safe_get(latest, 'load1')
        load5 = safe_get(latest, 'load5')
        load15 = safe_get(latest, 'load15')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Load Average</div>
                <div class="metric-value-sm text-pink">{load1:.1f}</div>
                <div class="metric-sub">{load5:.1f} / {load15:.1f}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        disk = safe_get(latest, 'disk_root_percent')
        disk_class = 'text-ok' if disk < 70 else ('text-warn' if disk < 85 else 'text-error')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Disk Usage</div>
                <div class="metric-value-sm {disk_class}">{disk:.1f}%</div>
                <div class="metric-sub">root partition</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 3: MEMORY & SWAP DETAILS
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">💾 Memory & Swap Details</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        mem_total = safe_get(latest, 'mem_total_bytes')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Total RAM</div>
                <div class="metric-value-sm">{format_bytes(mem_total)}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        mem_used = safe_get(latest, 'mem_used_bytes')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Used RAM</div>
                <div class="metric-value-sm text-orange">{format_bytes(mem_used)}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        mem_avail = safe_get(latest, 'mem_available_bytes')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Available RAM</div>
                <div class="metric-value-sm text-ok">{format_bytes(mem_avail)}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        swap_total = safe_get(latest, 'swap_total_bytes')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Total Swap</div>
                <div class="metric-value-sm">{format_bytes(swap_total)}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        swap_used = safe_get(latest, 'swap_used_bytes')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Used Swap</div>
                <div class="metric-value-sm text-cyan">{format_bytes(swap_used)}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col6:
        swap_pct = safe_get(latest, 'swap_percent')
        swap_class = 'text-ok' if swap_pct < 20 else ('text-warn' if swap_pct < 50 else 'text-error')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Swap %</div>
                <div class="metric-value-sm {swap_class}">{swap_pct:.1f}%</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 4: NETWORK I/O
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">🌐 Network I/O</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        net_recv = safe_get(latest, 'net_recv_bps')
        net_send = safe_get(latest, 'net_send_bps')
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">Total Received</div>
                    <div class="metric-value-sm text-ok">{format_bytes(net_recv)}</div>
                    <div class="metric-sub">cumulative</div>
                </div>
            ''', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">Total Sent</div>
                    <div class="metric-value-sm text-error">{format_bytes(net_send)}</div>
                    <div class="metric-sub">cumulative</div>
                </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        network_fig = create_network_chart(df)
        st.plotly_chart(network_fig, use_container_width=True, config={'displayModeBar': False})
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 5: POWER CHART
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">⚡ Power Consumption</div>', unsafe_allow_html=True)
    
    power_fig = create_power_chart(df)
    st.plotly_chart(power_fig, use_container_width=True, config={'displayModeBar': False})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current", f"{safe_get(latest, 'gpu_power_total'):.1f} W")
    with col2:
        st.metric("Peak", f"{df['gpu_power_total'].max():.1f} W")
    with col3:
        st.metric("Average", f"{df['gpu_power_total'].mean():.1f} W")
    with col4:
        per_gpu = safe_get(latest, 'gpu_power_avg')
        st.metric("Per GPU Avg", f"{per_gpu:.1f} W")
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 6: THERMAL CHART
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">🌡️ Thermal Monitoring</div>', unsafe_allow_html=True)
    
    thermal_fig = create_thermal_chart(df)
    st.plotly_chart(thermal_fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('''
        <div style="display: flex; gap: 20px; font-size: 0.8em; margin-top: -10px; margin-bottom: 20px;">
            <span class="thermal-optimal">🟢 Optimal (&lt;60°C)</span>
            <span class="thermal-normal">🟡 Normal (60-75°C)</span>
            <span class="thermal-high">🟠 High (75-85°C)</span>
            <span class="thermal-critical">🔴 Critical (&gt;85°C)</span>
        </div>
    ''', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 7: CPU & GPU UTILIZATION
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">📊 CPU & GPU Utilization</div>', unsafe_allow_html=True)
    
    cpu_gpu_fig = create_cpu_gpu_chart(df)
    st.plotly_chart(cpu_gpu_fig, use_container_width=True, config={'displayModeBar': False})
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 8: MEMORY CHART
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">🧠 Memory Utilization</div>', unsafe_allow_html=True)
    
    memory_fig = create_memory_chart(df)
    st.plotly_chart(memory_fig, use_container_width=True, config={'displayModeBar': False})
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 9: LOAD AVERAGE
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">📈 Load Average</div>', unsafe_allow_html=True)
    
    load_fig = create_load_chart(df)
    st.plotly_chart(load_fig, use_container_width=True, config={'displayModeBar': False})
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 10: SYSTEM INFO
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">ℹ️ System Information</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        uptime = safe_get(latest, 'uptime_sec')
        st.metric("Uptime", format_uptime(uptime))
    
    with col2:
        st.metric("Records", f"{len(df):,}")
    
    with col3:
        host = latest.get('host', 'unknown')
        st.metric("Server", host)
    
    with col4:
        gpu_count = safe_get(latest, 'gpu_count', 8)
        st.metric("GPUs", f"{gpu_count}× H100")
    
    with col5:
        machine_id = latest.get('machine_id', 'N/A')
        if machine_id and machine_id != 'N/A':
            st.metric("Machine ID", machine_id[:12] + "...")
        else:
            st.metric("Machine ID", "N/A")
    
    # Footer
    st.markdown(f'''
        <div style="text-align: center; color: #555; font-size: 0.75em; margin-top: 30px; padding: 20px; border-top: 1px solid #222;">
            ZON-Radiance Dashboard v2.0 • Displaying all 28 available metrics • Auto-refresh every {REFRESH_INTERVAL}s<br>
            Data range: {df['ts'].min().strftime("%Y-%m-%d %H:%M")} - {df['ts'].max().strftime("%Y-%m-%d %H:%M")} UTC
        </div>
    ''', unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(REFRESH_INTERVAL)
    st.rerun()


if __name__ == "__main__":
    main()
