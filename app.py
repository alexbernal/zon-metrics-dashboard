"""
ZON-Radiance GPU Metrics Dashboard
Construct CSS Theme (Matrix Green)
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
    /* Import monospace font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
    
    /* Root variables - Construct theme */
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
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main app background */
    .stApp {
        background: var(--nexus-bg);
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Grid overlay effect */
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
    
    /* Dashboard title */
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
    
    /* Section headings */
    .section-heading {
        color: var(--nexus-primary);
        font-size: 1.1em;
        margin: 20px 0 10px 0;
        border-bottom: 1px solid #222;
        padding-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Latest reading card */
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
    
    /* Metric cards */
    .metric-card {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid var(--nexus-border);
        border-radius: 6px;
        padding: 15px;
        text-align: center;
    }
    
    .metric-label {
        color: var(--color-muted);
        font-size: 0.75em;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    
    .metric-value {
        color: var(--nexus-primary);
        font-size: 1.8em;
        font-weight: 700;
    }
    
    .metric-delta {
        font-size: 0.8em;
        margin-top: 5px;
    }
    
    .delta-up { color: var(--color-warn); }
    .delta-down { color: var(--color-ok); }
    .delta-flat { color: var(--color-muted); }
    
    /* Status badges */
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
    
    /* Thermal zones */
    .thermal-optimal { color: #22c55e; }
    .thermal-normal { color: #eab308; }
    .thermal-high { color: #f97316; }
    .thermal-critical { color: #ef4444; }
    
    /* Info cards */
    .info-card {
        background: #1a1a2e;
        border: 1px solid #222;
        border-radius: 6px;
        padding: 12px;
        margin: 10px 0;
    }
    
    .info-card code {
        color: var(--color-ok);
    }
    
    /* Chart containers */
    .chart-container {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--nexus-border);
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
    }
    
    /* Streamlit metric overrides */
    [data-testid="stMetricValue"] {
        color: var(--nexus-primary) !important;
    }
    
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    
    /* Make charts use theme colors */
    .stPlotlyChart {
        background: transparent !important;
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
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_bytes(bytes_val: float) -> str:
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def get_delta_indicator(current: float, previous: float, unit: str = "", inverse: bool = False) -> str:
    """Generate delta indicator HTML."""
    if previous is None or pd.isna(previous):
        return '<span class="delta-flat">━ N/A</span>'
    
    diff = current - previous
    
    if abs(diff) < 0.01:
        return f'<span class="delta-flat">━ 0.0{unit}</span>'
    
    # For power/temp, down is good (inverse=False means up is bad)
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
        # Tight scaling for stable data
        mean_val = (min_val + max_val) / 2
        return mean_val - min_range / 2, mean_val + min_range / 2
    else:
        # Wider scaling with padding
        padding = data_range * padding_percent
        return min_val - padding, max_val + padding


# ═══════════════════════════════════════════════════════════════
# Chart Functions
# ═══════════════════════════════════════════════════════════════

def create_power_chart(df: pd.DataFrame):
    """Create power metrics chart with dynamic scaling."""
    import plotly.graph_objects as go
    
    # Sort chronologically for chart
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
    
    # Add rolling average
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
        height=300,
        yaxis=dict(
            range=[y_min, y_max],
            title='Watts',
            gridcolor='rgba(0, 255, 65, 0.1)',
            tickformat='.0f'
        ),
        xaxis=dict(
            gridcolor='rgba(0, 255, 65, 0.1)',
            title=''
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
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
    
    # Add thermal zone backgrounds
    if y_max > 60:
        fig.add_hrect(y0=60, y1=min(75, y_max), fillcolor="rgba(234, 179, 8, 0.1)", line_width=0)
    if y_max > 75:
        fig.add_hrect(y0=75, y1=min(85, y_max), fillcolor="rgba(249, 115, 22, 0.1)", line_width=0)
    if y_max > 85:
        fig.add_hrect(y0=85, y1=y_max, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0)
    
    # Temperature line
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=df_chart['gpu_temp_avg'],
        mode='lines',
        name='GPU Temp (Avg)',
        line=dict(color='#f97316', width=2),
        fill='tozeroy',
        fillcolor='rgba(249, 115, 22, 0.1)'
    ))
    
    # Thermal headroom line
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
        height=300,
        yaxis=dict(
            range=[y_min, y_max],
            title='Temperature (°C)',
            gridcolor='rgba(0, 255, 65, 0.1)',
            tickformat='.1f'
        ),
        yaxis2=dict(
            title='Headroom (°C)',
            overlaying='y',
            side='right',
            range=[0, 55],
            gridcolor='rgba(0, 0, 0, 0)'
        ),
        xaxis=dict(
            gridcolor='rgba(0, 255, 65, 0.1)',
            title=''
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig


def create_resources_chart(df: pd.DataFrame):
    """Create resource utilization chart."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    df_chart = df.sort_values('ts')
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('CPU & GPU Utilization (%)', 'Memory & Load')
    )
    
    # CPU utilization
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=df_chart['cpu_percent'],
        mode='lines',
        name='CPU %',
        line=dict(color='#8be9fd', width=2)
    ), row=1, col=1)
    
    # GPU utilization
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=df_chart['gpu_util_avg'],
        mode='lines',
        name='GPU Util %',
        line=dict(color='#bd93f9', width=2)
    ), row=1, col=1)
    
    # Memory percent
    fig.add_trace(go.Scatter(
        x=df_chart['ts'],
        y=df_chart['mem_percent'],
        mode='lines',
        name='Memory %',
        line=dict(color='#f1fa8c', width=2)
    ), row=2, col=1)
    
    # Load average (scaled to fit)
    if 'load1' in df_chart.columns:
        # Normalize load to 0-100 range for display
        max_load = df_chart['load1'].max()
        if max_load > 0:
            load_scaled = (df_chart['load1'] / max_load) * 50  # Scale to max 50%
            fig.add_trace(go.Scatter(
                x=df_chart['ts'],
                y=load_scaled,
                mode='lines',
                name=f'Load 1m (scaled)',
                line=dict(color='#ff79c6', width=1, dash='dash')
            ), row=2, col=1)
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        margin=dict(l=50, r=20, t=40, b=50),
        height=400,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.05,
            xanchor='right',
            x=1
        )
    )
    
    # Update y-axes
    fig.update_yaxes(gridcolor='rgba(0, 255, 65, 0.1)', row=1, col=1)
    fig.update_yaxes(gridcolor='rgba(0, 255, 65, 0.1)', row=2, col=1)
    fig.update_xaxes(gridcolor='rgba(0, 255, 65, 0.1)')
    
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
    
    # Inject Construct CSS
    st.markdown(CONSTRUCT_CSS, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="dashboard-title">⚡ ZON-RADIANCE METRICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">bizon1 • 8× NVIDIA H100 • Real-Time Monitoring</div>', unsafe_allow_html=True)
    
    # Fetch data
    with st.spinner("Loading metrics..."):
        df = fetch_metrics(200)
    
    if df.empty:
        st.error("No data available. Check Supabase connection and RLS policies.")
        st.stop()
    
    # Get latest and previous readings
    latest = df.iloc[0].to_dict()
    previous = df.iloc[1].to_dict() if len(df) > 1 else None
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 1: LATEST READING (TOP)
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">📡 Latest Reading</div>', unsafe_allow_html=True)
    
    # Timestamp and system state
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
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        power = latest.get('gpu_power_total', 0)
        prev_power = previous.get('gpu_power_total') if previous else None
        delta = get_delta_indicator(power, prev_power, 'W')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Power</div>
                <div class="metric-value">{power:.1f}W</div>
                <div class="metric-delta">{delta} (vs prev)</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        temp = latest.get('gpu_temp_avg', 0)
        prev_temp = previous.get('gpu_temp_avg') if previous else None
        delta = get_delta_indicator(temp, prev_temp, '°C')
        thermal_class = get_thermal_class(temp)
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Temp</div>
                <div class="metric-value {thermal_class}">{temp:.1f}°C</div>
                <div class="metric-delta">{delta} (vs prev)</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        cpu = latest.get('cpu_percent', 0)
        prev_cpu = previous.get('cpu_percent') if previous else None
        delta = get_delta_indicator(cpu, prev_cpu, '%')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">CPU</div>
                <div class="metric-value">{cpu:.1f}%</div>
                <div class="metric-delta">{delta} (vs prev)</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        mem = latest.get('mem_percent', 0)
        prev_mem = previous.get('mem_percent') if previous else None
        delta = get_delta_indicator(mem, prev_mem, '%')
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Memory</div>
                <div class="metric-value">{mem:.1f}%</div>
                <div class="metric-delta">{delta} (vs prev)</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 2: ADVANCED METRICS (Radiance Optimizer)
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">🧠 Radiance Optimizer Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Power Efficiency Ratio (PER)
    with col1:
        power = latest.get('gpu_power_total', 0) or 0
        cpu = latest.get('cpu_percent', 0) or 0
        gpu_util = latest.get('gpu_util_avg', 0) or 0
        total_util = max(1, cpu + gpu_util)
        per = power / total_util
        
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Power Efficiency Ratio</div>
                <div class="metric-value">{per:.1f}</div>
                <div class="metric-delta" style="color: #555;">W per % utilization</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Thermal Headroom
    with col2:
        temp = latest.get('gpu_temp_avg', 0) or 0
        headroom = 85 - temp
        headroom_class = 'thermal-optimal' if headroom > 30 else ('thermal-normal' if headroom > 15 else ('thermal-high' if headroom > 5 else 'thermal-critical'))
        
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Thermal Headroom</div>
                <div class="metric-value {headroom_class}">{headroom:.1f}°C</div>
                <div class="metric-delta" style="color: #555;">until throttle (85°C)</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Energy Cost (Hourly)
    with col3:
        power = latest.get('gpu_power_total', 0) or 0
        cost_per_hour = (power / 1000) * ELECTRICITY_RATE
        cost_per_day = cost_per_hour * 24
        cost_per_month = cost_per_day * 30
        
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Energy Cost</div>
                <div class="metric-value" style="color: #f1fa8c;">${cost_per_hour:.2f}/hr</div>
                <div class="metric-delta" style="color: #555;">${cost_per_day:.2f}/day • ${cost_per_month:.0f}/mo</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # GPU Utilization (simplified load metric since we don't have per-GPU data)
    with col4:
        gpu_util = latest.get('gpu_util_avg', 0) or 0
        gpu_count = latest.get('gpu_count', 8) or 8
        
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">GPU Fleet</div>
                <div class="metric-value" style="color: #bd93f9;">{gpu_util:.1f}%</div>
                <div class="metric-delta" style="color: #555;">{gpu_count}× H100 avg util</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 3: POWER CHART
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">⚡ Power Consumption</div>', unsafe_allow_html=True)
    
    power_fig = create_power_chart(df)
    st.plotly_chart(power_fig, use_container_width=True, config={'displayModeBar': False})
    
    # Power stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current", f"{latest.get('gpu_power_total', 0):.1f} W")
    with col2:
        st.metric("Peak (session)", f"{df['gpu_power_total'].max():.1f} W")
    with col3:
        st.metric("Average", f"{df['gpu_power_total'].mean():.1f} W")
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 4: THERMAL CHART
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">🌡️ Thermal Monitoring</div>', unsafe_allow_html=True)
    
    thermal_fig = create_thermal_chart(df)
    st.plotly_chart(thermal_fig, use_container_width=True, config={'displayModeBar': False})
    
    # Thermal legend
    st.markdown('''
        <div style="display: flex; gap: 20px; font-size: 0.8em; margin-top: -10px; margin-bottom: 20px;">
            <span class="thermal-optimal">🟢 Optimal (&lt;60°C)</span>
            <span class="thermal-normal">🟡 Normal (60-75°C)</span>
            <span class="thermal-high">🟠 High (75-85°C)</span>
            <span class="thermal-critical">🔴 Critical (&gt;85°C)</span>
        </div>
    ''', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 5: RESOURCES CHART
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">📊 Resource Utilization</div>', unsafe_allow_html=True)
    
    resources_fig = create_resources_chart(df)
    st.plotly_chart(resources_fig, use_container_width=True, config={'displayModeBar': False})
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 6: SYSTEM INFO
    # ═══════════════════════════════════════════════════════════
    
    st.markdown('<div class="section-heading">ℹ️ System Information</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        uptime = latest.get('uptime_sec', 0)
        st.metric("Uptime", format_uptime(uptime))
    
    with col2:
        st.metric("Records", f"{len(df):,}")
    
    with col3:
        host = latest.get('host', 'unknown')
        st.metric("Server", host)
    
    with col4:
        gpu_count = latest.get('gpu_count', 8)
        st.metric("GPUs", f"{gpu_count}× H100")
    
    # Footer with refresh info
    st.markdown(f'''
        <div style="text-align: center; color: #555; font-size: 0.75em; margin-top: 30px; padding: 20px;">
            ZON-Radiance Dashboard • Auto-refresh every {REFRESH_INTERVAL}s • 
            Data range: {df['ts'].min().strftime("%H:%M")} - {df['ts'].max().strftime("%H:%M")} UTC
        </div>
    ''', unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(REFRESH_INTERVAL)
    st.rerun()


if __name__ == "__main__":
    main()
