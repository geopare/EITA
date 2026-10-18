import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="EITA - Ateliê de Ideias", 
    page_icon="💡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS personalizada com a cor exata da logo (#1A3644) em todos os textos
st.markdown("""
<style>
    /* Estilo geral e fundo */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Esconder cabeçalho padrão do Streamlit */
    header {visibility: hidden;}
    
    /* Cor padrão (#1A3644) para todos os textos, parágrafos, labels e marcadores */
    html, body, [class*="css"], p, span, label, h1, h2, h3, h4, h5, h6, div {
        color: #1A3644 !important;
    }
    
    /* Botões minimalistas no menu e navegação */
    div.stButton > button {
        border: none;
        background-color: transparent;
        color: #1A3644 !important;
        font-weight: 600;
        font-size: 15px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        color: #C5A059 !important;
        background-color: #F8F9FA;
        border-radius: 8px;
    }
    
    /* Títulos de Categorias no Catálogo */
    .categoria-titulo {
        color: #1A3644 !important;
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 2px solid #C5A059;
        padding-bottom: 5px;
    }
    
    /* Bloco Integrado do Cabeçalho do Catálogo */
    .header-catalogo-container {
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .header-linha-dourada {
        border-left: 2px solid #C5A059;
        height: 48px;
    }
    .header-titulo-catalogo {
        color: #1A3644 !important;
        font-size: 32px;
        font-weight: 400;
        margin: 0;
        padding: 0;
        line-height: 1;
    }
    
    /* Personalização de acionadores/expansores */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1A3644 !important;
    }
    
    /* Ajustes em inputs e seletores */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        color: #1A3644 !important;
    }
</style>
""", unsafe_allow_html=True)

ARQUIVO_DADOS = "produtos_3d.csv"
PASTA_IMAGENS = "imagens"

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

# Carregar e Salvar Dados
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            df = pd.read_csv(ARQUIVO_DADOS)
            return df.to_dict("records")
        except Exception:
            return []
    return []

def salvar_dados(produtos_lista):
    try:
        df = pd.DataFrame(produtos_lista)
        df.to_csv(ARQUIVO_DADOS, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar dados localmente: {e}")

# Sessão
if "produtos" not in st.session_state:
    st.session_state["produtos"] = carregar_dados()

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Home"

# Custos Alemanha
if "custo_filamento_g" not in st.session_state:
    st.session_state["custo_filamento_g"] = 0.014
if "custo_hora_maquina" not in st.session_state:
    st.session_state["custo_hora_maquina"] = 1.00

custo_filamento_g = st.session_state["custo_filamento_g"]
custo_hora_maquina = st.session_state["custo_hora_maquina"]

categorias_lista = [
    "Decoração", "Utilitários", "Miniaturas", "Laços", 
    "Acessórios", "Organização", "Natal", "Religiao", "Outros"
]

prefixos_categorias = {
    "Decoração": "DEC", "Utilitários": "UTI", "Miniaturas": "MIN",
    "Laços": "LAC", "Acessórios": "ACE", "Organização": "ORG",
    "Natal": "NAT", "Religiao": "REL", "Outros": "OUT",
}

# ==========================================
# VERIFICAÇÃO E CARREGAMENTO DAS LOGOS
# ==========================================
caminho_logo = None
for p in ["logo.png", "imagens/logo.png", "logo.jpg"]:
    if os.path.exists(p):
        caminho_logo = p
        break

caminho_logo2 = None
for p in ["logo2.png", "imagens/logo2.png", "logo2.jpg"]:
    if os.path.exists(p):
        caminho_logo2 = p
        break

if not caminho_logo2:
    caminho_logo2 = caminho_logo

# ==========================================
# BARRA LATERAL (MENU SECUNDÁRIO E BACKUP)
# ==========================================
with st.sidebar:
    st.title("⚙️ Configurações & Backup")
    
    if st.button("🏠 Ir para a Tela Inicial", use_container_width=True):
        st.session_state["pagina_atual"] = "Home"
        st.session_state["edit_index"] = None
        st.rerun()

    st.markdown("---")
    st.subheader("💶 Custos Base (Alemanha)")
    st.session_state["custo_filamento_g"] = st.number_input("Custo Filamento (€/g)", min_value=0.0, value=custo_filamento_g, step=0.001, format="%.3f")
    st.session_state["custo_hora_maquina"] = st.number_input("Custo Hora Máquina (€/h)", min_value=0.0, value=custo_hora_maquina, step=0.10, format="%.2f")

    st.markdown("---")
    st.subheader("💾 Gestão de Backup")
    if st