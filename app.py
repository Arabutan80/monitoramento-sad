import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("Sistema de Monitoramento SAD")

# LINK CSV (já corrigido)
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(URL, sep=",")
    except:
        st.error("Erro ao ler a planilha.")
        return pd.DataFrame()

    # limpar espaços
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

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

    df["solo30"] = pd.to_numeric(df["solo30"], errors="coerce")
    df["solo60"] = pd.to_numeric(df["solo60"], errors="coerce")
    df["solo90"] = pd.to_numeric(df["solo90"], errors="coerce")
    df["temp_ar"] = pd.to_numeric(df["temp_ar"], errors="coerce")
    df["umid_ar"] = pd.to_numeric(df["umid_ar"], errors="coerce")

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
col3.metric("Solo Médio (°C)", f"{df[['solo30','solo60','solo90']].mean(axis=1).iloc[-1]:.2f}")

# ===== GRÁFICO SOLO =====
st.subheader("Temperatura do Solo")

st.line_chart(df.set_index("datetime")[["solo30","solo60","solo90"]])

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
