# =============================================================================================
# PROJETO: SAD MACAÚBAS — Painel de Monitoramento Agrometeorológico (Streamlit)
# =============================================================================================
# AUTOR: Arabutan Marques Neres
# PROGRAMA: Mestrado em Agroenergia Digital — PPGAD
# INSTITUIÇÃO: Universidade Federal do Tocantins — UFT
# DATA: Dezembro/2025
# =============================================================================================
#
# ARQUITETURA DO PAINEL
# ---------------------
# Camada de apresentação web do sistema agrometeorológico, hospedada em Streamlit Cloud,
# consumindo a base histórica gravada pelo RX no Google Sheets. O painel é renderizado em
# tempo quase real (atualização automática a cada 5 minutos) e expõe simultaneamente:
#   1. Cinco cartões de KPI com a leitura mais recente (temperaturas de solo, umidades de
#      solo, temperatura e umidade do ar, e flags de hardware do TX).
#   2. Séries temporais das variáveis do solo (temperatura e umidade nas três profundidades).
#   3. Séries temporais das variáveis do ar (temperatura e umidade relativa).
#   4. Tabela rolável com os 20 registros mais recentes para inspeção tabular.
#
# CICLO DE ATUALIZAÇÃO
# --------------------
# O TX coleta dados a cada 15 minutos. O painel atualiza a cada 300 segundos via três camadas
# combinadas: (a) tag HTML <meta http-equiv="refresh"> injetada na página instrui o próprio
# navegador a recarregar integralmente a interface, sem dependência de biblioteca externa;
# (b) cache_data com TTL de 300 s invalida a leitura cacheada da planilha em cada reexecução;
# (c) parâmetro cachebust adicionado à URL contorna o cache de borda (CDN) do próprio Google
# Sheets, garantindo que o CSV recebido seja sempre o mais recente publicado pelo doPost do
# Apps Script.
# =============================================================================================

import streamlit as st
import pandas as pd
import time

# URL de exportação do Google Sheets em formato CSV. O endpoint /export?format=csv produz
# uma representação imediata e cacheável da planilha completa, eliminando a necessidade de
# autenticação OAuth e simplificando a arquitetura para um painel público de leitura.
URL = "https://docs.google.com/spreadsheets/d/1yO4wEkz_3ABCNQk5peVeFEvUJTAmc7ZFaV79tfpgw8g/export?format=csv"

# Configuração global da página Streamlit: define o título da aba do navegador (utilizado
# também em compartilhamentos sociais) e o layout em largura total (wide), maximizando a
# área útil para a renderização simultânea dos cinco KPIs e dos gráficos de série temporal.
st.set_page_config(page_title="🌱 SAD Macaúbas | Monitoramento Agroenergia", layout="wide")

# =============================================================================================
# TEMA VISUAL — CSS injetado para padronizar a identidade visual do painel agronômico,
# sobrescrevendo o tema padrão do Streamlit por uma paleta clara de alto contraste. Os cartões
# de KPI utilizam borda lateral colorida como código semântico das variáveis: vermelho para
# temperatura, azul para umidade, laranja para variáveis do ar e amarelo para flags de
# hardware. Box-shadow sutil e borda arredondada conferem hierarquia visual entre os cartões
# e o fundo branco da aplicação.
# =============================================================================================
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

st.title("🌱 AGROENERGIA UFT - Monitoramento Macaúbas")

# Atualização automática da página via tag HTML meta refresh: instrui o navegador do cliente
# a recarregar integralmente a página a cada 5 minutos, disparando uma nova execução do
# script Python no servidor Streamlit Cloud. A abordagem nativa do HTML elimina a dependência
# da biblioteca streamlit-autorefresh — reduzindo o requirements.txt e o tempo de cold start
# do container — preservando o efeito funcional desejado: latência máxima de 5 minutos entre
# a publicação do dado na nuvem e sua visualização no painel, adequada ao ciclo de coleta de
# 15 minutos do TX.
st.markdown(
    '<meta http-equiv="refresh" content="300">',
    unsafe_allow_html=True
)                                                                       

# =============================================================================================
# carregar_dados — Realiza a aquisição e o tratamento do CSV exportado pelo Google Sheets,
# devolvendo um DataFrame Pandas pronto para consumo pelas camadas de visualização. A função
# é decorada com @st.cache_data(ttl=300), o que serializa o DataFrame em memória por 300 s e
# evita requisições redundantes ao Google a cada interação do usuário (clique em botão, hover
# em gráfico) — economizando largura de banda e respeitando os limites de quota da API. O
# parâmetro cachebust adicionado à URL é a contramedida ao cache de borda (CDN) do Google,
# que mantém versões intermediárias do CSV por alguns minutos e impede a propagação imediata
# de novos pacotes gravados pelo doPost. A combinação TTL local + cachebust remoto garante
# atualização ponta a ponta dentro do intervalo de 5 minutos.
# =============================================================================================
@st.cache_data(ttl=300)
def carregar_dados():

    # Construção da URL com parâmetro cachebust dinâmico (timestamp Unix em segundos): força
    # o Google a entregar a versão atualizada do CSV, contornando caches intermediários que
    # poderiam servir cópias defasadas em até 5 minutos.
    url_com_cachebust = f"{URL}&cachebust={int(time.time())}"

    try:
        df = pd.read_csv(url_com_cachebust, sep=",")
    except Exception as e:

        # Captura genérica de exceções da camada HTTP (timeout, erro de DNS, planilha sem
        # permissão pública) ou de parsing do CSV. O erro é exibido ao usuário e a função
        # retorna um DataFrame vazio para que a camada superior trate graciosamente a falha.
        st.error(f"Erro ao ler a planilha: {e}")
        return pd.DataFrame()

    # Higienização de espaços em branco: o firmware do TX usa "; " como separador, gerando
    # campos com espaço à esquerda. O strip() em toda coluna como string remove esses
    # caracteres antes da conversão numérica, prevenindo falhas de parsing.
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # Rotulação semântica das colunas conforme o protocolo do pacote CSV definido pelo TX:
    # 13 campos no total (data, dia da semana, hora, três temperaturas de solo, três umidades
    # brutas de solo, temperatura e umidade do ar, e dois flags de hardware).
    df.columns = [
        "data", "dia_semana", "hora",
        "solo30", "solo60", "solo90",
        "raw30", "raw60", "raw90",
        "temp_ar", "umid_ar",
        "status1", "status2"
    ]

    # Conversão para tipos numéricos das colunas que serão utilizadas em cálculos e gráficos.
    # O errors="coerce" transforma valores não conversíveis em NaN, permitindo identificar
    # pacotes corrompidos sem interromper o processamento do DataFrame inteiro.
    col_numericas = [
        "solo30", "solo60", "solo90",
        "raw30", "raw60", "raw90",
        "temp_ar", "umid_ar",
        "status1", "status2"
    ]
    for col in col_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Construção de uma coluna datetime composta a partir da concatenação de data e hora,
    # com dayfirst=True para interpretar corretamente o formato brasileiro "dd/mm/aaaa".
    # Essa coluna serve como índice nas séries temporais dos gráficos.
    df["datetime"] = pd.to_datetime(
        df["data"] + " " + df["hora"],
        dayfirst=True,
        errors="coerce"
    )

    # Descarte de registros com timestamp inválido (NaT): qualquer pacote cuja concatenação
    # data+hora não tenha sido parseável é removido, garantindo que os gráficos não exibam
    # pontos sem referência temporal.
    df = df.dropna(subset=["datetime"])
    return df


# Invocação da função decorada: na primeira execução de cada janela de 60 s, faz a leitura
# real do CSV; nas reexecuções subsequentes dentro do mesmo intervalo, retorna a cópia
# cacheada em memória, com latência desprezível.
df = carregar_dados()

# Verificação de integridade: se o DataFrame estiver vazio (planilha sem dados, erro de
# rede, ou todos os registros descartados por timestamp inválido), exibe alerta amigável
# e interrompe a renderização do restante do painel via st.stop().
if df.empty:
    st.warning("Nenhum dado disponível.")
    st.stop()

# Extração da linha mais recente para alimentação dos cartões de KPI. Como o doPost ordena
# cronologamente a planilha, iloc[-1] retorna sempre o último pacote recebido pelo RX.
ultimo = df.iloc[-1]
st.markdown(f"📡 Fonte: Google Sheets | Registros: {len(df)} | Última leitura: {ultimo['data']} {ultimo['hora']}")

# =============================================================================================
# CARTÕES DE KPI — Cinco colunas equidistantes, cada uma renderizando um cartão temático com
# bordas semânticas (cor lateral indica a natureza da variável). A escolha de cinco colunas
# preserva legibilidade em telas de 1280 px e acima, comprimindo apropriadamente em mobile.
# =============================================================================================
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

    # Mapeamento das flags binárias do TX (1 = operante, 0 = falha) para classes CSS que
    # produzem pontos verdes (flag-ok) ou vermelhos (flag-warn) ao lado do nome do dispositivo.
    # Permite ao operador identificar visualmente, em fração de segundo, se há subsistema
    # comprometido na estação remota.
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

# =============================================================================================
# SÉRIES TEMPORAIS — Gráficos de linha renderizados via st.line_chart, que utiliza o motor
# Altair/Vega-Lite internamente. O índice datetime é definido como eixo X para preservar a
# correta proporção temporal entre pontos não equidistantes (importante quando há falhas de
# transmissão e gaps de mais de 15 minutos). As cores seguem o esquema semântico dos cartões.
# =============================================================================================
st.subheader("🌡️ Temperatura do Solo — 30 cm, 60 cm e 90 cm")
st.line_chart(
    data=df.set_index("datetime")[["solo30", "solo60", "solo90"]],
    color=["#e74c3c", "#3498db", "#e67e22"],
    height=350
)

st.subheader("💧 Umidade do Solo — 30 cm, 60 cm e 90 cm")
st.line_chart(
    data=df.set_index("datetime")[["raw30", "raw60", "raw90"]],
    color=["#e74c3c", "#3498db", "#e67e22"],
    height=350
)

# Disposição em duas colunas das variáveis psicrométricas do ar (temperatura e umidade
# relativa), economizando espaço vertical e facilitando a comparação visual simultânea.
colA, colB = st.columns(2)
with colA:
    st.subheader("🌬️ Temperatura do Ar")
    st.line_chart(data=df.set_index("datetime")["temp_ar"], color="#e74c3c", height=300)
with colB:
    st.subheader("💨 Umidade do Ar (%)")
    st.line_chart(data=df.set_index("datetime")["umid_ar"], color="#3498db", height=300)

# Tabela rolável com os 20 registros mais recentes, exibida em largura total. O .tail(20)
# limita a renderização para preservar a performance de carregamento; o usuário pode rolar
# horizontalmente para inspecionar todas as 12 colunas relevantes do dataset.
st.subheader("📋 Últimos Registros")
st.dataframe(
    df[["data", "hora", "solo30", "solo60", "solo90", "raw30", "raw60", "raw90", "temp_ar", "umid_ar", "status1", "status2"]].tail(20),
    use_container_width=True
)

# =============================================================================================
# BOTÃO DE ATUALIZAÇÃO MANUAL — Oferece controle explícito ao usuário para forçar a
# atualização imediata, sem aguardar o ciclo automático de 60 s. Ao ser pressionado, o botão
# limpa todo o cache do Streamlit (st.cache_data.clear) e dispara uma reexecução completa
# do script (st.rerun), produzindo o efeito de uma releitura instantânea da planilha. Útil
# quando o usuário precisa verificar a recepção de um pacote específico recém-transmitido.
# =============================================================================================
st.divider()
if st.button("🔄 Atualizar agora"):
    st.cache_data.clear()
    st.rerun()
