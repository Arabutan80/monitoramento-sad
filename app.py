import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── CONFIGURAÇÃO DA PÁGINA ──────────────────────────────
st.set_page_config(
    page_title="Monitoramento Solo & Ar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS PERSONALIZADO (tema dark terra) ─────────────────
st.markdown("""
<style>
    /* Fundo geral */
    .stApp, body, .main {
        background-color: #0f1a0e;
        color: #d4e0cc;
    }
    /* Painéis do Streamlit */
    .css-1d391kg, .css-1r6slb0 {
        background-color: #182015 !important;
        border: 1px solid #2a3a25 !important;
        border-radius: 14px;
        padding: 16px;
    }
    /* Títulos */
    h1, h2, h3, h4 {
        color: #e8f0e0 !important;
    }
    /* Métricas */
    .stMetric {
        background-color: #182015;
        border: 1px solid #2a3a25;
        border-radius: 14px;
        padding: 12px;
    }
    /* Cards com borda colorida */
    .kpi-card {
        background: #182015;
        border: 1px solid #2a3a25;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.35);
        transition: transform 0.15s;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    .kpi-card .label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #8a9a80;
        margin-bottom: 4px;
    }
    .kpi-card .value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f0f4e8;
    }
    .kpi-card .unit {
        font-size: 0.78rem;
        color: #8a9a80;
    }
    .kpi-card .sub {
        font-size: 0.7rem;
        color: #8a9a80;
        margin-top: 2px;
    }
    .temp-solo { border-left: 4px solid #e8784a; }
    .umid-solo { border-left: 4px solid #2ecc88; }
    .temp-ar   { border-left: 4px solid #4da6e8; }
    .umid-ar   { border-left: 4px solid #5b8def; }
    .flags     { border-left: 4px solid #f0c040; }
    .flag-dot {
        width: 11px; height: 11px; border-radius: 50%; display: inline-block; margin-right: 5px;
    }
    .flag-ok { background: #2ecc71; }
    .flag-warn { background: #e74c3c; }
    /* Gráficos */
    .js-plotly-plot, .plotly {
        background: #182015 !important;
        border-radius: 14px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌱 Monitoramento Solo & Ar")

# ── CARREGAMENTO DOS DADOS ──────────────────────────────
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    # Lê o CSV separado por ponto-e-vírgula
    df_raw = pd.read_csv(URL, sep=';', header=None, dtype=str)

    registros = []
    bloco = []
    for _, row in df_raw.iterrows():
        valor = row[0]
        if pd.isna(valor):
            continue
        bloco.append(str(valor).strip())
        if len(bloco) == 13:
            try:
                registros.append({
                    "data": bloco[0],
                    "dia_semana": int(bloco[1]),
                    "hora": bloco[2],
                    "solo10": float(bloco[3]),
                    "solo20": float(bloco[4]),
                    "solo30": float(bloco[5]),
                    "raw10": int(bloco[6]),
                    "raw20": int(bloco[7]),
                    "raw30": int(bloco[8]),
                    "temp_ar": float(bloco[9]),
                    "umid_ar": float(bloco[10]),
                    "status1": int(bloco[11]),
                    "status2": int(bloco[12]),
                })
            except:
                pass
            bloco = []

    df = pd.DataFrame(registros)
    df["datetime"] = pd.to_datetime(
        df["data"] + " " + df["hora"],
        dayfirst=True,
        errors="coerce"
    )
    df = df.dropna(subset=["datetime"]).sort_values("datetime")
    return df

df = carregar_dados()

# ── KPI CARDS (último registro) ─────────────────────────
ultimo = df.iloc[-1]
media_solo = (ultimo["solo10"] + ultimo["solo20"] + ultimo["solo30"]) / 3
media_umid = (ultimo["raw10"] + ultimo["raw20"] + ultimo["raw30"]) / 3

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card temp-solo">
        <div class="label">Temp. Solo (média)</div>
        <div class="value">{media_solo:.2f}<span class="unit">°C</span></div>
        <div class="sub">S1:{ultimo['solo10']:.1f} S2:{ultimo['solo20']:.1f} S3:{ultimo['solo30']:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card umid-solo">
        <div class="label">Umidade Solo (média raw)</div>
        <div class="value">{media_umid:.1f}</div>
        <div class="sub">S1:{ultimo['raw10']} S2:{ultimo['raw20']} S3:{ultimo['raw30']}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card temp-ar">
        <div class="label">Temperatura do Ar</div>
        <div class="value">{ultimo['temp_ar']:.2f}<span class="unit">°C</span></div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card umid-ar">
        <div class="label">Umidade do Ar</div>
        <div class="value">{ultimo['umid_ar']:.1f}<span class="unit">%</span></div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    flag1_class = "flag-ok" if ultimo["status1"] == 1 else "flag-warn"
    flag2_class = "flag-ok" if ultimo["status2"] == 1 else "flag-warn"
    st.markdown(f"""
    <div class="kpi-card flags">
        <div class="label">Flags</div>
        <div style="display:flex; gap:16px; margin-top:8px;">
            <div><span class="flag-dot {flag1_class}"></span> Flag 1: {ultimo['status1']}</div>
            <div><span class="flag-dot {flag2_class}"></span> Flag 2: {ultimo['status2']}</div>
        </div>
        <div class="sub">🕐 {ultimo['hora']} · {ultimo['data']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"📡 Fonte: Google Sheets | Registros: {len(df)} | Última leitura: {ultimo['data']} {ultimo['hora']}")

# ── GRÁFICO 1: TEMPERATURA DO SOLO (3 sensores) ─────────
st.subheader("🌡️ Temperatura do Solo — 3 Sensores")
fig_solo = go.Figure()
fig_solo.add_trace(go.Scatter(
    x=df["datetime"], y=df["solo10"], mode="lines",
    name="Sensor 1", line=dict(color="#e8784a", width=2.5)
))
fig_solo.add_trace(go.Scatter(
    x=df["datetime"], y=df["solo20"], mode="lines",
    name="Sensor 2", line=dict(color="#d4956b", width=2.5, dash="dash")
))
fig_solo.add_trace(go.Scatter(
    x=df["datetime"], y=df["solo30"], mode="lines",
    name="Sensor 3", line=dict(color="#f0b090", width=2.5, dash="dot")
))
fig_solo.update_layout(
    template="plotly_dark",
    paper_bgcolor="#182015",
    plot_bgcolor="#182015",
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
    yaxis=dict(title="Temperatura (°C)", gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
    legend=dict(font=dict(color="#c8d8b8")),
    hovermode="x unified",
    height=350
)
st.plotly_chart(fig_solo, use_container_width=True)

# ── GRÁFICO 2: UMIDADE DO SOLO (raw) ────────────────────
st.subheader("💧 Umidade do Solo (raw) — 3 Sensores")
fig_umid = go.Figure()
fig_umid.add_trace(go.Scatter(
    x=df["datetime"], y=df["raw10"], mode="lines",
    name="Sensor 1 (raw)", line=dict(color="#2ecc88", width=2.5)
))
fig_umid.add_trace(go.Scatter(
    x=df["datetime"], y=df["raw20"], mode="lines",
    name="Sensor 2 (raw)", line=dict(color="#45d9a0", width=2.5, dash="dash")
))
fig_umid.add_trace(go.Scatter(
    x=df["datetime"], y=df["raw30"], mode="lines",
    name="Sensor 3 (raw)", line=dict(color="#70e8bb", width=2.5, dash="dot")
))
fig_umid.update_layout(
    template="plotly_dark",
    paper_bgcolor="#182015",
    plot_bgcolor="#182015",
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
    yaxis=dict(title="Umidade (raw)", gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
    legend=dict(font=dict(color="#c8d8b8")),
    hovermode="x unified",
    height=350
)
st.plotly_chart(fig_umid, use_container_width=True)

# ── GRÁFICOS DO AR (lado a lado) ────────────────────────
colA, colB = st.columns(2)

with colA:
    st.subheader("🌬️ Temperatura do Ar")
    fig_ar_temp = go.Figure()
    fig_ar_temp.add_trace(go.Scatter(
        x=df["datetime"], y=df["temp_ar"], mode="lines",
        name="Temp. Ar", line=dict(color="#4da6e8", width=2.8),
        fill="tozeroy", fillcolor="rgba(77,166,232,0.15)"
    ))
    fig_ar_temp.update_layout(
        template="plotly_dark",
        paper_bgcolor="#182015",
        plot_bgcolor="#182015",
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
        yaxis=dict(title="°C", gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
        showlegend=False,
        height=300
    )
    st.plotly_chart(fig_ar_temp, use_container_width=True)

with colB:
    st.subheader("💨 Umidade do Ar (%)")
    fig_ar_umid = go.Figure()
    fig_ar_umid.add_trace(go.Scatter(
        x=df["datetime"], y=df["umid_ar"], mode="lines",
        name="Umidade Ar", line=dict(color="#5b8def", width=2.8),
        fill="tozeroy", fillcolor="rgba(91,141,239,0.15)"
    ))
    fig_ar_umid.update_layout(
        template="plotly_dark",
        paper_bgcolor="#182015",
        plot_bgcolor="#182015",
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
        yaxis=dict(title="%", gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#8a9a80")),
        showlegend=False,
        height=300
    )
    st.plotly_chart(fig_ar_umid, use_container_width=True)

# ── TABELA ──────────────────────────────────────────────
st.subheader("Últimas 10 leituras")
st.dataframe(
    df[["data", "hora", "temp_ar", "umid_ar", "solo10", "solo20", "solo30", "status1", "status2"]].tail(10),
    use_container_width=True
)
