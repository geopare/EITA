import streamlit as st
import pandas as pd
import os
import time

# Configuração da Página
st.set_page_config(page_title="Gestão EITA", page_icon="🖨️", layout="wide")

# Caminhos dos arquivos e pastas
PASTA_IMAGENS = "imagens"
ARQUIVO_ANTIGO = "produtos_3d.csv"
ARQUIVO_CATALOGO = "catalogo_produtos.csv"

# Garante que a pasta de imagens existe
os.makedirs(PASTA_IMAGENS, exist_ok=True)

# Lista completa de categorias para abranger tudo do CSV antigo
categorias_produtos_lista = ["Decoração", "Natal", "Acessórios", "Utilitários", "Utilidades", "Brinquedos", "Outros"]

# ==========================================
# FUNÇÃO DE CARREGAMENTO DIRETA DO CSV ANTIGO
# ==========================================
@st.cache_data
def carregar_catalogo_direto():
    # Prioriza o arquivo principal produtos_3d.csv que contém todos os seus dados reais
    caminho_usado = ARQUIVO_ANTIGO if os.path.exists(ARQUIVO_ANTIGO) else ARQUIVO_CATALOGO
    
    if os.path.exists(caminho_usado):
        try:
            df = pd.read_csv(caminho_usado)
            produtos_convertidos = []
            for _, row in df.iterrows():
                # Se já estiver no formato do catálogo novo
                if "horas_imp" in df.columns:
                    produtos_convertidos.append(row.to_dict())
                else:
                    # Converte do formato antigo produtos_3d.csv
                    tempo_total = float(row.get("tempo", 0.0))
                    horas = int(tempo_total)
                    minutos = int(round((tempo_total - horas) * 60))
                    
                    produtos_convertidos.append({
                        "codigo": str(row.get("codigo", "SKU-001")),
                        "nome": str(row.get("nome", "Produto")),
                        "categoria": str(row.get("categoria", "Outros")),
                        "horas_imp": horas,
                        "minutos_imp": minutos,
                        "gramas_pla": float(row.get("material", 0.0)),
                        "usar_argola": False,
                        "qtd_argola": 1,
                        "usar_nfc": False,
                        "qtd_nfc": 1,
                        "insumos": f"{float(row.get('material', 0.0)):.0f}g PLA",
                        "custo_estimado": float(row.get("producao", 0.0)),
                        "foto": str(row.get("imagem", ""))
                    })
            return produtos_convertidos
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return []
    return []

def salvar_csv(caminho, dados, mensagem_sucesso):
    try:
        df = pd.DataFrame(dados)
        df.to_csv(caminho, index=False)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao salvar arquivo {caminho}: {e}")

# ==========================================
# INICIALIZAÇÃO DO SESSION STATE
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "ProdutosCatalogo"

if "catalogo" not in st.session_state:
    st.session_state["catalogo"] = carregar_catalogo_direto()

if "compras" not in st.session_state:
    st.session_state["compras"] = []

if "mostrar_produtos_catalogo" not in st.session_state:
    st.session_state["mostrar_produtos_catalogo"] = True # Já inicia mostrando para facilitar!

if "edit_idx_catalogo" not in st.session_state:
    st.session_state["edit_idx_catalogo"] = None

def renderizar_cabecalho(titulo):
    st.markdown(f"## 🖨️ Sistema EITA - {titulo}")