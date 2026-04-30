import streamlit as st
import pandas as pd

# URL do CSV publicado no Google Sheets (mantido igual)
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(page_title="Monitoramento SAD", layout="wide")

# =========================
# CSS TEMA ESCURO + CARDS
# =========================
st.markdown("""
<style>
    .stApp, body, .main {
        background-color: #0f1a0e;
        color: #d4e0cc;
    }
    .kpi-card {
        background: #182015;
        border: 1px solid #2a3a25;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.35);
        height: 100%;
    }
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
        width: 11px; height: 11px; border-radius: 50%;
        display: inline-block; margin-right: 5px;
    }
    .flag-ok { background: #2ecc71; }
    .flag-warn { background: #e74c3c; }
    h1, h2, h3 { color: #e8f0e0 !important; }
    .stDataFrame { background: #182015; border: 1px solid #2a3a25; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🌱 Sistema de Monitoramento SAD")

# =========================
# FUNÇÃO DE CARREGAMENTO (mantida igual)
# =========================
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(URL, sep=",")
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

    # Remover espaços extras
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # Nomear colunas corretamente
    df.columns = [
        "data",
        "dia_semana",
        "hora",
        "solo10",
        "solo20",
        "solo30",
        "raw10",
        "raw20",
        "raw30",
        "temp_ar",
        "umid_ar",
        "status1",
        "status2"
    ]

    # Conversões numéricas seguras
    col_numericas = [
        "solo10", "solo20", "solo30",
        "raw10", "raw20", "raw30",
        "temp_ar", "umid_ar",
        "status1", "status2"
    ]

    for col in col_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Criar coluna datetime
    df["datetime"] = pd.to_datetime(
        df["data"] + " " + df["hora"],
        dayfirst=True,
        errors="coerce"
    )

    # Remover linhas inválidas
    df = df.dropna(subset=["datetime"])

    return df


# =========================
# EXECUÇÃO PRINCIPAL
# =========================
df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado disponível.")
    st.stop()

# =========================
# KPI CARDS (último registro)
# =========================
ultimo = df.iloc[-1]
media_solo = (ultimo["solo10"] + ultimo["solo20"] + ultimo["solo30"]) / 3
media_umid = (ultimo["raw10"] + ultimo["raw20"] + ultimo["raw30"]) / 3

st.markdown(f"📡 Fonte: Google Sheets | Registros: {len(df)} | Última leitura: {ultimo['data']} {ultimo['hora']}")

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
        <div class="label">Umidade Solo (raw)</div>
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
    f1 = "flag-ok" if ultimo["status1"] == 1 else "flag-warn"
    f2 = "flag-ok" if ultimo["status2"] == 1 else "flag-warn"
    st.markdown(f"""
    <div class="kpi-card flags">
        <div class="label">Flags</div>
        <div style="display:flex; gap:16px; margin-top:8px;">
            <div><span class="flag-dot {f1}"></span> Flag 1: {ultimo['status1']}</div>
            <div><span class="flag-dot {f2}"></span> Flag 2: {ultimo['status2']}</div>
        </div>
        <div class="sub">🕐 {ultimo['hora']} · {ultimo['data']}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# GRÁFICOS MELHORADOS
# =========================

st.subheader("🌡️ Temperatura do Solo — 3 Sensores")
st.line_chart(
    df.set_index("datetime")[["solo10", "solo20", "solo30"]],
    color=["#e8784a", "#d4956b", "#f0b090"],
    height=350
)

st.subheader("💧 Umidade do Solo (raw) — 3 Sensores")
st.line_chart(
    df.set_index("datetime")[["raw10", "raw20", "raw30"]],
    color=["#2ecc88", "#45d9a0", "#70e8bb"],
    height=350
)

colA, colB = st.columns(2)
with colA:
    st.subheader("🌬️ Temperatura do Ar")
    st.line_chart(
        df.set_index("datetime")["temp_ar"],
        color="#4da6e8",
        height=300
    )
with colB:
    st.subheader("💨 Umidade do Ar (%)")
    st.line_chart(
        df.set_index("datetime")["umid_ar"],
        color="#5b8def",
        height=300
    )

# =========================
# TABELA FINAL
# =========================
st.subheader("📋 Últimos Registros")
st.dataframe(
    df[["data", "hora", "solo10", "solo20", "solo30", "raw10", "raw20", "raw30", "temp_ar", "umid_ar", "status1", "status2"]].tail(20),
    use_container_width=True
)
