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
    st.session_state["compras"] = carregar_csv(ARQUIVO_COMPRAS, {"categoria": "", "cor": "", "quantidade": 0.0, "unidade": "KG", "custo_total": 0.0, "fornecedor": ""})

if "producao" not in st.session_state:
    dados_iniciais_prod = carregar_csv(ARQUIVO_PRODUCAO, {"data": "", "codigo": "", "nome": "", "categoria": "", "qtd_produzida": 0, "pla_por_unidade": 0.0, "pla_total": 0.0, "material_extra": 0.0, "custo_unidade": 0.0})
    if not dados_iniciais_prod:
        dados_iniciais_prod = importar_dados_antigos()
    st.session_state["producao"] = dados_iniciais_prod

if "vendas" not in st.session_state:
    st.session_state["vendas"] = carregar_csv(ARQUIVO_VENDAS, {"data": "", "codigo": "", "nome": "", "qtd_vendida": 0, "valor_total": 0.0})

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
        st.rerun()
    if st.button("📦 Estoque de Materiais", use_container_width=True):
        st.session_state["pagina_atual"] = "EstoqueMateriais"
        st.rerun()
    if st.button("⚙️ Produção", use_container_width=True):
        st.session_state["pagina_atual"] = "Producao"
        st.rerun()
    if st.button("🏷️ Produtos Acabados", use_container_width=True):
        st.session_state["pagina_atual"] = "ProdutosProntos"
        st.rerun()
    if st.button("💸 Vendas (Saídas)", use_container_width=True):
        st.session_state["pagina_atual"] = "Vendas"
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
    renderizar_cabecalho("CADASTRO DE COMPRAS")
    st.markdown("---")

    with st.form("form_compra"):
        col1, col2 = st.columns(2)
        with col1:
            categoria = st.selectbox("Categoria", categorias_lista)
            cor = st.text_input("Cor / Variante (ex: Branco, Azul Silk, 3D Hojor)").strip().upper()
            quantidade = st.number_input("Quantidade Comprada", min_value=0.01, step=1.0)
        with col2:
            unidade = st.selectbox("Unidade Base", ["KG", "UN", "METROS", "PCT"])
            custo_total = st.number_input("Custo Total (€ ou R$)", min_value=0.0, step=0.50)
            fornecedor = st.text_input("Fornecedor").strip()

        submitted = st.form_submit_button("Salvar Compra e Atualizar Estoque")
        if submitted:
            if not cor:
                st.error("Informe a cor ou variante do material.")
            else:
                nova_compra = {
                    "categoria": categoria,
                    "cor": cor,
                    "quantidade": float(quantidade),
                    "unidade": unidade,
                    "custo_total": float(custo_total),
                    "fornecedor": fornecedor
                }
                st.session_state["compras"].append(nova_compra)
                salvar_csv(ARQUIVO_COMPRAS, st.session_state["compras"], "Nova compra cadastrada")
                st.success("Compra registrada com sucesso!")
                time.sleep(1)
                st.rerun()

    st.markdown("### 📋 Histórico de Compras")
    if st.session_state["compras"]:
        df_compras = pd.DataFrame(st.session_state["compras"])
        st.dataframe(df_compras, use_container_width=True)

# ==========================================
# ABA 2: ESTOQUE DE MATERIAIS CONSOLIDADO
# ==========================================
elif st.session_state["pagina_atual"] == "EstoqueMateriais":
    renderizar_cabecalho("ESTOQUE DE MATERIAIS CONSOLIDADO")
    st.markdown("---")
    st.markdown("O sistema consolida automaticamente compras da mesma categoria e cor, somando as quantidades e recalculando os custos médios.")

    if not st.session_state["compras"]:
        st.info("Nenhuma compra registrada ainda.")
    else:
        df_c = pd.DataFrame(st.session_state["compras"])
        df_agrupado = df_c.groupby(["categoria", "cor", "unidade"], as_index=False).agg({
            "quantidade": "sum",
            "custo_total": "sum"
        })
        df_agrupado["Custo Unitário Médio"] = df_agrupado["custo_total"] / df_agrupado["quantidade"]

        st.dataframe(df_agrupado, use_container_width=True)

# ==========================================
# ABA 3: PRODUÇÃO DIÁRIA
# ==========================================
elif st.session_state["pagina_atual"] == "Producao":
    renderizar_cabecalho("REGISTRO DE PRODUÇÃO")
    st.markdown("---")

    with st.form("form_producao"):
        col1, col2 = st.columns(2)
        with col1:
            data_prod = st.date_input("Data da Produção")
            codigo_prod = st.text_input("Código do Produto (SKU)").strip().upper()
            nome_prod = st.text_input("Nome do Produto").strip()
            categoria_prod = st.selectbox("Categoria", categorias_lista)
        with col2:
            qtd_produzida = st.number_input("Quantidade Produzida (unidades)", min_value=1, step=1)
            pla_por_uni = st.number_input("Consumo de PLA por Unidade (gramas)", min_value=0.0, step=1.0)
            material_extra = st.number_input("Material Extra Utilizado (TAGs, argolas, etc.)", min_value=0.0, step=1.0)
            custo_uni = st.number_input("Custo Unitário de Produção (€)", min_value=0.0, step=0.10)

        submitted_prod = st.form_submit_button("Registrar Produção e Baixar Estoque")
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
                st.session_state["producao"].append(nova_prod)
                salvar_csv(ARQUIVO_PRODUCAO, st.session_state["producao"], "Nova produção registrada")
                st.success("Produção registrada e materiais abatidos do estoque!")
                time.sleep(1)
                st.rerun()

    st.markdown("### 📋 Histórico de Produção")
    if st.session_state["producao"]:
        st.dataframe(pd.DataFrame(st.session_state["producao"]), use_container_width=True)

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

        estoque_final["Valor Total em Estoque"] = estoque_final["Estoque Atual"] * estoque_final["custo_unidade"]

        st.dataframe(estoque_final[["codigo", "nome", "categoria", "Estoque Atual", "custo_unidade", "Valor Total em Estoque"]], use_container_width=True)

# ==========================================
# ABA 5: VENDAS (SAÍDAS)
# ==========================================
elif st.session_state["pagina_atual"] == "Vendas":
    renderizar_cabecalho("REGISTRAR VENDAS")
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
            estoque_atual["disponivel"] = estoque_atual["qtd_produzida"]

        opcoes_venda = {
            f"{row['codigo']} — {row['nome']} (Disponível: {int(row['disponivel'])})": row 
            for _, row in estoque_atual.iterrows() if row["disponivel"] > 0
        }

        if not opcoes_venda:
            st.info("Não há produtos com estoque disponível para venda no momento.")
        else:
            with st.form("form_venda"):
                data_venda = st.date_input("Data da Venda")
                produto_escolhido_chave = st.selectbox("Selecione o Produto", list(opcoes_venda.keys()))
                prod_selecionado = opcoes_venda[produto_escolhido_chave]
                
                qtd_vendida = st.number_input("Quantidade Vendida", min_value=1, max_value=int(prod_selecionado["disponivel"]), step=1)
                preco_venda_unit = st.number_input("Preço de Venda Unitário (€)", min_value=0.0, value=float(prod_selecionado["custo_unidade"] * 2), step=0.50)

                submitted_venda = st.form_submit_button("Confirmar Venda e Dar Baixa")
                if submitted_venda:
                    nova_venda = {
                        "data": str(data_venda),
                        "codigo": prod_selecionado["codigo"],
                        "nome": prod_selecionado["nome"],
                        "qtd_vendida": int(qtd_vendida),
                        "valor_total": float(qtd_vendida * preco_venda_unit)
                    }
                    st.session_state["vendas"].append(nova_venda)
                    salvar_csv(ARQUIVO_VENDAS, st.session_state["vendas"], "Venda registrada com baixa de estoque")
                    st.success("Venda registrada e estoque atualizado com sucesso!")
                    time.sleep(1)
                    st.rerun()

    st.markdown("### 📋 Histórico de Vendas")
    if st.session_state["vendas"]:
        st.dataframe(pd.DataFrame(st.session_state["vendas"]), use_container_width=True)