import streamlit as st
import pandas as pd
import os
import base64
import time
from github import Github, GithubException

st.set_page_config(
    page_title="EITA - Sistema de Gestão e Produção", 
    page_icon="💡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada
st.markdown("""
<style>
    .main { background-color: #FFFFFF; }
    html, body, [class*="css"], p, span, label, h1, h2, h3, h4, h5, h6, div { color: #103b57 !important; }
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
    .categoria-titulo {
        color: #103b57 !important;
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 2px solid #C5A059;
        padding-bottom: 5px;
    }
    .header-catalogo-container { display: flex; align-items: center; gap: 18px; }
    .header-linha-dourada { border-left: 2px solid #C5A059; height: 48px; }
    .header-titulo-catalogo {
        color: #103b57 !important;
        font-size: 32px;
        font-weight: 400;
        margin: 0; padding: 0; line-height: 1; letter-spacing: 1.5px;
    }
</style>
""", unsafe_allow_html=True)

# Arquivos de dados do sistema unificado
ARQUIVO_ANTIGO = "produtos_3d.csv"
ARQUIVO_COMPRAS = "compras_materiais.csv"
ARQUIVO_PRODUCAO = "producao_itens.csv"
ARQUIVO_VENDAS = "vendas_registros.csv"
PASTA_IMAGENS = "imagens"

if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

# ==========================================
# FUNÇÕES DE GITHUB & PERSISTÊNCIA
# ==========================================
def salvar_no_github(caminho_arquivo, conteudo_bytes, mensagem):
    if "GITHUB_TOKEN" in st.secrets and "REPO_NAME" in st.secrets:
        try:
            token = st.secrets["GITHUB_TOKEN"]
            repo_name = st.secrets["REPO_NAME"]
            branch = st.secrets.get("BRANCH", "master")
            caminho_github = caminho_arquivo.replace("\\", "/")
            
            g = Github(token)
            repo = g.get_repo(repo_name)
            
            try:
                file_github = repo.get_contents(caminho_github, ref=branch)
                repo.update_file(path=caminho_github, message=mensagem, content=conteudo_bytes, sha=file_github.sha, branch=branch)
            except GithubException:
                repo.create_file(path=caminho_github, message=mensagem, content=conteudo_bytes, branch=branch)
            return True
        except Exception as e:
            st.error(f"Erro na sincronização GitHub: {e}")
            return False
    return False

def carregar_csv(caminho, colunas_padrao):
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho)
            for col in colunas_padrao:
                if col not in df.columns:
                    df[col] = colunas_padrao[col]
            return df.to_dict("records")
        except:
            return []
    return []

def salvar_csv(caminho, dados, mensagem):
    try:
        df = pd.DataFrame(dados)
        df.to_csv(caminho, index=False)
        salvar_no_github(caminho, df.to_csv(index=False).encode('utf-8'), mensagem)
    except Exception as e:
        st.error(f"Erro ao salvar arquivo {caminho}: {e}")

# ==========================================
# IMPORTAÇÃO AUTOMÁTICA DOS DADOS ANTIGOS
# ==========================================
def importar_dados_antigos():
    if os.path.exists(ARQUIVO_ANTIGO):
        try:
            df_antigo = pd.read_csv(ARQUIVO_ANTIGO)
            produtos_convertidos = []
            for _, row in df_antigo.iterrows():
                produtos_convertidos.append({
                    "data": "2026-10-01",
                    "codigo": str(row.get("codigo", "SKU-001")),
                    "nome": str(row.get("nome", "Produto Antigo")),
                    "categoria": str(row.get("categoria", "Outros")),
                    "qtd_produzida": 1,
                    "pla_por_unidade": float(row.get("material", 0.0)),
                    "pla_total": float(row.get("material", 0.0)),
                    "material_extra": float(row.get("gastos_extras", 0.0)) if "gastos_extras" in row else 0.0,
                    "custo_unidade": float(row.get("producao", 0.0)) if "producao" in row else 0.0
                })
            return produtos_convertidos
        except Exception:
            return []
    return []

# Inicialização do State
if "compras" not in st.session_state:
    st.session_state["compras"] = carregar_csv(ARQUIVO_COMPRAS, {
        "data": "", "nome_material": "", "categoria": "", "cor": "", 
        "quantidade": 0.0, "unidade": "KG", "custo_total": 0.0, 
        "custo_unitario": 0.0, "nota_fiscal": "", "fornecedor": ""
    })

if "producao" not in st.session_state:
    dados_iniciais_prod = carregar_csv(ARQUIVO_PRODUCAO, {"data": "", "codigo": "", "nome": "", "categoria": "", "qtd_produzida": 0, "pla_por_unidade": 0.0, "pla_total": 0.0, "material_extra": 0.0, "custo_unidade": 0.0})
    if not dados_iniciais_prod:
        dados_iniciais_prod = importar_dados_antigos()
    st.session_state["producao"] = dados_iniciais_prod

if "vendas" not in st.session_state:
    st.session_state["vendas"] = carregar_csv(ARQUIVO_VENDAS, {"data": "", "codigo": "", "nome": "", "qtd_vendida": 0, "valor_total": 0.0})

# Estados de Edição
if "edit_idx_compra" not in st.session_state:
    st.session_state["edit_idx_compra"] = None
if "edit_idx_producao" not in st.session_state:
    st.session_state["edit_idx_producao"] = None
if "edit_idx_venda" not in st.session_state:
    st.session_state["edit_idx_venda"] = None

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Home"

categorias_lista = ["PLA", "TAG", "Papelaria", "Decoração", "Utilitários", "Acessórios", "Outros"]

def renderizar_cabecalho(titulo):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <div class="header-catalogo-container">
            <h2 class="header-titulo-catalogo">EITA — {titulo}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("⬅️ MENU", use_container_width=True):
            st.session_state["pagina_atual"] = "Home"
            st.rerun()

# ==========================================
# MENU LATERAL
# ==========================================
with st.sidebar:
    st.title("💡 EITA Ateliê")
    if st.button("🏠 Início", use_container_width=True):
        st.session_state["pagina_atual"] = "Home"
        st.rerun()
    if st.button("🛒 Compras (Entradas)", use_container_width=True):
        st.session_state["pagina_atual"] = "Compras"
        st.session_state["edit_idx_compra"] = None
        st.rerun()
    if st.button("📦 Estoque de Materiais", use_container_width=True):
        st.session_state["pagina_atual"] = "EstoqueMateriais"
        st.rerun()
    if st.button("⚙️ Produção", use_container_width=True):
        st.session_state["pagina_atual"] = "Producao"
        st.session_state["edit_idx_producao"] = None
        st.rerun()
    if st.button("🏷️ Produtos Acabados", use_container_width=True):
        st.session_state["pagina_atual"] = "ProdutosProntos"
        st.rerun()
    if st.button("💸 Vendas (Saídas)", use_container_width=True):
        st.session_state["pagina_atual"] = "Vendas"
        st.session_state["edit_idx_venda"] = None
        st.rerun()

# ==========================================
# TELA INICIAL
# ==========================================
if st.session_state["pagina_atual"] == "Home":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #103b57; font-size: 45px;'>EITA ATELIÊ DE IDEIAS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #C5A059; font-size: 18px;'>Sistema Integrado de Estoque, Produção e Vendas</p>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🛒 CADASTRAR COMPRA", use_container_width=True):
            st.session_state["pagina_atual"] = "Compras"
            st.session_state["edit_idx_compra"] = None
            st.rerun()
        if st.button("📦 ESTOQUE DE MATERIAIS", use_container_width=True):
            st.session_state["pagina_atual"] = "EstoqueMateriais"
            st.rerun()
    with c2:
        if st.button("⚙️ REGISTRAR PRODUÇÃO", use_container_width=True):
            st.session_state["pagina_atual"] = "Producao"
            st.session_state["edit_idx_producao"] = None
            st.rerun()
        if st.button("🏷️ PRODUTOS PRONTOS", use_container_width=True):
            st.session_state["pagina_atual"] = "ProdutosProntos"
            st.rerun()
    with c3:
        if st.button("💸 REGISTRAR VENDA", use_container_width=True):
            st.session_state["pagina_atual"] = "Vendas"
            st.session_state["edit_idx_venda"] = None
            st.rerun()

# ==========================================
# ABA 1: COMPRAS DE MATERIAIS
# ==========================================
elif st.session_state["pagina_atual"] == "Compras":
    edit_idx = st.session_state["edit_idx_compra"]
    is_edit_compra = edit_idx is not None
    titulo_compra = "EDITAR COMPRA" if is_edit_compra else "CADASTRO DE COMPRAS"
    
    renderizar_cabecalho(titulo_compra)
    st.markdown("---")

    item_compra_atual = st.session_state["compras"][edit_idx] if is_edit_compra else {}

    with st.form("form_compra"):
        col1, col2 = st.columns(2)
        with col1:
            data_compra = st.date_input("Data da Compra")
            nome_material = st.text_input("Nome do Material (ex: Filamento PLA)", value=item_compra_atual.get("nome_material", "")).strip()
            
            cat_atual = item_compra_atual.get("categoria", categorias_lista[0])
            cat_idx = categorias_lista.index(cat_atual) if cat_atual in categorias_lista else 0
            categoria = st.selectbox("Categoria", categorias_lista, index=cat_idx)
            
            cor = st.text_input("Cor / Variante (ex: Branco)", value=item_compra_atual.get("cor", "")).strip().upper()
            quantidade = st.number_input("Quantidade Comprada", min_value=0.01, step=1.0, value=float(item_compra_atual.get("quantidade", 1.0)))
            
            unidades_disponiveis = ["KG", "UN", "METROS", "PCT", "G"]
            un_atual = item_compra_atual.get("unidade", "KG")
            un_idx = unidades_disponiveis.index(un_atual) if un_atual in unidades_disponiveis else 0
            unidade = st.selectbox("Unidade", unidades_disponiveis, index=un_idx)

        with col2:
            nota_fiscal = st.text_input("Número da Nota Fiscal / Pedido", value=item_compra_atual.get("nota_fiscal", "")).strip()
            
            fornecedores_lista = ["Amazon", "Online", "Loja física", "Outro"]
            forn_atual = item_compra_atual.get("fornecedor", "Amazon")
            forn_idx = fornecedores_lista.index(forn_atual) if forn_atual in fornecedores_lista else 3
            
            fornecedor_opcao = st.selectbox("Fornecedor", fornecedores_lista, index=forn_idx if forn_idx < 3 else 3)
            if fornecedor_opcao == "Outro" or forn_atual not in fornecedores_lista:
                fornecedor = st.text_input("Digite o nome do fornecedor", value=forn_atual if forn_atual not in fornecedores_lista else "").strip()
            else:
                fornecedor = fornecedor_opcao

            custo_total = st.number_input("Custo Total da Compra (€)", min_value=0.0, step=0.50, format="%.2f", value=float(item_compra_atual.get("custo_total", 0.0)))
            
            # Cálculo automático conforme regra solicitada:
            # Se KG -> divide o custo total por (quantidade * 1000) para achar o custo por grama, ou se a quantidade já estiver em KG, custo_total / (quantidade * 1000)
            # Se UN -> custo_total / quantidade
            if unidade == "KG" and quantidade > 0:
                custo_unitario_sugerido = custo_total / (quantidade * 1000) # Custo por grama
                rotulo_custo_unit = "Custo por Grama (€/g)"
            elif unidade == "UN" and quantidade > 0:
                custo_unitario_sugerido = custo_total / quantidade # Custo por unidade
                rotulo_custo_unit = "Custo por Unidade (€/un)"
            else:
                custo_unitario_sugerido = custo_total / quantidade if quantidade > 0 else 0.0
                rotulo_custo_unit = "Custo Unitário / por Grama (€)"

            custo_unit_val = float(item_compra_atual.get("custo_unitario", custo_unitario_sugerido))
            custo_unitario = st.number_input(rotulo_custo_unit, min_value=0.0, value=custo_unit_val, step=0.001, format="%.4f")

        btn_texto = "Salvar Alterações da Compra" if is_edit_compra else "Salvar Compra e Atualizar Estoque"
        submitted = st.form_submit_button(btn_texto)
        
        if submitted:
            if not nome_material or not cor:
                st.error("Por favor, preencha o Nome do Material e a Cor/Variante.")
            else:
                nova_compra = {
                    "data": str(data_compra),
                    "nome_material": nome_material,
                    "categoria": categoria,
                    "cor": cor,
                    "quantidade": float(quantidade),
                    "unidade": unidade,
                    "custo_total": float(custo_total),
                    "custo_unitario": float(custo_unitario),
                    "nota_fiscal": nota_fiscal,
                    "fornecedor": fornecedor
                }
                if is_edit_compra:
                    st.session_state["compras"][edit_idx] = nova_compra
                    st.session_state["edit_idx_compra"] = None
                    msg = "Compra atualizada com sucesso!"
                else:
                    st.session_state["compras"].append(nova_compra)
                    msg = "Compra registrada com sucesso!"
                
                salvar_csv(ARQUIVO_COMPRAS, st.session_state["compras"], msg)
                st.success(msg)
                time.sleep(1)
                st.rerun()

    if is_edit_compra:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_compra"] = None
            st.rerun()

    st.markdown("### 📋 Histórico de Compras (Gerenciar Itens)")
    if st.session_state["compras"]:
        for idx, compra in enumerate(st.session_state["compras"]):
            with st.expander(f"🛒 [{compra.get('data')}] {compra.get('nome_material')} - {compra.get('cor')} ({compra.get('quantidade')} {compra.get('unidade')}) - € {compra.get('custo_total'):.2f}"):
                c_info1, c_info2, c_btn1, c_btn2 = st.columns([2, 2, 1, 1])
                with c_info1:
                    st.write(f"**Categoria:** {compra.get('categoria')}")
                    st.write(f"**Fornecedor:** {compra.get('fornecedor')}")
                    st.write(f"**Nota Fiscal:** {compra.get('nota_fiscal')}")
                with c_info2:
                    st.write(f"**Custo Total:** € {compra.get('custo_total'):.2f}")
                    tipo_custo = "por Grama" if compra.get('unidade') == 'KG' else "por Unidade"
                    st.write(f"**Custo {tipo_custo}:** € {compra.get('custo_unitario'):.4f}")
                with c_btn1:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✏️ Editar", key=f"edit_compra_{idx}"):
                        st.session_state["edit_idx_compra"] = idx
                        st.rerun()
                with c_btn2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Excluir", key=f"del_compra_{idx}"):
                        st.session_state["compras"].pop(idx)
                        salvar_csv(ARQUIVO_COMPRAS, st.session_state["compras"], "Compra excluída")
                        st.success("Compra removida com sucesso!")
                        time.sleep(1)
                        st.rerun()

# ==========================================
# ABA 2: ESTOQUE DE MATERIAIS CONSOLIDADO
# ==========================================
elif st.session_state["pagina_atual"] == "EstoqueMateriais":
    renderizar_cabecalho("ESTOQUE DE MATERIAIS CONSOLIDADO")
    st.markdown("---")
    st.markdown("O sistema consolida automaticamente compras da mesma categoria e cor, somando as quantidades e recalculando os custos.")

    if not st.session_state["compras"]:
        st.info("Nenhuma compra registrada ainda.")
    else:
        df_c = pd.DataFrame(st.session_state["compras"])
        df_agrupado = df_c.groupby(["categoria", "cor", "unidade"], as_index=False).agg({
            "quantidade": "sum",
            "custo_total": "sum"
        })
        # Recalcular a média ponderada do custo unitário/por grama de forma correta
        df_agrupado["Custo Unitário / por Grama Médio (€)"] = df_agrupado.apply(
            lambda r: (r["custo_total"] / (r["quantidade"] * 1000)) if r["unidade"] == "KG" and r["quantidade"] > 0 
            else (r["custo_total"] / r["quantidade"] if r["quantidade"] > 0 else 0), axis=1
        )

        st.dataframe(df_agrupado, use_container_width=True)

# ==========================================
# ABA 3: PRODUÇÃO DIÁRIA
# ==========================================
elif st.session_state["pagina_atual"] == "Producao":
    edit_idx_p = st.session_state["edit_idx_producao"]
    is_edit_prod = edit_idx_p is not None
    titulo_prod = "EDITAR PRODUÇÃO" if is_edit_prod else "REGISTRO DE PRODUÇÃO"

    renderizar_cabecalho(titulo_prod)
    st.markdown("---")

    item_prod_atual = st.session_state["producao"][edit_idx_p] if is_edit_prod else {}

    with st.form("form_producao"):
        col1, col2 = st.columns(2)
        with col1:
            data_prod = st.date_input("Data da Produção")
            codigo_prod = st.text_input("Código do Produto (SKU)", value=item_prod_atual.get("codigo", "")).strip().upper()
            nome_prod = st.text_input("Nome do Produto", value=item_prod_atual.get("nome", "")).strip()
            
            cat_p_atual = item_prod_atual.get("categoria", categorias_lista[0])
            cat_p_idx = categorias_lista.index(cat_p_atual) if cat_p_atual in categorias_lista else 0
            categoria_prod = st.selectbox("Categoria", categorias_lista, index=cat_p_idx)
        with col2:
            qtd_produzida = st.number_input("Quantidade Produzida (unidades)", min_value=1, step=1, value=int(item_prod_atual.get("qtd_produzida", 1)))
            pla_por_uni = st.number_input("Consumo de PLA por Unidade (gramas)", min_value=0.0, step=1.0, value=float(item_prod_atual.get("pla_por_unidade", 0.0)))
            material_extra = st.number_input("Material Extra Utilizado (TAGs, argolas, etc.)", min_value=0.0, step=1.0, value=float(item_prod_atual.get("material_extra", 0.0)))
            custo_uni = st.number_input("Custo Unitário de Produção (€)", min_value=0.0, step=0.10, value=float(item_prod_atual.get("custo_unidade", 0.0)))

        btn_txt_p = "Salvar Alterações da Produção" if is_edit_prod else "Registrar Produção e Baixar Estoque"
        submitted_prod = st.form_submit_button(btn_txt_p)
        
        if submitted_prod:
            if not codigo_prod or not nome_prod:
                st.error("Preencha o código e o nome do produto.")
            else:
                pla_total = pla_por_uni * qtd_produzida
                nova_prod = {
                    "data": str(data_prod),
                    "codigo": codigo_prod,
                    "nome": nome_prod,
                    "categoria": categoria_prod,
                    "qtd_produzida": int(qtd_produzida),
                    "pla_por_unidade": float(pla_por_uni),
                    "pla_total": float(pla_total),
                    "material_extra": float(material_extra),
                    "custo_unidade": float(custo_uni)
                }
                if is_edit_prod:
                    st.session_state["producao"][edit_idx_p] = nova_prod
                    st.session_state["edit_idx_producao"] = None
                    msg_p = "Produção atualizada com sucesso!"
                else:
                    st.session_state["producao"].append(nova_prod)
                    msg_p = "Produção registrada com sucesso!"

                salvar_csv(ARQUIVO_PRODUCAO, st.session_state["producao"], msg_p)
                st.success(msg_p)
                time.sleep(1)
                st.rerun()

    if is_edit_prod:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_producao"] = None
            st.rerun()

    st.markdown("### 📋 Histórico de Produção (Gerenciar Itens)")
    if st.session_state["producao"]:
        for idx, prod in enumerate(st.session_state["producao"]):
            with st.expander(f"⚙️ [{prod.get('data')}] {prod.get('codigo')} — {prod.get('nome')} (Qtd: {prod.get('qtd_produzida')})"):
                c_info1, c_info2, c_btn1, c_btn2 = st.columns([2, 2, 1, 1])
                with c_info1:
                    st.write(f"**Categoria:** {prod.get('categoria')}")
                    st.write(f"**PLA por Unidade:** {prod.get('pla_por_unidade')}g")
                    st.write(f"**PLA Total:** {prod.get('pla_total')}g")
                with c_info2:
                    st.write(f"**Material Extra:** {prod.get('material_extra')}")
                    st.write(f"**Custo Unit