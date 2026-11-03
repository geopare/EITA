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
                    "detalhes_insumos": f"PLA: {float(row.get('material', 0.0))}g",
                    "custo_unidade": float(row.get("producao", 0.0)) if "producao" in row else 0.0
                })
            return produtos_convertidos
        except Exception:
            return []
    return []

# Inicialização do State
if "compras" not in st.session_state:
    st.session_state["compras"] = carregar_csv(ARQUIVO_COMPRAS, {
        "data": "", "nome_material": "", "tipo_material": "PLA", "cor": "", 
        "quantidade": 0.0, "unidade": "KG", "custo_total": 0.0, 
        "nota_fiscal": "", "fornecedor": ""
    })

if "producao" not in st.session_state:
    dados_iniciais_prod = carregar_csv(ARQUIVO_PRODUCAO, {"data": "", "codigo": "", "nome": "", "categoria": "", "qtd_produzida": 0, "detalhes_insumos": "", "custo_unidade": 0.0})
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

tipos_materiais_lista = ["PLA", "TAG", "Argola", "NFC", "Papelaria", "Embalagem", "Outros"]
categorias_produtos_lista = ["Decoração", "Utilitários", "Miniaturas", "Chaveiros", "Acessórios", "Organização", "Natal", "Religiao", "Outros"]

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
            st.rerun()
        if st.button("📦 ESTOQUE DE MATERIAIS", use_container_width=True):
            st.session_state["pagina_atual"] = "EstoqueMateriais"
            st.rerun()
    with c2:
        if st.button("⚙️ REGISTRAR PRODUÇÃO", use_container_width=True):
            st.session_state["pagina_atual"] = "Producao"
            st.rerun()
        if st.button("🏷️ PRODUTOS PRONTOS", use_container_width=True):
            st.session_state["pagina_atual"] = "ProdutosProntos"
            st.rerun()
    with c3:
        if st.button("💸 REGISTRAR VENDA", use_container_width=True):
            st.session_state["pagina_atual"] = "Vendas"
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
            nome_material = st.text_input("Nome do Material (ex: Filamento Branco, Argola)", value=item_compra_atual.get("nome_material", "")).strip()
            
            tipo_atual = item_compra_atual.get("tipo_material", tipos_materiais_lista[0])
            tipo_idx = tipos_materiais_lista.index(tipo_atual) if tipo_atual in tipos_materiais_lista else 0
            tipo_material = st.selectbox("Tipo do Material", tipos_materiais_lista, index=tipo_idx)
            
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

        submitted = st.form_submit_button("Salvar Compra e Atualizar Estoque")
        if submitted:
            if not nome_material or not cor:
                st.error("Por favor, preencha o Nome do Material e a Cor/Variante.")
            else:
                nova_compra = {
                    "data": str(data_compra),
                    "nome_material": nome_material,
                    "tipo_material": tipo_material,
                    "cor": cor,
                    "quantidade": float(quantidade),
                    "unidade": unidade,
                    "custo_total": float(custo_total),
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
            with st.expander(f"🛒 [{compra.get('data')}] ({compra.get('tipo_material')}) {compra.get('nome_material')} - {compra.get('cor')} ({compra.get('quantidade')} {compra.get('unidade')}) - € {compra.get('custo_total'):.2f}"):
                c_info1, c_info2, c_btn1, c_btn2 = st.columns([2, 2, 1, 1])
                with c_info1:
                    st.write(f"**Tipo:** {compra.get('tipo_material')}")
                    st.write(f"**Fornecedor:** {compra.get('fornecedor')}")
                    st.write(f"**Nota Fiscal:** {compra.get('nota_fiscal')}")
                with c_info2:
                    st.write(f"**Custo Total:** € {compra.get('custo_total'):.2f}")
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
    st.markdown("O sistema consolida automaticamente compras do mesmo material, tipo e cor, somando as quantidades e os custos totais.")

    if not st.session_state["compras"]:
        st.info("Nenhuma compra registrada ainda.")
    else:
        df_c = pd.DataFrame(st.session_state["compras"])
        df_agrupado = df_c.groupby(["tipo_material", "nome_material", "cor", "unidade"], as_index=False).agg({
            "quantidade": "sum",
            "custo_total": "sum"
        })
        df_agrupado["Custo Unitário Médio (€)"] = df_agrupado["custo_total"] / df_agrupado["quantidade"]

        st.dataframe(df_agrupado, use_container_width=True)

# ==========================================
# ABA 3: PRODUÇÃO DIÁRIA (MÚLTIPLOS INSUMOS)
# ==========================================
elif st.session_state["pagina_atual"] == "Producao":
    edit_idx_p = st.session_state["edit_idx_producao"]
    is_edit_prod = edit_idx_p is not None
    titulo_prod = "EDITAR PRODUÇÃO" if is_edit_prod else "REGISTRO DE PRODUÇÃO"

    renderizar_cabecalho(titulo_prod)
    st.markdown("---")

    item_prod_atual = st.session_state["producao"][edit_idx_p] if is_edit_prod else {}

    # Obter lista de produtos únicos já produzidos anteriormente (Catálogo de Referência)
    df_producao_existente = pd.DataFrame(st.session_state["producao"]) if st.session_state["producao"] else pd.DataFrame()
    catalogo_produtos = {}
    if not df_producao_existente.empty and "codigo" in df_producao_existente.columns:
        for _, r in df_producao_existente.drop_duplicates(subset=["codigo"]).iterrows():
            label_prod = f"{r.get('codigo')} — {r.get('nome')} ({r.get('categoria')})"
            catalogo_produtos[label_prod] = r

    # Mapear materiais disponíveis no estoque
    materiais_estoque_map = {}
    if st.session_state["compras"]:
        df_comp = pd.DataFrame(st.session_state["compras"])
        df_comp_ag = df_comp.groupby(["tipo_material", "nome_material", "unidade"], as_index=False).agg({"quantidade": "sum", "custo_total": "sum"})
        df_comp_ag["custo_unit"] = df_comp_ag["custo_total"] / df_comp_ag["quantidade"]
        for _, r in df_comp_ag.iterrows():
            chave = f"[{r['tipo_material']}] {r['nome_material']} (Disp: {r['quantidade']:.1f} {r['unidade']})"
            materiais_estoque_map[chave] = {
                "tipo": r["tipo_material"],
                "nome": r["nome_material"],
                "unidade": r["unidade"],
                "custo_unit": float(r["custo_unit"]) if r["quantidade"] > 0 else 0.0
            }

    with st.form("form_producao"):
        col1, col2 = st.columns(2)
        with col1:
            data_prod = st.date_input("Data da Produção")
            
            # Escolha clara entre usar um produto já cadastrado no catálogo ou criar um novo
            origem_cadastro = st.radio("Produto", ["Cadastrar novo produto", "Selecionar do catálogo de produtos"], horizontal=True)
            
            codigo_prod = ""
            nome_prod = ""
            cat_p_atual = categorias_produtos_lista[0]
            
            if origem_cadastro == "Selecionar do catálogo de produtos" and catalogo_produtos:
                prod_escolhido_combo = st.selectbox("Escolha o Produto Existente", list(catalogo_produtos.keys()))
                dados_sel = catalogo_produtos[prod_escolhido_combo]
                
                codigo_prod = dados_sel.get("codigo")
                nome_prod = dados_sel.get("nome")
                cat_p_atual = dados_sel.get("categoria")
                
                st.markdown(f"<div style='padding: 10px; background-color: #F8F9FA; border-left: 4px solid #103b57; border-radius: 4px;'><b>Produto Selecionado:</b> {codigo_prod} — {nome_prod}</div>", unsafe_allow_html=True)
            else:
                codigo_prod = st.text_input("Código do Produto (SKU)", value=item_prod_atual.get("codigo", "")).strip().upper()
                nome_prod = st.text_input("Nome do Produto", value=item_prod_atual.get("nome", "")).strip()
                cat_p_atual = item_prod_atual.get("categoria", categorias_produtos_lista[0])

            cat_p_idx = categorias_produtos_lista.index(cat_p_atual) if cat_p_atual in categorias_produtos_lista else 0
            categoria_prod = st.selectbox("Categoria do Produto", categorias_produtos_lista, index=cat_p_idx)
            qtd_produzida = st.number_input("Quantidade Produzida (unidades)", min_value=1, step=1, value=int(item_prod_atual.get("qtd_produzida", 1)))

        with col2:
            st.markdown("##### 🧪 Composição de Insumos (Por Unidade Produzida)")
            st.markdown("Selecione os materiais do estoque que entram na fabricação de **1 unidade**:")
            
            materiais_escolhidos_para_baixa = []
            custo_total_calculado_unitario = 0.0

            if materiais_estoque_map:
                opcoes_materiais = ["Nenhum"] + list(materiais_estoque_map.keys())
                
                mat_1 = st.selectbox("Insumo 1 (ex: PLA)", opcoes_materiais, index=0)
                qtd_1 = st.number_input("Qtd Insumo 1 por Unidade", min_value=0.0, step=1.0, value=0.0)

                mat_2 = st.selectbox("Insumo 2 (ex: Argola)", opcoes_materiais, index=0)
                qtd_2 = st.number_input("Qtd Insumo 2 por Unidade", min_value=0.0, step=1.0, value=0.0)

                mat_3 = st.selectbox("Insumo 3 (ex: NFC / Tag)", opcoes_materiais, index=0)
                qtd_3 = st.number_input("Qtd Insumo 3 por Unidade", min_value=0.0, step=1.0, value=0.0)

                for mat_sel, q_sel in [(mat_1, qtd_1), (mat_2, qtd_2), (mat_3, qtd_3)]:
                    if mat_sel != "Nenhum" and q_sel > 0:
                        info_mat = materiais_estoque_map[mat_sel]
                        custo_item = info_mat["custo_unit"] * q_sel
                        custo_total_calculado_unitario += custo_item
                        materiais_escolhidos_para_baixa.append({
                            "nome": info_mat["nome"],
                            "unidade": info_mat["unidade"],
                            "qtd_por_unidade": q_sel
                        })
            else:
                st.warning("Cadastre compras de materiais primeiro.")

            custo_uni = st.number_input("Custo Unitário Final (€)", min_value=0.0, step=0.10, value=float(item_prod_atual.get("custo_unidade", custo_total_calculado_unitario)))

        btn_txt_p = "Salvar Alterações da Produção" if is_edit_prod else "Registrar Produção e Baixar Insumos"
        submitted_prod = st.form_submit_button(btn_txt_p)
        
        if submitted_prod:
            if not codigo_prod or not nome_prod:
                st.error("Preencha o código e o nome do produto.")
            else:
                texto_insumos_resumo = ", ".join([f"{item['qtd_por_unidade']} {item['unidade']} de {item['nome']}" for item in materiais_escolhidos_para_baixa]) if materiais_escolhidos_para_baixa else "Insumos manuais"

                # Dar baixa no estoque para cada insumo utilizado proporcionalmente à quantidade produzida
                for item in materiais_escolhidos_para_baixa:
                    qtd_total_baixa = item["qtd_por_unidade"] * qtd_produzida
                    nova_baixa = {
                        "data": str(data_prod),
                        "nome_material": item["nome"],
                        "tipo_material": "CONSUMO",
                        "cor": "GERAL",
                        "quantidade": -qtd_total_baixa,
                        "unidade": item["unidade"],
                        "custo_total": 0.0,
                        "nota_fiscal": f"Prod {codigo_prod}",
                        "fornecedor": "Consumo Interno"
                    }
                    st.session_state["compras"].append(nova_baixa)
                
                if materiais_escolhidos_para_baixa:
                    salvar_csv(ARQUIVO_COMPRAS, st.session_state["compras"], "Baixa de múltiplos insumos na produção")

                nova_prod = {
                    "data": str(data_prod),
                    "codigo": codigo_prod,
                    "nome": nome_prod,
                    "categoria": categoria_prod,
                    "qtd_produzida": int(qtd_produzida),
                    "detalhes_insumos": texto_insumos_resumo,
                    "custo_unidade": float(custo_uni)
                }
                
                if is_edit_prod:
                    st.session_state["producao"][edit_idx_p] = nova_prod
                    st.session_state["edit_idx_producao"] = None
                    msg_p = "Produção atualizada com sucesso!"
                else:
                    st.session_state["producao"].append(nova_prod)
                    msg_p = "Produção registrada com baixa de insumos!"

                salvar_csv(ARQUIVO_PRODUCAO, st.session_state["producao"], msg_p)
                st.success(msg_p)
                time.sleep(1)
                st.rerun()

    if is_edit_prod:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_producao"] = None
            st.rerun()

    st.markdown("### 📋 Histórico de Produção por Categoria")
    if not st.session_state["producao"]:
        st.info("Nenhuma produção registrada até o momento.")
    else:
        for cat in categorias_produtos_lista:
            prods_desta_cat = [(idx_g, p) for idx_g, p in enumerate(st.session_state["producao"]) if p.get("categoria") == cat]
            
            if prods_desta_cat:
                with st.expander(f"📁 **{cat}** ({len(prods_desta_cat)} registros)"):
                    for idx_global, prod in prods_desta_cat:
                        st.markdown(f"**[{prod.get('data')}] {prod.get('codigo')} — {prod.get('nome')}** (Qtd: {prod.get('qtd_produzida')} un.)")
                        c_info1, c_info2, c_btn1, c_btn2 = st.columns([2, 2, 1, 1])
                        with c_info1:
                            st.write(f"• Insumos: {prod.get('detalhes_insumos', 'N/A')}")
                        with c_info2:
                            st.write(f"• Custo Unitário: € {float(prod.get('custo_unidade', 0.0)):.2f}")
                        with c_btn1:
                            if st.button("✏️ Editar", key=f"edit_prod_{idx_global}"):
                                st.session_state["edit_idx_producao"] = idx_global
                                st.rerun()
                        with c_btn2:
                            if st.button("🗑️ Excluir", key=f"del_prod_{idx_global}"):
                                st.session_state["producao"].pop(idx_global)
                                salvar_csv(ARQUIVO_PRODUCAO, st.session_state["producao"], "Produção excluída")
                                st.success("Produção removida com sucesso!")
                                time.sleep(1)
                                st.rerun()
                        st.markdown("---")

# ==========================================
# ABA 4: PRODUTOS EM ESTOQUE (ACABADOS)
# ==========================================
elif st.session_state["pagina_atual"] == "ProdutosProntos":
    renderizar_cabecalho("PRODUTOS ACABADOS EM ESTOQUE")
    st.markdown("---")
    st.markdown("Lista consolidada de tudo o que foi produzido menos o que já foi vendido.")

    if not st.session_state["producao"]:
        st.info("Nenhum produto produzido até o momento.")
    else:
        df_prod = pd.DataFrame(st.session_state["producao"])
        df_vend = pd.DataFrame(st.session_state["vendas"]) if st.session_state["vendas"] else pd.DataFrame(columns=["codigo", "qtd_vendida"])

        estoque_produzido = df_prod.groupby(["codigo", "nome", "categoria", "custo_unidade"], as_index=False).agg({"qtd_produzida": "sum"})
        
        if not df_vend.empty and "codigo" in df_vend.columns:
            vendas_agrupadas = df_vend.groupby("codigo", as_index=False).agg({"qtd_vendida": "sum"})
            estoque_final = pd.merge(estoque_produzido, vendas_agrupadas, on="codigo", how="left").fillna(0)
            estoque_final["Estoque Atual"] = estoque_final["qtd_produzida"] - estoque_final["qtd_vendida"]
        else:
            estoque_final = estoque_produzido.copy()
            estoque_final["Estoque Atual"] = estoque_final["qtd_produzida"]

        estoque_final["Valor Total em Estoque (€)"] = estoque_final["Estoque Atual"] * estoque_final["custo_unidade"]

        st.dataframe(estoque_final[["codigo", "nome", "categoria", "Estoque Atual", "custo_unidade", "Valor Total em Estoque (€)"]], use_container_width=True)

# ==========================================
# ABA 5: VENDAS (SAÍDAS)
# ==========================================
elif st.session_state["pagina_atual"] == "Vendas":
    edit_idx_v = st.session_state["edit_idx_venda"]
    is_edit_venda = edit_idx_v is not None
    titulo_venda = "EDITAR VENDA" if is_edit_venda else "REGISTRAR VENDAS"

    renderizar_cabecalho(titulo_venda)
    st.markdown("---")

    if not st.session_state["producao"]:
        st.warning("Cadastre uma produção antes de registrar vendas.")
    else:
        df_prod = pd.DataFrame(st.session_state["producao"])
        df_vend = pd.DataFrame(st.session_state["vendas"]) if st.session_state["vendas"] else pd.DataFrame(columns=["codigo", "qtd_vendida"])
        
        prod_totais = df_prod.groupby(["codigo", "nome", "custo_unidade"], as_index=False).agg({"qtd_produzida": "sum"})
        if not df_vend.empty and "codigo" in df_vend.columns:
            vendas_totais = df_vend.groupby("codigo", as_index=False).agg({"qtd_vendida": "sum"})
            estoque_atual = pd.merge(prod_totais, vendas_totais, on="codigo", how="left").fillna(0)
            estoque_atual["disponivel"] = estoque_atual["qtd_produzida"] - estoque_atual["qtd_vendida"]
        else:
            estoque_atual = prod_totais.copy()
            estoque_atual["disponivel"] = estoque_atual["qtd_produz_ida"] if "qtd_produz_ida" in estoque_atual else estoque_atual["qtd_produzida"]

        opcoes_venda = {
            f"{row['codigo']} — {row['nome']} (Disponível: {int(row['disponivel'])})": row 
            for _, row in estoque_atual.iterrows() if row["disponivel"] > 0
        }

        if not opcoes_venda and not is_edit_venda:
            st.info("Não há produtos com estoque disponível para venda no momento.")
        else:
            item_venda_atual = st.session_state["vendas"][edit_idx_v] if is_edit_venda else {}

            with st.form("form_venda"):
                data_venda = st.date_input("Data da Venda")
                
                chaves_opcoes = list(opcoes_venda.keys())
                default_idx = 0
                if is_edit_venda:
                    codigo_editando = item_venda_atual.get("codigo")
                    for idx_op, ch in enumerate(chaves_opcoes):
                        if codigo_editando in ch:
                            default_idx = idx_op
                            break

                produto_escolhido_chave = st.selectbox("Selecione o Produto", chaves_opcoes, index=default_idx)
                prod_selecionado = opcoes_venda[produto_escolhido_chave]
                
                qtd_venda_atual = int(item_venda_atual.get("qtd_vendida", 1))
                limite_max = int(prod_selecionado["disponivel"]) + (qtd_venda_atual if is_edit_venda else 0)
                
                qtd_vendida = st.number_input("Quantidade Vendida", min_value=1, max_value=limite_max, step=1, value=qtd_venda_atual)
                
                preco_sugerido = float(item_venda_atual.get("valor_total", prod_selecionado["custo_unidade"] * 2)) / qtd_venda_atual if is_edit_venda else float(prod_selecionado["custo_unidade"] * 2)
                preco_venda_unit = st.number_input("Preço de Venda Unitário (€)", min_value=0.0, value=preco_sugerido, step=0.50)

                btn_txt_v = "Salvar Alterações da Venda" if is_edit_venda else "Confirmar Venda e Dar Baixa"
                submitted_venda = st.form_submit_button(btn_txt_v)
                
                if submitted_venda:
                    nova_venda = {
                        "data": str(data_venda),
                        "codigo": prod_selecionado["codigo"],
                        "nome": prod_selecionado["nome"],
                        "qtd_vendida": int(qtd_vendida),
                        "valor_total": float(qtd_vendida * preco_venda_unit)
                    }
                    if is_edit_venda:
                        st.session_state["vendas"][edit_idx_v] = nova_venda
                        st.session_state["edit_idx_venda"] = None
                        msg_v = "Venda atualizada com sucesso!"
                    else:
                        st.session_state["vendas"].append(nova_venda)
                        msg_v = "Venda registrada com sucesso!"

                    salvar_csv(ARQUIVO_VENDAS, st.session_state["vendas"], msg_v)
                    st.success(msg_v)
                    time.sleep(1)
                    st.rerun()

    if is_edit_venda:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_venda"] = None
            st.rerun()

    st.markdown("### 📋 Histórico de Vendas (Gerenciar Itens)")
    if st.session_state["vendas"]:
        for idx, venda in enumerate(st.session_state["vendas"]):
            with st.expander(f"💸 [{venda.get('data')}] {venda.get('codigo')} — {venda.get('nome')} (Qtd: {venda.get('qtd_vendida')}) - € {venda.get('valor_total'):.2f}"):
                c_btn1, c_btn2, _ = st.columns([1, 1, 3])
                with c_btn1:
                    if st.button("✏️ Editar", key=f"edit_venda_{idx}"):
                        st.session_state["edit_idx_venda"] = idx
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ Excluir", key=f"del_venda_{idx}"):
                        st.session_state["vendas"].pop(idx)
                        salvar_csv(ARQUIVO_VENDAS, st.session_state["vendas"], "Venda excluída")
                        st.success("Venda removida com sucesso!")
                        time.sleep(1)
                        st.rerun()