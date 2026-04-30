import streamlit as st
import pandas as pd

URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

st.set_page_config(page_title="🌱 SAD Macaúbas | Monitoramento Agroenergia", layout="wide")

# =========================
# CSS TEMA CLARO + CARDS CENTRALIZADOS + TABELA ESQUERDA
# =========================
st.markdown("""
<style>
    .stApp, body, .main {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    .kpi-card {
        background: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        height: 100%;
        text-align: center;
    }
    .kpi-card .label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #666666;
        margin-bottom: 8px;
    }
    .kpi-card .valor-linha {
        font-size: 1.5rem;
        font-weight: 700;
        color: #222222;
        margin-bottom: 4px;
    }
    .kpi-card .unidade {
        font-size: 0.85rem;
        color: #666666;
    }
    .temp-solo { border-left: 4px solid #e74c3c; }
    .umid-solo { border-left: 4px solid #3498db; }
    .temp-ar   { border-left: 4px solid #e67e22; }
    .umid-ar   { border-left: 4px solid #2ecc71; }
    .flags     { border-left: 4px solid #f1c40f; }
    .flag-dot {
        width: 11px; height: 11px; border-radius: 50%;
        display: inline-block; margin-right: 5px;
    }
    .flag-ok { background: #27ae60; }
    .flag-warn { background: #e74c3c; }
    h1, h2, h3 { color: #222222 !important; }
    div[data-testid="stDataFrame"] table td,
    div[data-testid="stDataFrame"] table th {
        text-align: left !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌱 Sistema de Monitoramento SAD")

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(URL, sep=",")
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    df.columns = [
        "data", "dia_semana", "hora",
        "solo30", "solo60", "solo90",
        "raw30", "raw60", "raw90",
        "temp_ar", "umid_ar",
        "status1", "status2"
    ]

    col_numericas = [
        "solo30", "solo60", "solo90",
        "raw30", "raw60", "raw90",
        "temp_ar", "umid_ar",
        "status1", "status2"
    ]
    for col in col_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["datetime"] = pd.to_datetime(
        df["data"] + " " + df["hora"],
        dayfirst=True,
        errors="coerce"
    )
    df = df.dropna(subset=["datetime"])
    return df

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado disponível.")
    st.stop()

ultimo = df.iloc[-1]
st.markdown(f"📡 Fonte: Google Sheets | Registros: {len(df)} | Última leitura: {ultimo['data']} {ultimo['hora']}")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card temp-solo">
        <div class="label">Temp. Solo (30/60/90 cm)</div>
        <div class="valor-linha">{ultimo['solo30']:.1f}°C <span style="font-size:0.8rem;color:#666;">30 cm</span></div>
        <div class="valor-linha">{ultimo['solo60']:.1f}°C <span style="font-size:0.8rem;color:#666;">60 cm</span></div>
        <div class="valor-linha">{ultimo['solo90']:.1f}°C <span style="font-size:0.8rem;color:#666;">90 cm</span></div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card umid-solo">
        <div class="label">Umidade Solo (30/60/90 cm)</div>
        <div class="valor-linha">{ultimo['raw30']} <span style="font-size:0.8rem;color:#666;">(raw) 30 cm</span></div>
        <div class="valor-linha">{ultimo['raw60']} <span style="font-size:0.8rem;color:#666;">(raw) 60 cm</span></div>
        <div class="valor-linha">{ultimo['raw90']} <span style="font-size:0.8rem;color:#666;">(raw) 90 cm</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card temp-ar">
        <div class="label">Temperatura do Ar</div>
        <div class="valor-linha">{ultimo['temp_ar']:.2f}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card umid-ar">
        <div class="label">Umidade do Ar</div>
        <div class="valor-linha">{ultimo['umid_ar']:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    f1 = "flag-ok" if ultimo["status1"] == 1 else "flag-warn"
    f2 = "flag-ok" if ultimo["status2"] == 1 else "flag-warn"
    st.markdown(f"""
    <div class="kpi-card flags">
        <div class="label">Dispositivos</div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:6px; margin-top:8px;">
            <div><span class="flag-dot {f1}"></span> Cartão Micro SD</div>
            <div><span class="flag-dot {f2}"></span> Relógio RTC</div>
        </div>
        <div style="font-size:0.7rem;color:#666;margin-top:8px;">🕐 {ultimo['hora']} · {ultimo['data']}</div>
    </div>
    """, unsafe_allow_html=True)

# Gráficos
st.subheader("🌡️ Temperatura do Solo — 30 cm, 60 cm e 90 cm")
st.line_chart(
    data=df.set_index("datetime")[["solo30", "solo60", "solo90"]],
    color=["#e74c3c", "#3498db", "#e67e22"],   # vermelho, azul, laranja
    height=350
)

st.subheader("💧 Umidade do Solo — 30 cm, 60 cm e 90 cm")
st.line_chart(
    data=df.set_index("datetime")[["raw30", "raw60", "raw90"]],
    color=["#e74c3c", "#3498db", "#e67e22"],   # mesmas cores
    height=350
)

colA, colB = st.columns(2)
with colA:
    st.subheader("🌬️ Temperatura do Ar")
    st.line_chart(data=df.set_index("datetime")["temp_ar"], color="#e74c3c", height=300)
with colB:
    st.subheader("💨 Umidade do Ar (%)")
    st.line_chart(data=df.set_index("datetime")["umid_ar"], color="#3498db", height=300)

st.subheader("📋 Últimos Registros")
st.dataframe(
    df[["data", "hora", "solo30", "solo60", "solo90", "raw30", "raw60", "raw90", "temp_ar", "umid_ar", "status1", "status2"]].tail(20),
    use_container_width=True
)
