import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
import s3fs
import numpy as np
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Market Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}
.stApp {
    background: #080C18;
    color: #E2E8F0;
}
.block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1400px;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Header ── */
.dash-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 1.5rem 0;
    border-bottom: 1px solid rgba(0,212,255,0.15);
    margin-bottom: 1.5rem;
}
.dash-title {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #F8FAFC;
}
.dash-title span { color: #00D4FF; }
.dash-subtitle {
    font-size: 0.78rem;
    color: #64748B;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 2px;
}
.live-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,255,136,0.08);
    border: 1px solid rgba(0,255,136,0.25);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.72rem;
    color: #00FF88;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}
.live-dot {
    width: 6px; height: 6px;
    background: #00FF88;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,255,136,0.5); }
    50% { opacity: 0.6; box-shadow: 0 0 0 4px rgba(0,255,136,0); }
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(135deg, #0F1629 0%, #0D1425 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: rgba(0,212,255,0.25); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}
.kpi-card.cyan::before  { background: linear-gradient(90deg, #00D4FF, transparent); }
.kpi-card.green::before { background: linear-gradient(90deg, #00FF88, transparent); }
.kpi-card.amber::before { background: linear-gradient(90deg, #F59E0B, transparent); }
.kpi-card.purple::before{ background: linear-gradient(90deg, #A78BFA, transparent); }

.kpi-label {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    color: #64748B;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #F8FAFC;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.03em;
    line-height: 1;
}
.kpi-sub {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
}
.kpi-badge-up   { color: #00FF88; }
.kpi-badge-down { color: #F87171; }

/* ── Section headers ── */
.section-header {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 1.5rem 0 0.75rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.05);
}

/* ── Chart container ── */
.chart-card {
    background: #0F1629;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
}
.chart-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94A3B8;
    margin-bottom: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ── Table styling ── */
.styled-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.82rem;
}
.styled-table th {
    background: rgba(0,212,255,0.05);
    color: #64748B;
    font-weight: 500;
    letter-spacing: 0.08em;
    font-size: 0.68rem;
    text-transform: uppercase;
    padding: 10px 14px;
    text-align: right;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.styled-table th:first-child { text-align: left; }
.styled-table td {
    padding: 9px 14px;
    text-align: right;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    font-family: 'JetBrains Mono', monospace;
    color: #CBD5E1;
    vertical-align: middle;
}
.styled-table td:first-child {
    text-align: left;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    color: #E2E8F0;
}
.styled-table tr:hover td { background: rgba(0,212,255,0.03); }
.coin-icon {
    display: inline-flex; align-items: center; gap: 8px;
}
.coin-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.price-bar-wrap {
    display: flex; align-items: center; gap: 8px;
}
.price-bar-bg {
    flex: 1; height: 4px; background: rgba(255,255,255,0.06);
    border-radius: 2px; min-width: 60px;
}
.price-bar-fill {
    height: 4px; border-radius: 2px;
}

/* ── Metric overrides ── */
[data-testid="stMetric"] {
    background: transparent !important;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.4rem !important;
    color: #F8FAFC !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── Plotly chart background ── */
.js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}

/* ── Divider ── */
.thin-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin: 1.25rem 0;
}

/* ── Info tag ── */
.info-tag {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(100,116,139,0.12);
    border: 1px solid rgba(100,116,139,0.2);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.7rem;
    color: #64748B;
    font-family: 'JetBrains Mono', monospace;
}
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_data():
    fs = s3fs.S3FileSystem(
        client_kwargs={'endpoint_url': 'http://minio:9000'},
        key='admin',
        secret='password',
        use_ssl=False
    )
    bucket_path = "gold/market_data/coingecko_summary/"
    fichiers = fs.glob(f"{bucket_path}*.parquet")
    if not fichiers:
        return None
    dfs = []
    for f in fichiers:
        with fs.open(f, 'rb') as file:
            dfs.append(pq.read_table(file).to_pandas())
    df = pd.concat(dfs, ignore_index=True)
    if 'exact_time' in df.columns:
        df['exact_time'] = pd.to_datetime(df['exact_time'])
        df = df.sort_values('exact_time')
    return df


# ── Header ───────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S UTC")
st.markdown(f"""
<div class="dash-header">
  <div>
    <div class="dash-title">₿ Crypto <span>Market</span> Dashboard</div>
    <div class="dash-subtitle">MinIO · gold/market_data/coingecko_summary</div>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <div class="info-tag">🕐 {now_str}</div>
    <div class="live-badge"><div class="live-dot"></div>LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Load ──────────────────────────────────────────────────────────────────────
df = load_data()

if df is None:
    st.error("❌ Aucun fichier parquet trouvé dans MinIO.")
    st.stop()

# ── Compute KPIs ──────────────────────────────────────────────────────────────
latest = df.iloc[-1]
btc_price    = latest.get('bitcoin_price', 0)
btc_vol      = latest.get('bitcoin_vol', 0)
eth_price    = latest.get('ethereum_price', 0)
eth_vol      = latest.get('ethereum_vol', 0)
total_rows   = len(df)
n_files      = 2

# Price evolution (first vs last)
btc_first = df['bitcoin_price'].iloc[0] if 'bitcoin_price' in df.columns else btc_price
btc_pct   = ((btc_price - btc_first) / btc_first * 100) if btc_first else 0
eth_first = df['ethereum_price'].iloc[0] if 'ethereum_price' in df.columns else eth_price
eth_pct   = ((eth_price - eth_first) / eth_first * 100) if eth_first else 0

def fmt_price(v):
    return f"${v:,.2f}"

def fmt_vol(v):
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.2f}M"
    if v >= 1e3:  return f"${v/1e3:.2f}K"
    return f"${v:.2f}"

def pct_badge(pct):
    arrow = "▲" if pct >= 0 else "▼"
    cls   = "up" if pct >= 0 else "down"
    return f'<span class="kpi-badge-{cls}">{arrow} {abs(pct):.2f}%</span>'

# ── KPI Row ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Key metrics</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card cyan">
      <div class="kpi-label">Bitcoin Price</div>
      <div class="kpi-value">{fmt_price(btc_price)}</div>
      <div class="kpi-sub">{pct_badge(btc_pct)} vs first record</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card green">
      <div class="kpi-label">Ethereum Price</div>
      <div class="kpi-value">{fmt_price(eth_price)}</div>
      <div class="kpi-sub">{pct_badge(eth_pct)} vs first record</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card amber">
      <div class="kpi-label">BTC Volume 24h</div>
      <div class="kpi-value">{fmt_vol(btc_vol)}</div>
      <div class="kpi-sub"><span style="color:#64748b">latest snapshot</span></div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card purple">
      <div class="kpi-label">ETH Volume 24h</div>
      <div class="kpi-value">{fmt_vol(eth_vol)}</div>
      <div class="kpi-sub"><span style="color:#64748b">{total_rows} data points loaded</span></div>
    </div>""", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
if 'exact_time' in df.columns and len(df) > 1:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    st.markdown('<div class="section-header">Price history</div>', unsafe_allow_html=True)

    ch1, ch2 = st.columns(2)

    chart_cfg = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Space Grotesk', color='#64748B', size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=10, color='#475569'),
            linecolor='rgba(255,255,255,0.05)'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.04)',
            zeroline=False,
            tickfont=dict(size=10, color='#475569'),
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#0F1629',
            bordercolor='rgba(0,212,255,0.3)',
            font=dict(family='JetBrains Mono', size=11, color='#E2E8F0')
        ),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=10)
        )
    )

    with ch1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">₿ Bitcoin price (USD)</div>', unsafe_allow_html=True)
        fig_btc = go.Figure()
        fig_btc.add_trace(go.Scatter(
            x=df['exact_time'], y=df['bitcoin_price'],
            mode='lines',
            line=dict(color='#00D4FF', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,212,255,0.05)',
            name='BTC',
            hovertemplate='<b>%{y:$,.2f}</b><extra></extra>'
        ))
        fig_btc.update_layout(**chart_cfg, height=220)
        st.plotly_chart(fig_btc, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Ξ Ethereum price (USD)</div>', unsafe_allow_html=True)
        fig_eth = go.Figure()
        fig_eth.add_trace(go.Scatter(
            x=df['exact_time'], y=df['ethereum_price'],
            mode='lines',
            line=dict(color='#00FF88', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,255,136,0.05)',
            name='ETH',
            hovertemplate='<b>%{y:$,.2f}</b><extra></extra>'
        ))
        fig_eth.update_layout(**chart_cfg, height=220)
        st.plotly_chart(fig_eth, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Volume chart
    if 'bitcoin_vol' in df.columns and 'ethereum_vol' in df.columns:
        st.markdown('<div class="section-header">Volume comparison</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">24h Trading Volume</div>', unsafe_allow_html=True)
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=df['exact_time'], y=df['bitcoin_vol'],
            name='BTC Volume', marker_color='rgba(0,212,255,0.6)',
            hovertemplate='BTC: <b>%{y:$,.0f}</b><extra></extra>'
        ))
        fig_vol.add_trace(go.Bar(
            x=df['exact_time'], y=df['ethereum_vol'],
            name='ETH Volume', marker_color='rgba(0,255,136,0.6)',
            hovertemplate='ETH: <b>%{y:$,.0f}</b><extra></extra>'
        ))
        fig_vol.update_layout(
            **chart_cfg,
            height=200,
            barmode='group',
            bargap=0.2,
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

# ── Latest Snapshot Table ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">Latest snapshots</div>', unsafe_allow_html=True)

display_df = df.tail(10).copy()[::-1]

# Build max for progress bars
btc_max = df['bitcoin_price'].max() if 'bitcoin_price' in df.columns else 1
eth_max = df['ethereum_price'].max() if 'ethereum_price' in df.columns else 1

rows_html = ""
for _, row in display_df.iterrows():
    time_str  = str(row.get('exact_time', ''))[:19] if 'exact_time' in row else '—'
    btc_p     = row.get('bitcoin_price', 0)
    eth_p     = row.get('ethereum_price', 0)
    btc_v     = row.get('bitcoin_vol', 0)
    eth_v     = row.get('ethereum_vol', 0)
    btc_pct_w = min((btc_p / btc_max) * 100, 100)
    eth_pct_w = min((eth_p / eth_max) * 100, 100)

    rows_html += f"""
    <tr>
      <td><span style="font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#475569">{time_str}</span></td>
      <td>
        <div class="price-bar-wrap">
          <span style="color:#00D4FF">{fmt_price(btc_p)}</span>
          <div class="price-bar-bg"><div class="price-bar-fill" style="width:{btc_pct_w:.1f}%;background:#00D4FF;"></div></div>
        </div>
      </td>
      <td>
        <div class="price-bar-wrap">
          <span style="color:#00FF88">{fmt_price(eth_p)}</span>
          <div class="price-bar-bg"><div class="price-bar-fill" style="width:{eth_pct_w:.1f}%;background:#00FF88;"></div></div>
        </div>
      </td>
      <td style="color:#94A3B8">{fmt_vol(btc_v)}</td>
      <td style="color:#94A3B8">{fmt_vol(eth_v)}</td>
    </tr>"""

st.markdown(f"""
<div class="chart-card">
<table class="styled-table">
  <thead>
    <tr>
      <th>Timestamp</th>
      <th>BTC Price</th>
      <th>ETH Price</th>
      <th>BTC Volume</th>
      <th>ETH Volume</th>
    </tr>
  </thead>
  <tbody>{rows_html}</tbody>
</table>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:0.25rem 0;">
  <span class="info-tag">⚡ Cache TTL · 30s</span>
  <span class="info-tag">📦 {total_rows} rows · {n_files} parquet files</span>
  <span class="info-tag">🗄️ MinIO · gold layer</span>
</div>
""", unsafe_allow_html=True)