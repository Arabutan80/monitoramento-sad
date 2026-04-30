import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("Sistema de Monitoramento SAD")

# LINK CSV (já corrigido)
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

@st.cache_data
def carregar_dados():
    try:
        df_raw = pd.read_csv(URL, sep=';', header=None, engine='python')
    except:
        st.error("Erro ao ler o CSV. Verifique se a planilha está pública.")
        return pd.DataFrame()

    registros = []
    bloco = []

    for _, row in df_raw.iterrows():
        valor = str(row[0]).strip()

        if valor == "" or valor.lower() == "nan":
            continue

        bloco.append(valor)

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

    if len(registros) == 0:
        st.error("Nenhum dado válido encontrado na planilha.")
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    df["datetime"] = pd.to_datetime(
        df["data"] + " " + df["hora"],
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(subset=["datetime"])

    return df

df = carregar_dados()

if df.empty:
    st.stop()

# ===== KPIs =====
st.subheader("Indicadores atuais")

col1, col2, col3 = st.columns(3)

col1.metric("Temp Ar (°C)", f"{df['temp_ar'].iloc[-1]:.2f}")
col2.metric("Umidade Ar (%)", f"{df['umid_ar'].iloc[-1]:.2f}")
col3.metric("Solo Médio (°C)", f"{df[['solo10','solo20','solo30']].mean(axis=1).iloc[-1]:.2f}")

# ===== GRÁFICO SOLO =====
st.subheader("Temperatura do Solo")

st.line_chart(df.set_index("datetime")[["solo10","solo20","solo30"]])

# ===== AMBIENTE =====
col1, col2 = st.columns(2)

with col1:
    st.subheader("Temperatura do Ar")
    st.line_chart(df.set_index("datetime")["temp_ar"])

with col2:
    st.subheader("Umidade do Ar")
    st.line_chart(df.set_index("datetime")["umid_ar"])

# ===== TABELA =====
st.subheader("Últimas Leituras")
st.dataframe(df.tail(10))
