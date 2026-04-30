import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Monitoramento Solo & Ar", layout="wide", initial_sidebar_state="collapsed")

# ── CSS TEMA ESCURO ─────────────────────────────────────
st.markdown("""
<style>
    .stApp, body, .main { background-color: #0f1a0e; color: #d4e0cc; }
    .kpi-card {
        background: #182015; border: 1px solid #2a3a25; border-radius: 14px;
        padding: 16px 18px; margin-bottom: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.35);
    }
    .temp-solo { border-left: 4px solid #e8784a; }
    .umid-solo { border-left: 4px solid #2ecc88; }
    .temp-ar   { border-left: 4px solid #4da6e8; }
    .umid-ar   { border-left: 4px solid #5b8def; }
    .flags     { border-left: 4px solid #f0c040; }
    .flag-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .flag-ok { background: #2ecc71; }
    .flag-warn { background: #e74c3c; }
    .label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.6px; color: #8a9a80; }
    .value { font-size: 1.75rem; font-weight: 700; color: #f0f4e8; }
    .unit { font-size: 0.78rem; color: #8a9a80; }
    .sub { font-size: 0.7rem; color: #8a9a80; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

st.title("🌱 Monitoramento Solo & Ar")

# ── FUNÇÃO DE CARREGAMENTO ──────────────────────────────
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def processar_csv(csv_texto):
    """Converte o texto CSV em DataFrame padronizado."""
    df_raw = pd.read_csv(StringIO(csv_texto), sep=';', header=None, dtype=str)
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
    if not df.empty:
        df["datetime"] = pd.to_datetime(
            df["data"] + " " + df["hora"],
            dayfirst=True,
            errors="coerce"
        )
        df = df.dropna(subset=["datetime"]).sort_values("datetime")
    return df

# ── TENTAR CARREGAR VIA REQUISIÇÃO ─────────────────────
dados_exemplo = """06/04/2026;1;18:15:00;27.44;27.44;27.44;58;27;42;27.62;89.25;1;1
06/04/2026;1;18:30:00;27.44;27.44;27.44;58;27;42;27.37;91.32;1;1
06/04/2026;1;18:45:00;27.50;27.44;27.44;58;27;42;27.07;92.74;1;1"""

df = None
mensagem = ""

try:
    resposta = requests.get(URL, headers=HEADERS, timeout=10)
    if resposta.status_code == 200 and len(resposta.text) > 50:
        df = processar_csv(resposta.text)
        if not df.empty:
            mensagem = "✅ Dados carregados automaticamente do Google Sheets."
except Exception as e:
    pass

# ── SE FALHAR, OFERECER UPLOAD MANUAL ─────────────────
if df is None or df.empty:
    st.warning("⚠️ Não foi possível carregar automaticamente. Você pode baixar o CSV manualmente e fazer upload aqui.")
    arquivo = st.file_uploader("📂 Selecione o arquivo CSV da planilha", type="csv")
    if arquivo is not None:
        try:
            texto = arquivo.getvalue().decode("utf-8")
            df = processar_csv(texto)
            if not df.empty:
                mensagem = "✅ Dados carregados via upload manual."
        except:
            st.error("Erro ao processar o arquivo enviado.")
    else:
        # Fallback final com dados de exemplo, apenas para a visualização não quebrar
        st.info("🔹 Enquanto isso, veja o exemplo visual com dados de demonstração.")
        df = processar_csv(dados_exemplo)
        mensagem = "ℹ️ Exibindo dados de exemplo (não reais)."

# ── EXIBIR OS DADOS (agora df com certeza existe) ─────
if df is None or df.empty:
    st.error("Nenhum dado disponível. Verifique o arquivo CSV ou a planilha publicada.")
    st.stop()

ultimo = df.iloc[-1]
media_solo = (ultimo["solo10"] + ultimo["solo20"] + ultimo["solo30"]) / 3
media_umid = (ultimo["raw10"] + ultimo["raw20"] + ultimo["raw30"]) / 3

st.markdown(f"📡 {mensagem} | Registros: {len(df)} | Última leitura: {ultimo['data']} {ultimo['hora']}")

# ── CARDS ──────────────────────────────────────────────
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

# ── GRÁFICOS ──────────────────────────────────────────
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
    st.line_chart(df.set_index("datetime")["temp_ar"], color="#4da6e8", height=300)
with colB:
    st.subheader("💨 Umidade do Ar (%)")
    st.line_chart(df.set_index("datetime")["umid_ar"], color="#5b8def", height=300)

# ── TABELA ────────────────────────────────────────────
st.subheader("Últimas 10 leituras")
st.dataframe(df[["data", "hora", "temp_ar", "umid_ar", "solo10", "solo20", "solo30", "status1", "status2"]].tail(10),
             use_container_width=True)
