import streamlit as st
import pandas as pd
import os

# Configuração da Página
st.set_page_config(page_title="Gestão EITA", page_icon="🖨️", layout="wide")

# Caminhos dos arquivos e pastas
PASTA_IMAGENS = "imagens"
ARQUIVO_CATALOGO = "catalogo_produtos.csv"
ARQUIVO_ANTIGO = "produtos_3d.csv"
ARQUIVO_COMPRAS = "compras_insumos.csv"

os.makedirs(PASTA_IMAGENS, exist_ok=True)
categorias_produtos_lista = ["Decoração", "Natal", "Acessórios", "Utilitários", "Utilidades", "Brinquedos", "Outros"]

# ==========================================
# GERENCIAMENTO DE ESTADO
# ==========================================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Início"

if "catalogo" not in st.session_state:
    if os.path.exists(ARQUIVO_CATALOGO):
        try:
            st.session_state["catalogo"] = pd.read_csv(ARQUIVO_CATALOGO).to_dict("records")
        except:
            st.session_state["catalogo"] = []
    elif os.path.exists(ARQUIVO_ANTIGO):
        try:
            df_old = pd.read_csv(ARQUIVO_ANTIGO)
            conv = []
            for _, r in df_old.iterrows():
                t = float(r.get("tempo", 0.0))
                conv.append({
                    "codigo": str(r.get("codigo", "SKU-001")),
                    "nome": str(r.get("nome", "Produto")),
                    "categoria": str(r.get("categoria", "Outros")),
                    "horas_imp": int(t),
                    "minutos_imp": int(round((t - int(t)) * 60)),
                    "gramas_pla": float(r.get("material", 0.0)),
                    "custo_estimado": float(r.get("producao", 0.0)),
                    "foto": str(r.get("imagem", ""))
                })
            st.session_state["catalogo"] = conv
        except:
            st.session_state["catalogo"] = []
    else:
        st.session_state["catalogo"] = []

if "compras" not in st.session_state:
    if os.path.exists(ARQUIVO_COMPRAS):
        try:
            st.session_state["compras"] = pd.read_csv(ARQUIVO_COMPRAS).to_dict("records")
        except:
            st.session_state["compras"] = []
    else:
        st.session_state["compras"] = []

def salvar_dados(caminho, dados):
    try:
        pd.DataFrame(dados).to_csv(caminho, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# ==========================================
# MENU LATERAL & DOWNLOAD DE ARQUIVOS
# ==========================================
st.sidebar.title("🖨️ Sistema EITA")
menu_opcoes = ["Início", "Catálogo", "Calcular", "Compras", "Produção"]
escolha_lateral = st.sidebar.radio("Navegação", menu_opcoes, index=menu_opcoes.index(st.session_state["pagina"]) if st.session_state["pagina"] in menu_opcoes else 0)

st.session_state["pagina"] = escolha_lateral

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Downloads de Arquivos")

# Função auxiliar para download
def botao_download(nome_arquivo, label):
    if os.path.exists(nome_arquivo):
        with open(nome_arquivo, "rb") as f:
            st.sidebar.download_button(
                label=label,
                data=f,
                file_name=nome_arquivo,
                mime="text/csv"
            )
    else:
        st.sidebar.caption(f"{nome_arquivo} não encontrado.")

botao_download(ARQUIVO_CATALOGO, "📥 Baixar Catálogo (CSV)")
botao_download(ARQUIVO_ANTIGO, "📥 Baixar Dados Antigos (CSV)")
botao_download(ARQUIVO_COMPRAS, "📥 Baixar Compras (CSV)")

# ==========================================
# 1. PÁGINA INICIAL (HOME)
# ==========================================
if st.session_state["pagina"] == "Início":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Centralizando a Logo e os botões
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        # Exibe a logo se existir na pasta ou exibe um título elegante caso não tenha o arquivo logo.png
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center;'>🖨️ GESTÃO EITA</h1>", unsafe_allow_html=True)
            st.caption("<p style='text-align: center;'>Central de Controle de Impressão 3D</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>Escolha uma opção abaixo:</h4>", unsafe_allow_html=True)
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("📊 Catálogo", use_container_width=True):
                st.session_state["pagina"] = "Catálogo"
                st.rerun()
            if st.button("💰 Calcular", use_container_width=True):
                st.session_state["pagina"] = "Calcular"
                st.rerun()
        with b2:
            if st.button("🛒 Compras", use_container_width=True):
                st.session_state["pagina"] = "Compras"
                st.rerun()
            if st.button("⚙️ Produção", use_container_width=True):
                st.session_state["pagina"] = "Produção"
                st.rerun()

# ==========================================
# 2. CATÁLOGO DE PRODUTOS
# ==========================================
elif st.session_state["pagina"] == "Catálogo":
    st.markdown("## 📊 Catálogo de Produtos")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    if not st.session_state["catalogo"]:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        for cat in categorias_produtos_lista:
            prods = [p for p in st.session_state["catalogo"] if p.get("categoria") == cat]
            if prods:
                with st.expander(f"📁 **{cat}** ({len(prods)} produtos)"):
                    for idx, prod in enumerate(prods):
                        st.markdown(f"**🏷️ [{prod.get('codigo')}] {prod.get('nome')}**")
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.write(f"• **Peso PLA:** {prod.get('gramas_pla', 0)}g")
                            st.write(f"• **Custo Estimado:** € {float(prod.get('custo_estimado', 0.0)):.2f}")
                        with c2:
                            foto = str(prod.get("foto", ""))
                            if foto and os.path.exists(foto):
                                st.image(foto, use_container_width=True)
                            else:
                                st.caption("Sem foto")
                        st.markdown("---")

# ==========================================
# 3. CALCULADORA
# ==========================================
elif st.session_state["pagina"] == "Calcular":
    st.markdown("## 💰 Calculadora de Precificação")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    c1, c2 = st.columns(2)
    with c1:
        gramas = st.number_input("Gramas de PLA", min_value=0.0, value=50.0)
        horas = st.number_input("Horas de Impressão", min_value=0.0, value=3.0)
    with c2:
        margem = st.number_input("Margem de Lucro (%)", min_value=0.0, value=100.0)
        custo = (gramas * 0.025) + (horas * 0.50)
        venda = custo * (1 + (margem / 100))
        st.markdown(f"### Custo: € {custo:.2f}")
        st.markdown(f"### Venda Sugerida: € {venda:.2f}")

# ==========================================
# 4. COMPRAS
# ==========================================
elif st.session_state["pagina"] == "Compras":
    st.markdown("## 🛒 Cadastro de Compras")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    with st.form("form_compra"):
        material = st.selectbox("Material", ["PLA", "NFC", "Argola", "Outros"])
        qtd = st.number_input("Quantidade", min_value=0.1, value=1.0)
        total = st.number_input("Custo Total (€)", min_value=0.0, value=20.0)
        if st.form_submit_button("Salvar Compra"):
            st.session_state["compras"].append({"material": material, "quantidade": qtd, "custo_total": total})
            salvar_dados(ARQUIVO_COMPRAS, st.session_state["compras"])
            st.success("Compra salva!")
            st.rerun()

# ==========================================
# 5. PRODUÇÃO
# ==========================================
elif st.session_state["pagina"] == "Produção":
    st.markdown("## ⚙️ Registro de Produção")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    st.info("Módulo de produção pronto para novos registros.")