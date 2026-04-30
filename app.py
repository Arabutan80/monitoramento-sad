import streamlit as st
import pandas as pd

# URL do CSV publicado no Google Sheets
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

# =========================
# FUNÇÃO DE CARREGAMENTO
# =========================
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv(URL, sep=",")
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

    # Remover espaços extras (muito importante no seu caso)
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

# Evita quebra do sistema
if df.empty:
    st.warning("Nenhum dado disponível.")
    st.stop()

# =========================
# INTERFACE
# =========================

st.set_page_config(page_title="Monitoramento SAD", layout="wide")

st.title("Sistema de Monitoramento SAD")

# KPIs (último valor)
ultimo = df.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric("Temp. Ar (°C)", f"{ultimo['temp_ar']:.2f}")
col2.metric("Umidade (%)", f"{ultimo['umid_ar']:.2f}")
col3.metric("Solo 10cm", f"{ultimo['solo10']:.2f}")

# =========================
# GRÁFICOS
# =========================

st.subheader("Umidade do Solo")
st.line_chart(df.set_index("datetime")[["solo10", "solo20", "solo30"]])

st.subheader("Temperatura do Ar")
st.line_chart(df.set_index("datetime")[["temp_ar"]])

st.subheader("Umidade do Ar")
st.line_chart(df.set_index("datetime")[["umid_ar"]])

# =========================
# TABELA FINAL
# =========================

st.subheader("Últimos Registros")
st.dataframe(df.tail(20))
