import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="EITA - Ateliê de Ideias", 
    page_icon="💡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS personalizada para visual clean / elegante
st.markdown("""
<style>
    /* Estilo geral e fundo */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Esconder cabeçalho padrão do Streamlit */
    header {visibility: hidden;}
    
    /* Botões minimalistas no menu central */
    div.stButton > button {
        border: none;
        background-color: transparent;
        color: #1A3644;
        font-weight: 600;
        font-size: 15px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        color: #C5A059;
        background-color: #F8F9FA;
        border-radius: 8px;
    }
    
    /* Títulos de Categorias no Catálogo */
    .categoria-titulo {
        color: #1A3644;
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 2px solid #C5A059;
        padding-bottom: 5px;
    }
    
    /* Esconder bordas pesadas do expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1A3644;
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

# Encontrar caminho da logo
caminho_logo = None
for p in ["logo.png", "imagens/logo.png", "logo.jpg"]:
    if os.path.exists(p):
        caminho_logo = p
        break

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
    if st.session_state["produtos"]:
        df_export = pd.DataFrame(st.session_state["produtos"])
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Backup (CSV)",
            data=csv_data,
            file_name="produtos_3d_backup.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    arquivo_backup = st.file_uploader("📤 Restaurar Backup (CSV)", type=["csv"])
    if arquivo_backup is not None:
        try:
            df_import = pd.read_csv(arquivo_backup)
            st.session_state["produtos"] = df_import.to_dict("records")
            salvar_dados(st.session_state["produtos"])
            st.success("Backup restaurado!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar backup: {e}")

# ==========================================
# PÁGINA INICIAL: CLEAN / DESIGN MINIMALISTA
# ==========================================
if st.session_state["pagina_atual"] == "Home":
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Exibição Centralizada da Logo
    col_e, col_centro, col_d = st.columns([1, 2, 1])
    with col_centro:
        if caminho_logo:
            st.image(caminho_logo, use_container_width=True)
        else:
            st.markdown(
                "<h1 style='text-align: center; color: #1A3644; font-size: 50px; letter-spacing: 4px;'>E I T A</h1>"
                "<p style='text-align: center; color: #888; letter-spacing: 3px;'>ATELIÊ DE IDEIAS</p>", 
                unsafe_allow_html=True
            )
            
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Menu Limpo Inferior (PROTUDOS | CADASTRA NOVO PRODUTO | ORCAMENTO)
    col_m1, col_m2, col_m3 = st.columns([1, 1, 1])
    
    with col_m1:
        if st.button("PROTUDOS", use_container_width=True):
            st.session_state["pagina_atual"] = "Produtos"
            st.rerun()
            
    with col_m2:
        if st.button("CADASTRA NOVO PRODUTO", use_container_width=True):
            st.session_state["edit_index"] = None
            st.session_state["pagina_atual"] = "Cadastrar"
            st.rerun()
            
    with col_m3:
        if st.button("ORCAMENTO", use_container_width=True):
            st.session_state["pagina_atual"] = "Orcamento"
            st.rerun()

# ==========================================
# PÁGINA 2: CATÁLOGO DE PRODUTOS (LAYOUT LOGO2)
# ==========================================
elif st.session_state["pagina_atual"] == "Produtos":
    
    # Cabeçalho no estilo Logo2: Logo + Divisor + Título + Botão VOLTAr
    col_logo, col_div, col_titulo, col_voltar = st.columns([2.5, 0.2, 4, 1.5])
    
    with col_logo:
        if caminho_logo:
            st.image(caminho_logo, width=220)
        else:
            st.markdown("<h3 style='color: #1A3644; margin: 0;'>EITA ATELIÊ DE IDEIAS</h3>", unsafe_allow_html=True)
            
    with col_div:
        st.markdown("<div style='border-left: 2px solid #C5A059; height: 60px; margin: auto;'></div>", unsafe_allow_html=True)
        
    with col_titulo:
        st.markdown("<h2 style='color: #1A3644; font-weight: 400; margin-top: 10px;'>catalogo de Produtos</h2>", unsafe_allow_html=True)
        
    with col_voltar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("VOLTAr", use_container_width=True):
            st.session_state["pagina_atual"] = "Home"
            st.rerun()
            
    st.markdown("---")
    
    produtos = st.session_state["produtos"]
    
    if not produtos:
        st.info("Nenhum produto cadastrado até o momento.")
    else:
        # Agrupamento de Produtos por Categoria
        for cat in categorias_lista:
            prods_cat = [p for p in produtos if p.get("categoria") == cat]
            
            if prods_cat:
                st.markdown(f"<div class='categoria-titulo'>{cat}</div>", unsafe_allow_html=True)
                
                for i_cat, p in enumerate(prods_cat):
                    # Encontrar o índice global do produto
                    idx_global = produtos.index(p)
                    
                    with st.expander(f"{p.get('codigo', 'SKU')} — {p.get('nome', 'Sem nome')}"):
                        col_img, col_info1, col_info2, col_info3 = st.columns([1.5, 1.5, 1.5, 1.5])
                        
                        with col_img:
                            caminho_img = p.get("imagem")
                            if caminho_img and isinstance(caminho_img, str) and os.path.exists(caminho_img):
                                st.image(caminho_img, width=130)
                            else:
                                st.write("*(Sem Imagem)*")

                        with col_info1:
                            st.write(f"**Tempo:** {p.get('tempo')} h")
                            st.write(f"**Material:** {p.get('material')} g")
                        with col_info2:
                            st.write(f"**Custo Produção:** € {p.get('producao', 0):.2f}")
                            st.write(f"**Margem:** {p.get('margem')}%")
                            st.write(f"**Lucro:** € {p.get('lucro', 0):.2f}")
                        with col_info3:
                            st.markdown(f"### **€ {p.get('venda', 0):.2f}**")
                                
                        col_A, col_B, _ = st.columns([1, 1, 3])
                        with col_A:
                            if st.button("Editar", key=f"edit_cat_{idx_global}"):
                                st.session_state["edit_index"] = idx_global
                                st.session_state["pagina_atual"] = "Cadastrar"
                                st.rerun()
                        with col_B:
                            if st.button("Excluir", key=f"del_cat_{idx_global}"):
                                img_path = p.get("imagem")
                                if img_path and isinstance(img_path, str) and os.path.exists(img_path):
                                    try:
                                        os.remove(img_path)
                                    except:
                                        pass
                                st.session_state["produtos"].pop(idx_global)
                                salvar_dados(st.session_state["produtos"])
                                st.rerun()

# ==========================================
# PÁGINA 3: CADASTRAR / EDITAR PRODUTO
# ==========================================
elif st.session_state["pagina_atual"] == "Cadastrar":
    col_voltar, col_t = st.columns([1.5, 5])
    with col_voltar:
        if st.button("VOLTAr"):
            st.session_state["edit_index"] = None
            st.session_state["pagina_atual"] = "Home"
            st.rerun()
            
    is_editing = st.session_state["edit_index"] is not None
    
    with col_t:
        titulo_pg = "Editar Produto" if is_editing else "Cadastrar Novo Produto"
        st.markdown(f"<h2 style='color: #1A3644; margin: 0;'>{titulo_pg}</h2>", unsafe_allow_html=True)

    st.markdown("---")
    
    prod_edit = st.session_state["produtos"][st.session_state["edit_index"]] if is_editing else {
        "codigo": "", "nome": "", "categoria": "Decoração",
        "tempo": 0.0, "material": 0.0, "margem": 100.0, "imagem": None
    }

    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        cat_atual = str(prod_edit.get("categoria", "Decoração"))
        cat_index = categorias_lista.index(cat_atual) if cat_atual in categorias_lista else 0
        categoria = st.selectbox("Categoria", categorias_lista, index=cat_index)
        
        if not is_editing:
            prefixo_atual = prefixos_categorias.get(categoria, "PRD")
            produtos_mesma_cat = [p for p in st.session_state["produtos"] if p.get("categoria") == categoria]
            codigo_sugerido = f"{prefixo_atual}-{len(produtos_mesma_cat) + 1:03d}"
        else:
            codigo_sugerido = str(prod_edit.get("codigo", ""))

        codigo = st.text_input("Código SKU", value=codigo_sugerido, disabled=True)
        nome = st.text_input("Nome do Produto", value=str(prod_edit.get("nome", "")))
        
    with col_f2:
        tempo_impressao = st.number_input("Tempo de Impressão (Horas)", min_value=0.0, step=0.5, value=float(prod_edit.get("tempo", 0.0)))
        material_uso = st.number_input("Material Utilizado (Gramas)", min_value=0.0, step=1.0, value=float(prod_edit.get("material", 0.0)))
        margem_desejada = st.number_input("Margem de Lucro (%)", min_value=0.0, step=10.0, value=float(prod_edit.get("margem", 100.0)))

    foto_produto = st.file_uploader("Carregar Imagem / Foto do Produto", type=["jpg", "jpeg", "png"])
    
    if st.button("Salvar Produto", use_container_width=True):
        if not nome:
            st.error("Por favor, preencha o Nome do produto.")
        else:
            try:
                preco_producao = (material_uso * custo_filamento_g) + (tempo_impressao * custo_hora_maquina)
                valor_lucro = preco_producao * (margem_desejada / 100)
                preco_venda = preco_producao + valor_lucro
                
                caminho_imagem_salva = prod_edit.get("imagem", None)
                if foto_produto is not None:
                    nome_limpo = "".join(c for c in foto_produto.name if c.isalnum() or c in ('.', '_', '-'))
                    caminho_imagem_salva = os.path.join(PASTA_IMAGENS, f"{codigo_sugerido.replace('-', '_')}_{nome_limpo}")
                    with open(caminho_imagem_salva, "wb") as f:
                        f.write(foto_produto.getbuffer())

                produto_dados = {
                    "codigo": codigo_sugerido,
                    "nome": nome,
                    "categoria": categoria,
                    "tempo": tempo_impressao,
                    "material": material_uso,
                    "producao": preco_producao,
                    "margem": margem_desejada,
                    "venda": preco_venda,
                    "lucro": valor_lucro,
                    "imagem": caminho_imagem_salva
                }
                
                if is_editing:
                    st.session_state["produtos"][st.session_state["edit_index"]] = produto_dados
                    st.session_state["edit_index"] = None
                else:
                    st.session_state["produtos"].append(produto_dados)
                
                salvar_dados(st.session_state["produtos"])
                st.success("Produto salvo com sucesso!")
                st.session_state["pagina_atual"] = "Produtos"
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ==========================================
# PÁGINA 4: GERAR ORÇAMENTO
# ==========================================
elif st.session_state["pagina_atual"] == "Orcamento":
    col_voltar, col_t = st.columns([1.5, 5])
    with col_voltar:
        if st.button("VOLTAr"):
            st.session_state["pagina_atual"] = "Home"
            st.rerun()
    with col_t:
        st.markdown("<h2 style='color: #1A3644; margin: 0;'>Gerador de Orçamentos</h2>", unsafe_allow_html=True)

    st.markdown("---")
    
    produtos = st.session_state["produtos"]
    if not produtos:
        st.warning("Cadastre produtos antes de gerar um orçamento.")
    else:
        opcoes_produtos = {f"{p.get('codigo')} - {p.get('nome')} (€ {p.get('venda', 0):.2f})": p for p in produtos}
        produtos_selecionados = st.multiselect("Selecione os Produtos", options=list(opcoes_produtos.keys()))
        
        if produtos_selecionados:
            total_geral = 0.0
            st.markdown("### Resumo do Pedido")
            for nome_op in produtos_selecionados:
                prod = opcoes_produtos[nome_op]
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{prod.get('nome')}** ({prod.get('codigo')})")
                with col2:
                    qtd = st.number_input(f"Qtd", min_value=1, value=1, key=f"q_{prod.get('codigo')}")
                with col3:
                    desc = st.number_input(f"Desc (%)", min_value=0.0, max_value=100.0, value=0.0, key=f"d_{prod.get('codigo')}")
                
                subtotal = (float(prod.get('venda', 0)) * qtd) * (1 - (desc / 100))
                total_geral += subtotal
                st.write(f"Subtotal: **€ {subtotal:.2f}**")
                st.markdown("---")
                
            st.markdown(f"## **Total Final: € {total_geral:.2f}**")