import streamlit as st
import pandas as pd
import os
from datetime import date

# Configuração da Página
st.set_page_config(page_title="Gestão EITA", page_icon="🖨️", layout="wide")

# Caminhos dos arquivos e pastas
PASTA_IMAGENS = "imagens"
ARQUIVO_CATALOGO = "catalogo_produtos.csv"
ARQUIVO_ANTIGO = "produtos_3d.csv"
ARQUIVO_COMPRAS = "compras_insumos.csv"
ARQUIVO_PRODUCAO = "producao_lotes.csv"

os.makedirs(PASTA_IMAGENS, exist_ok=True)

# Categorias oficiais e separadas
categorias_produtos_lista = ["Decoração", "Utilidades", "Acessórios", "Natal", "Laços", "Outros"]

# ==========================================
# GERENCIAMENTO DE ESTADO E CARREGAMENTO
# ==========================================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Início"

if "mostrar_tabela_compras" not in st.session_state:
    st.session_state["mostrar_tabela_compras"] = True

if "mostrar_tabela_producao" not in st.session_state:
    st.session_state["mostrar_tabela_producao"] = True

if "edit_idx_catalogo" not in st.session_state:
    st.session_state["edit_idx_catalogo"] = None

def normalizar_categoria(cat_str):
    """Padroniza e mapeia corretamente as categorias existentes"""
    c = str(cat_str).strip().lower()
    if "decor" in c:
        return "Decoração"
    elif "util" in c:
        return "Utilidades"
    elif "acess" in c:
        return "Acessórios"
    elif "natal" in c:
        return "Natal"
    elif "laç" in c or "lac" in c:
        return "Laços"
    else:
        return "Outros"

# Carregamento inteligente com mapeamento corrigido
if "catalogo" not in st.session_state:
    lista_carregada = []
    
    if os.path.exists(ARQUIVO_CATALOGO):
        try:
            df_cat = pd.read_csv(ARQUIVO_CATALOGO)
            for _, r in df_cat.iterrows():
                cat_nome = normalizar_categoria(r.get("categoria", "Outros"))
                lista_carregada.append({
                    "codigo": str(r.get("codigo", "SKU-001")),
                    "nome": str(r.get("nome", "Produto")),
                    "categoria": cat_nome,
                    "gramas_pla": float(r.get("gramas_pla", r.get("material", 0.0))),
                    "horas_imp": float(r.get("horas_imp", r.get("tempo", 0.0))),
                    "extras": str(r.get("extras", "Nenhum")),
                    "preco_calculado": float(r.get("preco_calculado", r.get("producao", 0.0))),
                    "foto": str(r.get("foto", r.get("imagem", "")))
                })
        except:
            pass

    if not lista_carregada and os.path.exists(ARQUIVO_ANTIGO):
        try:
            df_old = pd.read_csv(ARQUIVO_ANTIGO)
            for _, r in df_old.iterrows():
                cat_nome = normalizar_categoria(r.get("categoria", "Outros"))
                lista_carregada.append({
                    "codigo": str(r.get("codigo", "SKU-001")),
                    "nome": str(r.get("nome", "Produto")),
                    "categoria": cat_nome,
                    "gramas_pla": float(r.get("material", 0.0)),
                    "horas_imp": float(r.get("tempo", 0.0)),
                    "extras": "Importado do sistema anterior",
                    "preco_calculado": float(r.get("producao", 0.0)),
                    "foto": str(r.get("imagem", ""))
                })
        except:
            pass

    st.session_state["catalogo"] = lista_carregada

# Carrega Compras
if "compras" not in st.session_state:
    if os.path.exists(ARQUIVO_COMPRAS):
        try:
            st.session_state["compras"] = pd.read_csv(ARQUIVO_COMPRAS).to_dict("records")
        except:
            st.session_state["compras"] = []
    else:
        st.session_state["compras"] = []

# Carrega Produção
if "producao" not in st.session_state:
    if os.path.exists(ARQUIVO_PRODUCAO):
        try:
            st.session_state["producao"] = pd.read_csv(ARQUIVO_PRODUCAO).to_dict("records")
        except:
            st.session_state["producao"] = []
    else:
        st.session_state["producao"] = []

def salvar_dados(caminho, dados):
    try:
        df = pd.DataFrame(dados)
        df.to_csv(caminho, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar arquivo {caminho}: {e}")

# ==========================================
# MENU LATERAL & DOWNLOAD DE ARQUIVOS
# ==========================================
st.sidebar.title("🖨️ Sistema EITA")
menu_opcoes = ["Início", "Catálogo", "Calcular", "Compras", "Produção"]
escolha_lateral = st.sidebar.radio("Navegação", menu_opcoes, index=menu_opcoes.index(st.session_state["pagina"]) if st.session_state["pagina"] in menu_opcoes else 0)

st.session_state["pagina"] = escolha_lateral

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Downloads de Arquivos")

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
botao_download(ARQUIVO_COMPRAS, "📥 Baixar Compras (CSV)")
botao_download(ARQUIVO_PRODUCAO, "📥 Baixar Produção (CSV)")

# ==========================================
# 1. PÁGINA INICIAL (HOME)
# ==========================================
if st.session_state["pagina"] == "Início":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center;'>🖨️ GESTÃO EITA</h1>", unsafe_allow_html=True)
            st.caption("<p style='text-align: center;'>Baden-Württemberg - Alemanha</p>", unsafe_allow_html=True)
        
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
# 2. CATÁLOGO DE PRODUTOS, CADASTRO E EDIÇÃO
# ==========================================
elif st.session_state["pagina"] == "Catálogo":
    edit_idx = st.session_state["edit_idx_catalogo"]
    is_editing = edit_idx is not None and edit_idx < len(st.session_state["catalogo"])
    
    titulo_pagina = "✏️ Editar Produto no Catálogo" if is_editing else "📊 Catálogo de Produtos e Novos Cadastros"
    st.markdown(f"## {titulo_pagina}")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.session_state["edit_idx_catalogo"] = None
        st.rerun()
        
    produto_em_edicao = st.session_state["catalogo"][edit_idx] if is_editing else {}

    form_titulo = "✏️ Alterar Dados do Produto" if is_editing else "➕ Cadastrar Novo Produto no Catálogo"
    st.markdown(f"### {form_titulo}")
    
    with st.form("form_catalogo_crud"):
        col_cad1, col_cad2 = st.columns(2)
        
        with col_cad1:
            nome_prod = st.text_input("Nome do Produto", value=produto_em_edicao.get("nome", ""), placeholder="Ex: Chaveiro Personalizado")
            
            cat_atual = produto_em_edicao.get("categoria", categorias_produtos_lista[0])
            cat_idx = categorias_produtos_lista.index(cat_atual) if cat_atual in categorias_produtos_lista else 0
            categoria_prod = st.selectbox("Categoria", categorias_produtos_lista, index=cat_idx)
            
            if is_editing:
                codigo_automatico = produto_em_edicao.get("codigo", "SKU-001")
            else:
                prefixo = categoria_prod[:3].upper()
                prods_mesma_cat = [p for p in st.session_state["catalogo"] if str(p.get("categoria")).strip() == categoria_prod]
                proximo_num = len(prods_mesma_cat) + 1
                codigo_automatico = f"{prefixo}-{proximo_num:03d}"
            
            st.text_input("Código do Produto", value=codigo_automatico, disabled=True)
            
            gramas_pla = st.number_input("Gramas de PLA utilizadas", min_value=0.0, value=float(produto_em_edicao.get("gramas_pla", 30.0)), step=1.0)
            horas_imp = st.number_input("Horas de Impressão", min_value=0.0, value=float(produto_em_edicao.get("horas_imp", 2.0)), step=0.5)

        # <--- É AQUI DENTRO QUE ESSE BLOCO ENTRA (na segunda coluna) --->
        with col_cad2:
            st.markdown("##### 🔌 Extras / Componentes Opcionais")
            extras_atuais = produto_em_edicao.get("extras", "")
            
            # Bloco da Tag NFC
            usa_nfc = st.checkbox("Tag NFC", value="NFC:" in extras_atuais)
            desc_nfc = st.text_input("Detalhe Tag NFC", value="NTAG216" if usa_nfc else "") if usa_nfc else ""
            custo_nfc = st.number_input("Custo NFC (€)", min_value=0.0, value=0.30) if usa_nfc else 0.0

            # Bloco da Argola
            usa_argola = st.checkbox("Argola", value="Argola:" in extras_atuais)
            desc_argola = st.text_input("Detalhe Argola", value="12mm" if usa_argola else "") if usa_argola else ""
            custo_argola = st.number_input("Custo Argola (€)", min_value=0.0, value=0.10) if usa_argola else 0.0

            # Bloco de Outros
            usa_outros = st.checkbox("Outros Extras", value="Outros:" in extras_atuais)
            desc_outros = st.text_input("Descrição de Outros", value="" if not usa_outros else "Extra") if usa_outros else ""
            custo_outros = st.number_input("Custo Outros (€)", min_value=0.0, value=0.0) if usa_outros else 0.0

            margem_lucro = st.number_input("Margem de Lucro Desejada (%)", min_value=0.0, value=100.0, step=10.0)

            st.markdown("##### 📸 Foto do Produto")
            foto_upload = st.file_uploader("Fazer Upload da Imagem", type=["jpg", "jpeg", "png"])

# ==========================================
# 3. CALCULADORA
# ==========================================
elif st.session_state["pagina"] == "Calcular":
    st.markdown("## 💰 Calculadora de Precificação")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    st.markdown("### ⚙️ Custos Base")
    col_base1, col_base2 = st.columns(2)
    with col_base1:
        preco_kg_pla = st.number_input("Valor pago por 1 KG de PLA (€)", min_value=0.0, value=20.00, step=0.50, format="%.2f")
        custo_g_pla = preco_kg_pla / 1000.0  
        st.caption(f"Custo por grama: **€ {custo_g_pla:.4f} / g**")
    with col_base2:
        custo_h_imp = st.number_input("Custo por Hora de Impressão (€/h)", min_value=0.00, value=1.00, step=0.25, format="%.2f")
        st.caption("Referência Baden-Württemberg: € 1.00 / h")
        
    st.markdown("---")
    st.markdown("### 🖨️ Simulação de Projeto")
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        gramas = st.number_input("Gramas de PLA usadas", min_value=0.0, value=50.0, step=1.0)
        horas = st.number_input("Horas de Impressão", min_value=0.0, value=3.0, step=0.5)
        
        st.markdown("##### 🔌 Extras")
        usa_nfc = st.checkbox("Tag NFC (Calc)")
        qtd_nfc = st.number_input("Qtd NFC", min_value=1, value=1, key="qn") if usa_nfc else 0
        custo_nfc = st.number_input("Custo unitário NFC (€)", min_value=0.0, value=0.30, key="cn") if usa_nfc else 0.0
        
    with col_calc2:
        usa_argola = st.checkbox("Argola (Calc)")
        qtd_argola = st.number_input("Qtd Argolas", min_value=1, value=1, key="qa") if usa_argola else 0
        custo_argola = st.number_input("Custo unitário Argola (€)", min_value=0.0, value=0.10, key="ca") if usa_argola else 0.0
        
        usa_outros = st.checkbox("Outros (Calc)")
        desc_outros = st.text_input("Descrição Outros", placeholder="Ex: Embalagem", key="do") if usa_outros else ""
        outros_custos = st.number_input("Valor Outros (€)", min_value=0.0, value=0.0, key="vo") if usa_outros else 0.0
        
        margem = st.number_input("Margem de Lucro (%)", min_value=0.0, value=100.0, step=10.0)

    custo_pla = gramas * custo_g_pla
    custo_horas = horas * custo_h_imp
    custo_total = custo_pla + custo_horas + (qtd_nfc * custo_nfc) + (qtd_argola * custo_argola) + outros_custos
    preco_venda = custo_total * (1 + (margem / 100))
    
    st.markdown("---")
    st.markdown("### 📊 Resultado")
    r1, r2 = st.columns(2)
    with r1:
        st.metric(label="Custo Total", value=f"€ {custo_total:.2f}")
    with r2:
        st.metric(label="Preço Sugerido", value=f"€ {preco_venda:.2f}")

# ==========================================
# 4. COMPRAS
# ==========================================
elif st.session_state["pagina"] == "Compras":
    st.markdown("## 🛒 Cadastro de Compras de Insumos")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    with st.form("form_compra_detalhada"):
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            material = st.selectbox("Material", ["PLA", "Argolas", "NFC", "OUTROS"])
            data_compra = st.date_input("Data da Compra", value=date.today())
            variedade = st.text_input("Variedade (Cor / Modelo / Marca)", placeholder="Ex: Azul Seda, 12mm, NTAG216")
            
        with col_c2:
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                qtd = st.number_input("Quantidade", min_value=0.01, value=1.0, step=1.0)
            with col_q2:
                unidade_medida = st.selectbox("Unidade", ["KG", "Unidades", "Gramas", "Metros"])
                
            valor_compra = st.number_input("Valor da Compra (€)", min_value=0.0, value=20.0, step=1.0)
            identificacao_nota = st.text_input("Identificação da Nota (NF / Fatura)", placeholder="Ex: NF-12345")
            
        if st.form_submit_button("Salvar Compra"):
            nova_compra = {
                "material": material,
                "data_compra": str(data_compra),
                "variedade": variedade,
                "quantidade": qtd,
                "unidade": unidade_medida,
                "valor_compra": valor_compra,
                "identificacao_nota": identificacao_nota
            }
            st.session_state["compras"].append(nova_compra)
            salvar_dados(ARQUIVO_COMPRAS, st.session_state["compras"])
            st.success("Compra cadastrada com sucesso!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📋 Ver / Ocultar Compras Salvas"):
        st.session_state["mostrar_tabela_compras"] = not st.session_state["mostrar_tabela_compras"]

    if st.session_state["mostrar_tabela_compras"]:
        st.markdown("### 📦 Histórico de Compras")
        if not st.session_state["compras"]:
            st.info("Nenhuma compra registrada.")
        else:
            st.dataframe(pd.DataFrame(st.session_state["compras"]), use_container_width=True)
            if st.button("🗑️ Apagar Última Compra"):
                st.session_state["compras"].pop()
                salvar_dados(ARQUIVO_COMPRAS, st.session_state["compras"])
                st.success("Removido!")
                st.rerun()

# ==========================================
# 5. PRODUÇÃO
# ==========================================
elif st.session_state["pagina"] == "Produção":
    st.markdown("## ⚙️ Registro de Produção de Lotes")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    if not st.session_state["catalogo"]:
        st.warning("⚠️ Cadastre produtos no Catálogo primeiro para poder registrar lotes de produção.")
    else:
        nomes_produtos = [p["nome"] for p in st.session_state["catalogo"]]
        produto_escolhido = st.selectbox("Selecione o Produto do Catálogo", nomes_produtos)
        
        prod_atual = next((p for p in st.session_state["catalogo"] if p["nome"] == produto_escolhido), {})
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            codigo_prod = prod_atual.get("codigo", "SKU-000")
            st.text_input("Código", value=codigo_prod, disabled=True)
            categoria_prod = prod_atual.get("categoria", "Outros")
            st.text_input("Categoria", value=categoria_prod, disabled=True)
            quantidade_lote = st.number_input("Quantidade no Lote", min_value=1, value=1, step=1)
            data_producao = st.date_input("Data da Produção", value=date.today())
            
        with col_p2:
            preco_unit = float(prod_atual.get("preco_calculado", 0.0))
            st.metric(label="Preço Unitário Calculado", value=f"€ {preco_unit:.2f}")
            st.metric(label="Valor Total do Lote", value=f"€ {preco_unit * quantidade_lote:.2f}")
            
            foto_p = str(prod_atual.get("foto", ""))
            if foto_p and os.path.exists(foto_p):
                st.image(foto_p, width=150, caption=produto_escolhido)
            else:
                st.caption("Sem foto.")
                
        if st.button("💾 Salvar Lote Produzido"):
            nova_prod = {
                "codigo": codigo_prod,
                "nome_produto": produto_escolhido,
                "categoria": categoria_prod,
                "quantidade": quantidade_lote,
                "data_producao": str(data_producao),
                "valor_total_lote": round(preco_unit * quantidade_lote, 2)
            }
            st.session_state["producao"].append(nova_prod)
            salvar_dados(ARQUIVO_PRODUCAO, st.session_state["producao"])
            st.success("Produção registrada com sucesso!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📋 Ver / Ocultar Histórico de Produção"):
        st.session_state["mostrar_tabela_producao"] = not st.session_state["mostrar_tabela_producao"]

    if st.session_state["mostrar_tabela_producao"]:
        st.markdown("### 📦 Lotes Produzidos")
        if not st.session_state["producao"]:
            st.info("Nenhum lote registrado.")
        else:
            st.dataframe(pd.DataFrame(st.session_state["producao"]), use_container_width=True)
            if st.button("🗑️ Apagar Último Registro"):
                st.session_state["producao"].pop()
                salvar_dados(ARQUIVO_PRODUCAO, st.session_state["producao"])
                st.success("Removido!")
                st.rerun()