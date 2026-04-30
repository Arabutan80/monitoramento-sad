import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Monitoramento Solo & Ar", layout="wide", initial_sidebar_state="collapsed")

# CSS idêntico ao anterior (omitido por brevidade, manter o mesmo CSS da sua versão)
st.markdown("""<style>
    /* Cole aqui o mesmo CSS que você já está usando */
    .stApp, body, .main { background-color: #0f1a0e; color: #d4e0cc; }
    .kpi-card { background: #182015; border: 1px solid #2a3a25; border-radius: 14px; padding: 16px 18px; margin-bottom: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.35); }
    .temp-solo { border-left: 4px solid #e8784a; }
    .umid-solo { border-left: 4px solid #2ecc88; }
    .temp-ar   { border-left: 4px solid #4da6e8; }
    .umid-ar   { border-left: 4px solid #5b8def; }
    .flags     { border-left: 4px solid #f0c040; }
    .flag-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .flag-ok { background: #2ecc71; }
    .flag-warn { background: #e74c3c; }
</style>""", unsafe_allow_html=True)

st.title("🌱 Monitoramento Solo & Ar")

# URLs alternativas para tentar carregar
URLS = [
    "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv",
    "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/gviz/tq?tqx=out:csv&gid=0",
]

@st.cache_data(ttl=60)
def carregar_dados():
    for i, url in enumerate(URLS):
        try:
            df_raw = pd.read_csv(url, sep=';', header=None, dtype=str)
            if df_raw.empty:
                continue
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
                df["datetime"] = pd.to_datetime(df["data"] + " " + df["hora"], dayfirst=True, errors="coerce")
                df = df.dropna(subset=["datetime"]).sort_values("datetime")
                return df
        except Exception as e:
            st.warning(f"URL {i+1} falhou: {e}")
            continue
    return None

df = carregar_dados()

if df is None or df.empty:
    st.error("❌ **Não foi possível carregar os dados da planilha.**")
    st.info("""
    **Possíveis causas:**
    - A planilha não está mais publicada na Web.
    - O link CSV expirou ou foi alterado.
    - O Streamlit Cloud está temporariamente bloqueado.

    **Soluções:**
    - Publique novamente a planilha (Arquivo → Compartilhar → Publicar na web → CSV).
    - Copie o novo link e substitua na variável `URLS` no código.
    - Ou faça upload manual do CSV baixado.
    """)
    uploaded_file = st.file_uploader("📂 Ou faça upload do arquivo CSV baixado da planilha", type=['csv'])
    if uploaded_file is not None:
        # Lê o arquivo upado e processa igual
        df_raw = pd.read_csv(uploaded_file, sep=';', header=None, dtype=str)
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
            df["datetime"] = pd.to_datetime(df["data"] + " " + df["hora"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["datetime"]).sort_values("datetime")
    else:
        st.stop()

# Restante do código (KPIs, gráficos, tabela) continua igual ao que você já tem, a partir do df carregado
# Mas agora com a certeza de que df não é None nem vazio
ultimo = df.iloc[-1]
# ... (resto do seu código de KPIs, gráficos etc., que já está funcionando quando df tem dados)
