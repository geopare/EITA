import streamlit as st
import pandas as pd
import os
import base64
from github import Github, GithubException

st.set_page_config(
    page_title="EITA - Ateliê de Ideias", 
    page_icon="💡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada com a cor (#103b57) em todos os textos
st.markdown("""
<style>
    /* Estilo geral e fundo */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Cor padrão (#103b57) para todos os textos */
    html, body, [class*="css"], p, span, label, h1, h2, h3, h4, h5, h6, div {
        color: #103b57 !important;
    }
    
    /* Botões minimalistas */
    div.stButton > button {
        border: none;
        background-color: transparent;
        color: #103b57 !important;
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
        color: #103b57 !important;
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 2px solid #C5A059;
        padding-bottom: 5px;
    }
    
    /* Bloco Integrado do Cabeçalho */
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
        color: #103b57 !important;
        font-size: 32px;
        font-weight: 400;
        margin: 0;
        padding: 0;
        line-height: 1;
        letter-spacing: 1.5px;
    }
    
    /* Expander e Inputs */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #103b57 !important;
    }
    
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        color: #103b57 !important;
    }
</style>
""", unsafe_allow_html=True)

ARQUIVO_DADOS = "produtos_3d.csv"
PASTA_IMAGENS = "imagens"

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

# ==========================================
# FUNÇÕES DE INTEGRAÇÃO AUTOMÁTICA COM GITHUB
# ==========================================
def salvar_arquivo_no_github(caminho_arquivo, conteudo_bytes, mensagem_commit):
    """Envia/atualiza um arquivo diretamente no repositório GitHub via API."""
    if "GITHUB_TOKEN" in st.secrets and "REPO_NAME" in st.secrets:
        try:
            token = st.secrets["GITHUB_TOKEN"]
            repo_name = st.secrets["REPO_NAME"]
            branch = st.secrets.get("BRANCH", "main")
            
            g = Github(token)
            repo = g.get_repo(repo_name)
            
            try:
                file_github = repo.get_contents(caminho_arquivo, ref=branch)
                repo.update_file(
                    path=caminho_arquivo,
                    message=mensagem_commit,
                    content=conteudo_bytes,
                    sha=file_github.sha,
                    branch=branch
                )
            except GithubException:
                repo.create_file(
                    path=caminho_arquivo,
                    message=mensagem_commit,
                    content=conteudo_bytes,
                    branch=branch
                )
            return True
        except Exception as e:
            st.warning(f"Aviso de sincronização GitHub: {e}")
            return False
    return False

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
        
        # Automação: envia o CSV para o GitHub
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        salvar_arquivo_no_github(ARQUIVO_DADOS, csv_bytes, "Atualização automática do banco de produtos")
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

# Sessão
if "produtos" not in st.session_state:
    st.session_state["produtos"] = carregar_dados()

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Home"

if "custo_filamento_g" not in st.session_state:
    st.session_state["custo_filamento_g"] = 0.014
if "custo_hora_maquina" not in st.session_state:
    st.session_state["custo_hora_maquina"] = 1.00

categorias_lista = [
    "Decoração", "Utilitários", "Miniaturas", "Laços", 
    "Acessórios", "Organização", "Natal", "Religiao", "Outros"
]

prefixos_categorias = {
    "Decoração": "DEC", "Utilitários": "UTI", "Miniaturas": "MIN",
    "Laços": "LAC", "Acessórios": "ACE", "Organização": "ORG",
    "Natal": "NAT", "Religiao": "REL", "Outros": "OUT",
}

# Verificação das Logos
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

def renderizar_cabecalho(titulo_pagina, exibir_btn_novo=False):
    col_cabecalho, col_acoes = st.columns([4, 2])
    
    with col_cabecalho:
        if caminho_logo2:
            with open(caminho_logo2, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            html_header = f"""
            <div class="header-catalogo-container">
                <img src="data:image/png;base64,{encoded_string}" style="max-height: 55px; width: auto;" />
                <div class="header-linha-dourada"></div>
                <h2 class="header-titulo-catalogo">{titulo_pagina}</h2>
            </div>
            """
            st.markdown(html_header, unsafe_allow_html=True)
        else:
            html_header = f"""
            <div class="header-catalogo-container">
                <h3 style="color: #103b57; margin: 0;">EITA ATELIÊ DE IDEIAS</h3>
                <div class="header-linha-dourada"></div>
                <h2 class="header-titulo-catalogo">{titulo_pagina}</h2>
            </div>
            """
            st.markdown(html_header, unsafe_allow_html=True)
            
    with col_acoes:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if exibir_btn_novo:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("➕ NOVO", use_container_width=True):
                    st.session_state["edit_index"] = None
                    st.session_state["pagina_atual"] = "Cadastrar"
                    st.rerun()
            with btn_col2:
                if st.button("VOLTAr", use_container_width=True):
                    st.session_state["edit_index"] = None
                    st.session_state["pagina_atual"] = "Home"
                    st.rerun()
        else:
            if st.button("VOLTAr", use_container_width=True):
                st.session_state["edit_index"] = None
                st.session_state["pagina_atual"] = "Home"
                st.rerun()

# ==========================================
# BARRA LATERAL (MENU & BACKUP)
# ==========================================
with st.sidebar:
    st.title("⚙️ Configurações & Backup")
    
    if st.button("🏠 Ir para a Tela Inicial", use_container_width=True):
        st.session_state["pagina_atual"] = "Home"
        st.session_state["edit_index"] = None
        st.rerun()

    st.markdown("---")
    st.subheader("💶 Custos Base (Alemanha)")
    st.session_state["custo_filamento_g"] = st.number_input("Custo Filamento (€/g)", min_value=0.0, value=float(st.session_state["custo_filamento_g"]), step=0.001, format="%.3f", key="side_filamento")
    st.session_state["custo_hora_maquina"] = st.number_input("Custo Hora Máquina (€/h)", min_value=0.0, value=float(st.session_state["custo_hora_maquina"]), step=0.10, format="%.2f", key="side_maquina")

    st.markdown("---")
    st.subheader("💾 Gestão de Backup")
    
    if st.session_state["produtos"]:
        df_export = pd.DataFrame(st.session_state["produtos"])
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Backup (CSV)",
            data=csv_data,
            file_name="produtos_3d.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Nenhum produto cadastrado para exportar.")

    st.markdown("")
    arquivo_backup = st.file_uploader("📤 Restaurar Backup (CSV)", type=["csv"], key="uploader_backup_side")
    if arquivo_backup is not None:
        try:
            df_import = pd.read_csv(arquivo_backup)
            st.session_state["produtos"] = df_import.to_dict("records")
            salvar_dados(st.session_state["produtos"])
            st.success("Backup restaurado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar backup: {e}")

# ==========================================
# PÁGINA INICIAL: CLEAN
# ==========================================
if st.session_state["pagina_atual"] == "Home":
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_e, col_centro, col_d = st.columns([1, 2, 1])
    with col_centro:
        if caminho_logo:
            st.image(caminho_logo, use_container_width=True)
        else:
            st.markdown(
                "<h1 style='text-align: center; color: #103b57; font-size: 50px; letter-spacing: 4px;'>E I T A</h1>"
                "<p style='text-align: center; color: #C5A059; letter-spacing: 3px;'>ATELIÊ DE IDEIAS</p>", 
                unsafe_allow_html=True
            )
            
    st.markdown("<br><br>", unsafe_allow_html=True)
    
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
# PÁGINA 2: CATÁLOGO DE PRODUTOS
# ==========================================
elif st.session_state["pagina_atual"] == "Produtos":
    
    renderizar_cabecalho("PRODUTOS", exibir_btn_novo=True)
    st.markdown("---")
    
    produtos = st.session_state["produtos"]
    
    if not produtos:
        st.info("Nenhum produto cadastrado até o momento.")
    else:
        for cat in categorias_lista:
            prods_cat = [p for p in produtos if p.get("categoria") == cat]
            
            if prods_cat:
                st.markdown(f"<div class='categoria-titulo'>{cat}</div>", unsafe_allow_html=True)
                
                for i_cat, p in enumerate(prods_cat):
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
    
    is_editing = st.session_state["edit_index"] is not None
    titulo_pg = "EDITAR PRODUTO" if is_editing else "CADASTRAR PRODUTO"
    
    renderizar_cabecalho(titulo_pg)
    st.markdown("---")
    
    prod_edit = st.session_state["produtos"][st.session_state["edit_index"]] if is_editing else {
        "codigo": "", "nome": "", "categoria": "Decoração",
        "tempo": 0.0, "material": 0.0, "margem": 100.0, "imagem": None
    }

    with st.expander("⚙️ Ajustar Custos Base de Cálculo (€)", expanded=False):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.session_state["custo_filamento_g"] = st.number_input(
                "Custo Filamento (€/g)", 
                min_value=0.0, 
                value=float(st.session_state["custo_filamento_g"]), 
                step=0.001, 
                format="%.3f",
                key="input_custo_fil"
            )
        with col_c2:
            st.session_state["custo_hora_maquina"] = st.number_input(
                "Custo Hora Máquina (€/h)", 
                min_value=0.0, 
                value=float(st.session_state["custo_hora_maquina"]), 
                step=0.10, 
                format="%.2f",
                key="input_custo_maq"
            )

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
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Salvar Produto", use_container_width=True):
        if not nome:
            st.error("Por favor, preencha o Nome do produto.")
        else:
            try:
                c_fil = st.session_state["custo_filamento_g"]
                c_maq = st.session_state["custo_hora_maquina"]
                
                preco_producao = (material_uso * c_fil) + (tempo_impressao * c_maq)
                valor_lucro = preco_producao * (margem_desejada / 100)
                preco_venda = preco_producao + valor_lucro
                
                caminho_imagem_salva = prod_edit.get("imagem", None)
                if foto_produto is not None:
                    nome_limpo = "".join(c for c in foto_produto.name if c.isalnum() or c in ('.', '_', '-'))
                    caminho_imagem_salva = os.path.join(PASTA_IMAGENS, f"{codigo_sugerido.replace('-', '_')}_{nome_limpo}")
                    
                    bytes_foto = foto_produto.getvalue()
                    with open(caminho_imagem_salva, "wb") as f:
                        f.write(bytes_foto)
                    
                    # Automação: envia a foto para o repositório no GitHub
                    salvar_arquivo_no_github(caminho_imagem_salva, bytes_foto, f"Upload de foto para {codigo_sugerido}")

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
                st.success("Produto e imagem salvos com sucesso no GitHub!")
                st.session_state["pagina_atual"] = "Produtos"
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ==========================================
# PÁGINA 4: GERADOR DE ORÇAMENTOS
# ==========================================
elif st.session_state["pagina_atual"] == "Orcamento":
    
    renderizar_cabecalho("ORÇAMENTO")
    st.markdown("---")
    
    produtos = st.session_state["produtos"]
    
    if not produtos:
        st.warning("Ainda não há produtos cadastrados.")
    else:
        opcoes_produtos = {
            f"{p.get('codigo', 'SKU')} — {p.get('nome', 'Produto')} (€ {p.get('venda', 0):.2f})": p 
            for p in produtos
        }
        
        produtos_selecionados_chaves = st.multiselect(
            "🛒 Selecione os Produtos para o Orçamento", 
            options=list(opcoes_produtos.keys())
        )
        
        if produtos_selecionados_chaves:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #103b57;'>📦 Detalhes e Quantidades</h3>", unsafe_allow_html=True)
            
            total_orcamento = 0.0
            resumo_texto = "📋 *ORÇAMENTO — EITA ATELIÊ DE IDEIAS*\n\n"
            
            for i_item, chave in enumerate(produtos_selecionados_chaves):
                prod = opcoes_produtos[chave]
                codigo = prod.get('codigo', '')
                nome = prod.get('nome', '')
                preco_unit = float(prod.get('venda', 0))
                
                with st.expander(f"🔹 {codigo} — {nome} (€ {preco_unit:.2f}/unid)", expanded=True):
                    col_qtd, col_desc, col_total_item = st.columns([1.5, 1.5, 2])
                    
                    with col_qtd:
                        qtd = st.number_input(
                            f"Quantidade", 
                            min_value=1, 
                            value=1, 
                            step=1, 
                            key=f"orc_qtd_{codigo}_{i_item}"
                        )
                        
                    with col_desc:
                        desc = st.number_input(
                            f"Desconto (%)", 
                            min_value=0.0, 
                            max_value=100.0, 
                            value=0.0, 
                            step=5.0, 
                            key=f"orc_desc_{codigo}_{i_item}"
                        )
                        
                    subtotal_bruto = preco_unit * qtd
                    desconto_val = subtotal_bruto * (desc / 100)
                    subtotal_liquido = subtotal_bruto - desconto_val
                    total_orcamento += subtotal_liquido
                    
                    with col_total_item:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"Subtotal: **€ {subtotal_liquido:.2f}**")
                    
                    desc_str = f" (-{desc:.0f}%)" if desc > 0 else ""
                    resumo_texto += f"• *{qtd}x {nome}* ({codigo})\n  € {preco_unit:.2f} un. → *€ {subtotal_liquido:.2f}*{desc_str}\n\n"

            resumo_texto += f"-----------------------------\n💰 *TOTAL DO ORÇAMENTO: € {total_orcamento:.2f}*"

            st.markdown("---")
            st.markdown(f"<h2 style='color: #103b57;'>💰 Total Geral: € {total_orcamento:.2f}</h2>", unsafe_allow_html=True)
            
            with st.expander("📄 Ver Resumo Formatado para Enviar ao Cliente"):
                st.code(resumo_texto, language="text")