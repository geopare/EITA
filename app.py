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
ARQUIVO_CATALOGO = "catalogo_produtos.csv"
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
                # Calcula horas e minutos aproximados com base na coluna 'tempo'
                tempo_total = float(row.get("tempo", 0.0))
                horas = int(tempo_total)
                minutos = int(round((tempo_total - horas) * 60))
                
                produtos_convertidos.append({
                    "codigo": str(row.get("codigo", "SKU-001")),
                    "nome": str(row.get("nome", "Produto Antigo")),
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
                    "foto": str(row.get("imagem", ""))  # Pega o caminho exato da imagem do arquivo antigo!
                })
            return produtos_convertidos
        except Exception as e:
            st.error(f"Erro ao importar dados antigos: {e}")
            return []
    return []

# Inicialização do State
if "compras" not in st.session_state:
    st.session_state["compras"] = carregar_csv(ARQUIVO_COMPRAS, {
        "data": "", "nome_material": "", "tipo_material": "PLA", "cor": "", 
        "quantidade": 0.0, "unidade": "KG", "custo_total": 0.0, 
        "nota_fiscal": "", "fornecedor": ""
    })

if "catalogo" not in st.session_state:
    dados_iniciais_cat = carregar_csv(ARQUIVO_CATALOGO, {"codigo": "", "nome": "", "categoria": "", "insumos": "", "custo_estimado": 0.0})
    if not dados_iniciais_cat:
        dados_iniciais_cat = importar_dados_antigos()
    st.session_state["catalogo"] = dados_iniciais_cat

if "producao" not in st.session_state:
    st.session_state["producao"] = carregar_csv(ARQUIVO_PRODUCAO, {"data": "", "codigo": "", "nome": "", "categoria": "", "qtd_produzida": 0, "detalhes_insumos": "", "custo_unidade": 0.0})

if "vendas" not in st.session_state:
    st.session_state["vendas"] = carregar_csv(ARQUIVO_VENDAS, {"data": "", "codigo": "", "nome": "", "qtd_vendida": 0, "valor_total": 0.0})

# Estados de Edição
if "edit_idx_compra" not in st.session_state:
    st.session_state["edit_idx_compra"] = None
if "edit_idx_catalogo" not in st.session_state:
    st.session_state["edit_idx_catalogo"] = None
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
        st.rerun()
    if st.button("📦 Estoque de Materiais", use_container_width=True):
        st.session_state["pagina_atual"] = "EstoqueMateriais"
        st.rerun()
    if st.button("🏷️ Produtos (Catálogo)", use_container_width=True):
        st.session_state["pagina_atual"] = "ProdutosCatalogo"
        st.rerun()
    if st.button("⚙️ Produção", use_container_width=True):
        st.session_state["pagina_atual"] = "Producao"
        st.rerun()
    if st.button("📦 Produtos Prontos (Estoque)", use_container_width=True):
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
        if st.button("🏷️ CADASTRO DE PRODUTOS", use_container_width=True):
            st.session_state["pagina_atual"] = "ProdutosCatalogo"
            st.rerun()
        if st.button("⚙️ REGISTRAR PRODUÇÃO", use_container_width=True):
            st.session_state["pagina_atual"] = "Producao"
            st.rerun()
    with c3:
        if st.button("📦 PRODUTOS PRONTOS", use_container_width=True):
            st.session_state["pagina_atual"] = "ProdutosProntos"
            st.rerun()
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
            data_compra = st.date_input("Data da Compra")
            nome_material = st.text_input("Nome do Material (ex: Filamento Branco, Argola)").strip()
            tipo_material = st.selectbox("Tipo do Material", tipos_materiais_lista)
            cor = st.text_input("Cor / Variante (ex: Branco)").strip().upper()
            quantidade = st.number_input("Quantidade Comprada", min_value=0.01, step=1.0)
            unidade = st.selectbox("Unidade", ["KG", "UN", "METROS", "PCT", "G"])
        with col2:
            nota_fiscal = st.text_input("Número da Nota Fiscal / Pedido").strip()
            fornecedor_opcao = st.selectbox("Fornecedor", ["Amazon", "Online", "Loja física", "Outro"])
            fornecedor = st.text_input("Nome do Fornecedor").strip() if fornecedor_opcao == "Outro" else fornecedor_opcao
            custo_total = st.number_input("Custo Total da Compra (€)", min_value=0.0, step=0.50, format="%.2f")

        if st.form_submit_button("Salvar Compra e Atualizar Estoque"):
            if not nome_material or not cor:
                st.error("Preencha o Nome do Material e a Cor.")
            else:
                nova_compra = {
                    "data": str(data_compra), "nome_material": nome_material, "tipo_material": tipo_material,
                    "cor": cor, "quantidade": float(quantidade), "unidade": unidade,
                    "custo_total": float(custo_total), "nota_fiscal": nota_fiscal, "fornecedor": fornecedor
                }
                st.session_state["compras"].append(nova_compra)
                salvar_csv(ARQUIVO_COMPRAS, st.session_state["compras"], "Nova compra cadastrada")
                st.success("Compra registrada com sucesso!")
                time.sleep(1)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Botão para exibir/ocultar o histórico de compras sob demanda
    if "mostrar_historico_compras" not in st.session_state:
        st.session_state["mostrar_historico_compras"] = False

    if st.button("📋 Ver Histórico de Compras Cadastradas"):
        st.session_state["mostrar_historico_compras"] = not st.session_state["mostrar_historico_compras"]

    if st.session_state["mostrar_historico_compras"]:
        st.markdown("### Histórico de Compras")
        if st.session_state["compras"]:
            for idx, compra in enumerate(st.session_state["compras"]):
                titulo_expander = f"🛒 [{compra.get('data')}] ({compra.get('tipo_material')}) {compra.get('nome_material')} - {compra.get('cor')} ({compra.get('quantidade')} {compra.get('unidade')})"
                with st.expander(titulo_expander):
                    st.write(f"• **Fornecedor:** {compra.get('fornecedor')}")
                    st.write(f"• **Nota Fiscal:** {compra.get('nota_fiscal')}")
                    st.write(f"• **Custo Total:** € {compra.get('custo_total'):.2f}")
                    if st.button("🗑️ Excluir Compra", key=f"del_compra_{idx}"):
                        st.session_state["compras"].pop(idx)
                        salvar_csv(ARQUIVO_COMPRAS, st.session_state["compras"], "Compra excluída")
                        st.rerun()
        else:
            st.info("Nenhuma compra registrada ainda.")

# ==========================================
# ABA 2: ESTOQUE DE MATERIAIS CONSOLIDADO
# ==========================================
elif st.session_state["pagina_atual"] == "EstoqueMateriais":
    renderizar_cabecalho("ESTOQUE DE MATERIAIS CONSOLIDADO")
    st.markdown("---")
    if not st.session_state["compras"]:
        st.info("Nenhuma compra registrada ainda.")
    else:
        df_c = pd.DataFrame(st.session_state["compras"])
        df_agrupado = df_c.groupby(["tipo_material", "nome_material", "cor", "unidade"], as_index=False).agg({"quantidade": "sum", "custo_total": "sum"})
        df_agrupado["Custo Unitário Médio (€)"] = df_agrupado["custo_total"] / df_agrupado["quantidade"]
        st.dataframe(df_agrupado, use_container_width=True)

# ==========================================
# ABA 3: CATÁLOGO DE PRODUTOS (O que a EITA faz)
# ==========================================
elif st.session_state["pagina_atual"] == "ProdutosCatalogo":
    edit_idx_cat = st.session_state["edit_idx_catalogo"]
    is_edit_cat = edit_idx_cat is not None
    renderizar_cabecalho("EDITAR PRODUTO" if is_edit_cat else "CADASTRO DE PRODUTOS (CATÁLOGO)")
    st.markdown("---")

    item_cat_atual = st.session_state["catalogo"][edit_idx_cat] if is_edit_cat else {}

    # Mapear custo médio de PLA, NFC e Argolas com base nas Compras
    custo_g_pla = 0.025  # Valor padrão (€ 0,025/g ~ € 25/kg)
    custo_unit_nfc = 0.30  
    custo_unit_argola = 0.10  

    if st.session_state["compras"]:
        df_comp = pd.DataFrame(st.session_state["compras"])
        
        pla_comp = df_comp[df_comp["tipo_material"].str.upper() == "PLA"]
        if not pla_comp.empty and pla_comp["quantidade"].sum() > 0:
            total_g = pla_comp.apply(lambda r: r["quantidade"] * 1000 if str(r["unidade"]).upper() == "KG" else r["quantidade"], axis=1).sum()
            if total_g > 0:
                custo_g_pla = pla_comp["custo_total"].sum() / total_g

        nfc_comp = df_comp[df_comp["tipo_material"].str.upper() == "NFC"]
        if not nfc_comp.empty and nfc_comp["quantidade"].sum() > 0:
            custo_unit_nfc = nfc_comp["custo_total"].sum() / nfc_comp["quantidade"].sum()

        arg_comp = df_comp[df_comp["tipo_material"].str.upper() == "ARGOLA"]
        if not arg_comp.empty and arg_comp["quantidade"].sum() > 0:
            custo_unit_argola = arg_comp["custo_total"].sum() / arg_comp["quantidade"].sum()

    with st.form("form_catalogo"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_prod = st.text_input("Nome do Produto", value=item_cat_atual.get("nome", "")).strip()
            
            cat_atual = item_cat_atual.get("categoria", categorias_produtos_lista[0])
            cat_idx = categorias_produtos_lista.index(cat_atual) if cat_atual in categorias_produtos_lista else 0
            categoria_prod = st.selectbox("Categoria", categorias_produtos_lista, index=cat_idx)

            prefixo = categoria_prod[:3].upper()
            prods_cat = [p for p in st.session_state["catalogo"] if p.get("categoria") == categoria_prod]
            proximo_numero = len(prods_cat) + 1 if not is_edit_cat else int(item_cat_atual.get("codigo", f"{prefixo}-000").split("-")[-1])
            codigo_auto = item_cat_atual.get("codigo") if is_edit_cat else f"{prefixo}-{proximo_numero:03d}"

            st.text_input("Código do Produto (Gerado Automático)", value=codigo_auto, disabled=True)

            c_h, c_m = st.columns(2)
            with c_h:
                horas_imp = st.number_input("Horas de Impressão", min_value=0, max_value=72, value=int(item_cat_atual.get("horas_imp", 0)), step=1)
            with c_m:
                minutos_imp = st.number_input("Minutos de Impressão", min_value=0, max_value=59, value=int(item_cat_atual.get("minutos_imp", 0)), step=5)

            gramas_pla = st.number_input("Peso de PLA (Gramas)", min_value=0.0, step=1.0, value=float(item_cat_atual.get("gramas_pla", 0.0)))

        with col2:
            st.markdown("##### 🔌 Acessórios e Extras Opcionais")
            usar_argola = st.checkbox("Incluir Argola de Chaveiro", value=item_cat_atual.get("usar_argola", False))
            qtd_argola = st.number_input("Qtd. Argolas", min_value=1, step=1, value=int(item_cat_atual.get("qtd_argola", 1))) if usar_argola else 0

            usar_nfc = st.checkbox("Incluir Tag NFC", value=item_cat_atual.get("usar_nfc", False))
            qtd_nfc = st.number_input("Qtd. Tags NFC", min_value=1, step=1, value=int(item_cat_atual.get("qtd_nfc", 1))) if usar_nfc else 0

            st.markdown("##### 📸 Imagem do Produto")
            
            tipo_foto_opcao = st.radio("Origem da Imagem", ["Fazer Upload de Nova", "Escolher Foto Já Salva"], horizontal=True)
            
            upload_foto = None
            foto_selecionada_existente = ""

            imagens_existentes = [f for f in os.listdir(PASTA_IMAGENS) if f.lower().endswith(('png', 'jpg', 'jpeg'))] if os.path.exists(PASTA_IMAGENS) else []

            if tipo_foto_opcao == "Fazer Upload de Nova":
                upload_foto = st.file_uploader("Selecione um arquivo de imagem", type=["jpg", "jpeg", "png"])
            else:
                if imagens_existentes:
                    foto_escolhida = st.selectbox("Selecione uma foto já cadastrada", imagens_existentes)
                    foto_selecionada_existente = os.path.join(PASTA_IMAGENS, foto_escolhida)
                else:
                    st.info("Nenhuma foto salva anteriormente na pasta.")

            custo_pla_calc = gramas_pla * custo_g_pla
            custo_arg_calc = qtd_argola * custo_unit_argola
            custo_nfc_calc = qtd_nfc * custo_unit_nfc
            custo_total_est = custo_pla_calc + custo_arg_calc + custo_nfc_calc

            st.markdown(f"**Custo Estimado do Produto:** € {custo_total_est:.2f}")

        btn_txt = "Salvar Alterações no Produto" if is_edit_cat else "Cadastrar Produto no Catálogo"
        if st.form_submit_button(btn_txt):
            if not nome_prod:
                st.error("Preencha o Nome do Produto.")
            else:
                caminho_foto = item_cat_atual.get("foto", "")
                if tipo_foto_opcao == "Fazer Upload de Nova" and upload_foto is not None:
                    ext = upload_foto.name.split(".")[-1]
                    caminho_foto = os.path.join(PASTA_IMAGENS, f"{codigo_auto}.{ext}")
                    with open(caminho_foto, "wb") as f:
                        f.write(upload_foto.getbuffer())
                elif tipo_foto_opcao == "Escolher Foto Já Salva" and foto_selecionada_existente:
                    caminho_foto = foto_selecionada_existente

                insumos_detalhe = [f"{gramas_pla:.0f}g PLA"]
                if usar_argola:
                    insumos_detalhe.append(f"{qtd_argola}x Argola")
                if usar_nfc:
                    insumos_detalhe.append(f"{qtd_nfc}x Tag NFC")

                novo_item_cat = {
                    "codigo": codigo_auto,
                    "nome": nome_prod,
                    "categoria": categoria_prod,
                    "horas_imp": int(horas_imp),
                    "minutos_imp": int(minutos_imp),
                    "gramas_pla": float(gramas_pla),
                    "usar_argola": usar_argola,
                    "qtd_argola": int(qtd_argola),
                    "usar_nfc": usar_nfc,
                    "qtd_nfc": int(qtd_nfc),
                    "insumos": ", ".join(insumos_detalhe),
                    "custo_estimado": float(custo_total_est),
                    "foto": caminho_foto
                }

                if is_edit_cat:
                    st.session_state["catalogo"][edit_idx_cat] = novo_item_cat
                    st.session_state["edit_idx_catalogo"] = None
                    msg = "Produto atualizado no catálogo!"
                else:
                    st.session_state["catalogo"].append(novo_item_cat)
                    msg = "Produto cadastrado no catálogo!"

                salvar_csv(ARQUIVO_CATALOGO, st.session_state["catalogo"], msg)
                st.success(msg)
                time.sleep(1)
                st.rerun()

    if is_edit_cat:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_catalogo"] = None
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if "mostrar_produtos_catalogo" not in st.session_state:
        st.session_state["mostrar_produtos_catalogo"] = False

    if st.button("📋 Ver Produtos Cadastrados no Catálogo"):
        st.session_state["mostrar_produtos_catalogo"] = not st.session_state["mostrar_produtos_catalogo"]

    if st.session_state["mostrar_produtos_catalogo"]:
        st.markdown("### 📋 Seus Produtos Cadastrados por Categoria")
        if not st.session_state["catalogo"]:
            st.info("Nenhum produto cadastrado no catálogo ainda.")
        else:
            for cat in categorias_produtos_lista:
                prods_cat_lista = [(i, p) for i, p in enumerate(st.session_state["catalogo"]) if p.get("categoria") == cat]
                if prods_cat_lista:
                    with st.expander(f"📁 **{cat}** ({len(prods_cat_lista)} produtos)"):
                        for idx, prod in prods_cat_lista:
                            st.markdown(f"**🏷️ [{prod.get('codigo')}] {prod.get('nome')}**")
                            col_detalhes, col_img = st.columns([3, 1])
                            with col_detalhes:
                                st.write(f"• **Tempo de Impressão:** {prod.get('horas_imp', 0)}h {prod.get('minutos_imp', 0)}min")
                                st.write(f"• **Peso de PLA:** {prod.get('gramas_pla', 0)} g")
                                st.write(f"• **Insumos:** {prod.get('insumos')}")
                                st.write(f"• **Custo Estimado:** € {float(prod.get('custo_estimado', 0.0)):.2f}")
                            
                            with col_img:
                                foto_path = str(prod.get("foto", ""))
                                codigo_prod = str(prod.get("codigo", ""))
                                foto_encontrada = ""
                                
                                tentativas = []
                                if foto_path:
                                    tentativas.append(foto_path)
                                    if not foto_path.startswith("imagens/"):
                                        tentativas.append(os.path.join(PASTA_IMAGENS, foto_path))
                                
                                if codigo_prod:
                                    for ext in ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"]:
                                        tentativas.append(os.path.join(PASTA_IMAGENS, f"{codigo_prod}.{ext}"))
                                        tentativas.append(os.path.join(PASTA_IMAGENS, f"{codigo_prod.lower()}.{ext}"))

                                for t in tentativas:
                                    if t and os.path.exists(t):
                                        foto_encontrada = t
                                        break

                                if foto_encontrada:
                                    st.image(foto_encontrada, use_container_width=True)
                                else:
                                    st.caption("Sem foto")
                                
                                # Lista de possíveis caminhos onde a foto pode estar
                                tentativas = []
                                if foto_path:
                                    tentativas.append(foto_path)
                                    # Se o caminho salvo não tiver a pasta 'imagens/', tenta adicionar
                                    if not foto_path.startswith("imagens/"):
                                        tentativas.append(os.path.join(PASTA_IMAGENS, foto_path))
                                
                                # Tenta buscar direto pelo código do produto com várias extensões
                                for ext in ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"]:
                                    tentativas.append(os.path.join(PASTA_IMAGENS, f"{codigo_prod}.{ext}"))
                                    tentativas.append(os.path.join(PASTA_IMAGENS, f"{codigo_prod.lower()}.{ext}"))

                                # Testa cada tentativa até achar um arquivo que realmente exista no disco
                                for t in tentativas:
                                    if t and os.path.exists(t):
                                        foto_encontrada = t
                                        break

                                if foto_encontrada:
                                    st.image(foto_encontrada, use_container_width=True)
                                else:
                                    st.caption("Sem foto")

                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("✏️ Editar", key=f"edit_cat_{idx}"):
                                    st.session_state["edit_idx_catalogo"] = idx
                                    st.rerun()
                            with c2:
                                if st.button("🗑️ Excluir", key=f"del_cat_{idx}"):
                                    st.session_state["catalogo"].pop(idx)
                                    salvar_csv(ARQUIVO_CATALOGO, st.session_state["catalogo"], "Produto excluído do catálogo")
                                    st.rerun()
                            st.markdown("---")
# ==========================================
# ABA 4: PRODUÇÃO DIÁRIA
# ==========================================
elif st.session_state["pagina_atual"] == "Producao":
    renderizar_cabecalho("REGISTRAR PRODUÇÃO")
    data_prod = st.date_input("Data da Produção")
    st.markdown("---")

    if not st.session_state["catalogo"]:
        st.warning("Cadastre primeiro os produtos na aba **Produtos (Catálogo)** antes de registrar uma produção.")
    else:
        # Criar mapa do catálogo para seleção rápida
        catalogo_map = {f"{c['codigo']} — {c['nome']} ({c['categoria']})": c for c in st.session_state["catalogo"]}

        with st.form("form_producao"):
            produto_escolhido_combo = st.selectbox("Escolha o Produto que vai produzir agora", list(catalogo_map.keys()))
            prod_info = catalogo_map[produto_escolhido_combo]

            st.info(f"📋 **Insumos cadastrados para este produto:** {prod_info.get('insumos', 'Nenhum')}")

            qtd_produzida = st.number_input("Quantidade que está produzindo agora (unidades)", min_value=1, step=1, value=1)
            custo_unit_final = st.number_input("Custo Unitário (€)", min_value=0.0, step=0.10, value=float(prod_info.get("custo_estimado", 0.0)))

            if st.form_submit_button("Confirmar Produção e Dar Baixa nos Insumos"):
                # Registrar a produção realizada
                nova_producao = {
                    "data": str(data_prod),
                    "codigo": prod_info["codigo"],
                    "nome": prod_info["nome"],
                    "categoria": prod_info["categoria"],
                    "qtd_produzida": int(qtd_produzida),
                    "detalhes_insumos": prod_info.get("insumos", ""),
                    "custo_unidade": float(custo_unit_final)
                }
                st.session_state["producao"].append(nova_producao)
                salvar_csv(ARQUIVO_PRODUCAO, st.session_state["producao"], "Nova produção registrada")
                st.success("Produção registrada com sucesso e estoque pronto atualizado!")
                time.sleep(1)
                st.rerun()

    st.markdown("### 📋 Histórico de Produção por Categoria")
    if not st.session_state["producao"]:
        st.info("Nenhuma produção registrada até o momento.")
    else:
        for cat in categorias_produtos_lista:
            prods_cat = [(i, p) for i, p in enumerate(st.session_state["producao"]) if p.get("categoria") == cat]
            if prods_cat:
                with st.expander(f"📁 **{cat}** ({len(prods_cat)} registros)"):
                    for idx_p, prod in prods_cat:
                        st.markdown(f"**[{prod.get('data')}] {prod.get('codigo')} — {prod.get('nome')}** (Qtd: {prod.get('qtd_produzida')} un.)")
                        st.write(f"• Insumos: {prod.get('detalhes_insumos')}")
                        st.write(f"• Custo Unitário: € {float(prod.get('custo_unidade', 0.0)):.2f}")
                        if st.button("🗑️ Excluir Produção", key=f"del_prod_{idx_p}"):
                            st.session_state["producao"].pop(idx_p)
                            salvar_csv(ARQUIVO_PRODUCAO, st.session_state["producao"], "Produção excluída")
                            st.rerun()
                        st.markdown("---")

# ==========================================
# ABA 5: PRODUTOS PRONTOS (ESTOQUE)
# ==========================================
elif st.session_state["pagina_atual"] == "ProdutosProntos":
    renderizar_cabecalho("PRODUTOS PRONTOS EM ESTOQUE")
    st.markdown("---")
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
# ABA 6: VENDAS (SAÍDAS)
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

        opcoes_venda = {f"{row['codigo']} — {row['nome']} (Disponível: {int(row['disponivel'])})": row for _, row in estoque_atual.iterrows() if row["disponivel"] > 0}

        if not opcoes_venda:
            st.info("Não há produtos com estoque disponível para venda.")
        else:
            with st.form("form_venda"):
                data_venda = st.date_input("Data da Venda")
                produto_escolhido_chave = st.selectbox("Selecione o Produto", list(opcoes_venda.keys()))
                prod_selecionado = opcoes_venda[produto_escolhido_chave]
                
                qtd_vendida = st.number_input("Quantidade Vendida", min_value=1, max_value=int(prod_selecionado["disponivel"]), step=1)
                preco_venda_unit = st.number_input("Preço de Venda Unitário (€)", min_value=0.0, value=float(prod_selecionado["custo_unidade"] * 2), step=0.50)

                if st.form_submit_button("Confirmar Venda e Dar Baixa"):
                    nova_venda = {
                        "data": str(data_venda), "codigo": prod_selecionado["codigo"],
                        "nome": prod_selecionado["nome"], "qtd_vendida": int(qtd_vendida),
                        "valor_total": float(qtd_vendida * preco_venda_unit)
                    }
                    st.session_state["vendas"].append(nova_venda)
                    salvar_csv(ARQUIVO_VENDAS, st.session_state["vendas"], "Venda registrada")
                    st.success("Venda registrada com sucesso!")
                    time.sleep(1)
                    st.rerun()

    st.markdown("### 📋 Histórico de Vendas")
    if st.session_state["vendas"]:
        for idx, venda in enumerate(st.session_state["vendas"]):
            with st.expander(f"💸 [{venda.get('data')}] {venda.get('codigo')} — {venda.get('nome')} (Qtd: {venda.get('qtd_vendida')}) - € {venda.get('valor_total'):.2f}"):
                if st.button("🗑️ Excluir Venda", key=f"del_venda_{idx}"):
                    st.session_state["vendas"].pop(idx)
                    salvar_csv(ARQUIVO_VENDAS, st.session_state["vendas"], "Venda excluída")
                    st.rerun()