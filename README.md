# ZON Radiance - GPU Server Metrics Dashboard

Real-time visualization dashboard for bizon1 GPU server metrics (8× NVIDIA H100 80GB).

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat&logo=supabase&logoColor=white)

## Features

- **Real-Time Metrics**: GPU power, CPU, memory, and utilization
- **Time Series Charts**: Power, temperature, and resource trends
- **System Health**: Load averages, memory breakdown
- **Cost Estimation**: Daily electricity cost calculator
- **Auto-Refresh**: Updates every 30 seconds

## Quick Start

### 1. Deploy to Streamlit Cloud (Recommended)

1. Fork this repo to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo → `app.py`
5. Add your Supabase ANON key in **Secrets**:
   ```toml
   SUPABASE_ANON_KEY = "your-anon-key-here"
   ```
6. Deploy!

### 2. Run Locally

```bash
# Clone the repo
git clone https://github.com/alexbernal/zon-metrics-dashboard.git
cd zon-metrics-dashboard

# Install dependencies
pip install -r requirements.txt

# Set up secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your SUPABASE_ANON_KEY

# Run
streamlit run app.py
```

## Supabase Setup

This dashboard uses Supabase's **ANON key** (not the service key) with Row Level Security (RLS).

### Enable RLS on your table:

```sql
-- Enable Row Level Security
ALTER TABLE sandbox_server_metrics ENABLE ROW LEVEL SECURITY;

-- Allow public READ access (no writes)
CREATE POLICY "Public read access" 
ON sandbox_server_metrics 
FOR SELECT 
USING (true);
```

### Get your ANON key:

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Settings → API
4. Copy the `anon` `public` key (NOT the service_role key!)

## Data Source

| Field | Description |
|-------|-------------|
| `gpu_power_total` | Total GPU power draw (Watts) |
| `gpu_temp_avg` | Average GPU temperature (°C) |
| `gpu_util_avg` | Average GPU utilization (%) |
| `cpu_percent` | CPU utilization (%) |
| `mem_percent` | Memory utilization (%) |
| `load1/5/15` | System load averages |
| `uptime_sec` | Server uptime (seconds) |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   bizon1        │     │    Supabase     │     │   Streamlit     │
│   (H100 GPUs)   │────▶│   (Postgres)    │────▶│   Dashboard     │
│                 │     │                 │     │                 │
│   Probe Agent   │     │  RLS Protected  │     │  Public URL     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## License

Internal use - ZON Energy
