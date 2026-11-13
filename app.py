import streamlit as st
import pandas as pd
import os
from datetime import date

# Configuração da Página
st.set_page_config(page_title="Gestão EITA", page_icon="🖨️", layout="wide")

# Caminhos dos arquivos e pastas
PASTA_IMAGENS = "imagens"
ARQUIVO_CATALOGO = "catalogo_produtos.csv"
ARQUIVO_COMPRAS = "compras_insumos.csv"
ARQUIVO_PRODUCAO = "producao_lotes.csv"

os.makedirs(PASTA_IMAGENS, exist_ok=True)

# Categorias oficiais fixas
categorias_produtos_lista = ["Decoração", "Utilidades", "Acessórios", "Natal", "Laços"]

def obter_prefixo_categoria(cat_str):
    c = str(cat_str).strip().lower()
    if "decor" in c or "decora" in c: return "DEC"
    elif "util" in c: return "UTI"
    elif "acess" in c: return "ACE"
    elif "natal" in c: return "NAT"
    elif "laç" in c or "lac" in c or "cha" in c: return "LAC"
    else: return "DEC"

def normalizar_categoria(cat_str):
    c = str(cat_str).strip().lower()
    if any(k in c for k in ["decor", "vaso", "planta", "decora"]): return "Decoração"
    elif any(k in c for k in ["util", "utilid"]): return "Utilidades"
    elif any(k in c for k in ["acess", "suporte"]): return "Acessórios"
    elif any(k in c for k in ["natal", "bola", "pinheiro", "noel", "vela"]): return "Natal"
    elif any(k in c for k in ["laç", "lac", "laco", "chaveiro", "cha"]): return "Laços"
    return "Decoração"

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

def carregar_catalogo():
    lista_carregada = []
    caminho_abs = os.path.abspath(ARQUIVO_CATALOGO)
    if os.path.exists(caminho_abs):
        try:
            df_cat = pd.read_csv(caminho_abs)
            df_cat.columns = [str(c).strip().lower() for c in df_cat.columns]
            
            for _, r in df_cat.iterrows():
                cat_raw = str(r.get("categoria", "Decoração"))
                cat_nome = normalizar_categoria(cat_raw)
                
                codigo = str(r.get("codigo", ""))
                if not codigo or codigo == "nan" or "-" not in codigo:
                    codigo = f"{obter_prefixo_categoria(cat_nome)}-001"

                g_pla = float(r.get("material", r.get("gramas_pla", 0.0)))
                h_imp = float(r.get("tempo", r.get("horas_imp", 0.0)))
                p_calc = float(r.get("venda", r.get("producao", 0.0)))
                foto_path = str(r.get("imagem", r.get("foto", "")))
                if foto_path == "nan": foto_path = ""

                lista_carregada.append({
                    "codigo": codigo,
                    "nome": str(r.get("nome", "Produto")),
                    "categoria": cat_nome,
                    "gramas_pla": g_pla,
                    "horas_imp": h_imp,
                    "extras": str(r.get("extras", "Nenhum")),
                    "preco_calculado": p_calc,
                    "foto": foto_path
                })
        except Exception as e:
            st.error(f"Erro ao carregar catálogo: {e}")
    return lista_carregada

if "catalogo" not in st.session_state or not st.session_state["catalogo"]:
    st.session_state["catalogo"] = carregar_catalogo()

if "compras" not in st.session_state:
    caminho_c = os.path.abspath(ARQUIVO_COMPRAS)
    if os.path.exists(caminho_c):
        try: st.session_state["compras"] = pd.read_csv(caminho_c).to_dict("records")
        except: st.session_state["compras"] = []
    else: st.session_state["compras"] = []

if "producao" not in st.session_state:
    caminho_p = os.path.abspath(ARQUIVO_PRODUCAO)
    if os.path.exists(caminho_p):
        try: st.session_state["producao"] = pd.read_csv(caminho_p).to_dict("records")
        except: st.session_state["producao"] = []
    else: st.session_state["producao"] = []

def salvar_dados_catalogo(dados):
    try:
        os.makedirs(PASTA_IMAGENS, exist_ok=True)
        dados_para_salvar = []
        for p in dados:
            dados_para_salvar.append({
                "codigo": p.get("codigo"),
                "nome": p.get("nome"),
                "categoria": p.get("categoria"),
                "tempo": p.get("horas_imp"),
                "material": p.get("gramas_pla"),
                "producao": p.get("preco_calculado") / 2.0,
                "margem": 100.0,
                "venda": p.get("preco_calculado"),
                "lucro": p.get("preco_calculado") / 2.0,
                "imagem": p.get("foto"),
                "gastos_extras": 0.0
            })
        df = pd.DataFrame(dados_para_salvar)
        caminho_abs = os.path.abspath(ARQUIVO_CATALOGO)
        df.to_csv(caminho_abs, index=False)
        st.success(f"Catálogo guardado com sucesso!")
    except Exception as e:
        st.error(f"Erro crítico ao salvar o catálogo: {e}")

# Garante arquivos iniciais
caminho_inicial_cat = os.path.abspath(ARQUIVO_CATALOGO)
if not os.path.exists(caminho_inicial_cat):
    pd.DataFrame(columns=["codigo", "nome", "categoria", "tempo", "material", "producao", "margem", "venda", "lucro", "imagem", "gastos_extras"]).to_csv(caminho_inicial_cat, index=False)

# ==========================================
# MENU LATERAL & CUSTOS BASE GLOBAIS
# ==========================================
st.sidebar.title("🖨️ Sistema EITA")
menu_opcoes = ["Início", "Catálogo", "Calcular", "Compras", "Produção"]
escolha_lateral = st.sidebar.radio("Navegação", menu_opcoes, index=menu_opcoes.index(st.session_state["pagina"]) if st.session_state["pagina"] in menu_opcoes else 0)

st.session_state["pagina"] = escolha_lateral

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Custos Base Globais")
if "global_preco_kg_pla" not in st.session_state: st.session_state["global_preco_kg_pla"] = 20.00
if "global_custo_h_imp" not in st.session_state: st.session_state["global_custo_h_imp"] = 1.00

st.session_state["global_preco_kg_pla"] = st.sidebar.number_input("Preço 1 KG PLA (€)", min_value=0.0, value=st.session_state["global_preco_kg_pla"], step=0.50, format="%.2f")
st.session_state["global_custo_h_imp"] = st.sidebar.number_input("Custo Hora Impressão (€/h)", min_value=0.0, value=st.session_state["global_custo_h_imp"], step=0.25, format="%.2f")

custo_g_pla_global = st.session_state["global_preco_kg_pla"] / 1000.0
custo_h_imp_global = st.session_state["global_custo_h_imp"]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Downloads de Arquivos")
caminho_dl = os.path.abspath(ARQUIVO_CATALOGO)
if os.path.exists(caminho_dl):
    with open(caminho_dl, "rb") as f:
        st.sidebar.download_button("📥 Baixar Catálogo (CSV)", data=f, file_name=ARQUIVO_CATALOGO, mime="text/csv")

# ==========================================
# 1. PÁGINA INICIAL (HOME)
# ==========================================
if st.session_state["pagina"] == "Início":
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
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
    
    col_vol, col_limpar = st.columns([3, 1])
    with col_vol:
        if st.button("⬅️ Voltar para a Página Inicial"):
            st.session_state["pagina"] = "Início"
            st.session_state["edit_idx_catalogo"] = None
            st.rerun()
    with col_limpar:
        if st.button("🗑️ Limpar Todo o Catálogo", type="secondary"):
            st.session_state["catalogo"] = []
            caminho_rem = os.path.abspath(ARQUIVO_CATALOGO)
            if os.path.exists(caminho_rem):
                os.remove(caminho_rem)
            st.success("Catálogo limpo com sucesso!")
            st.rerun()
        
    produto_em_edicao = st.session_state["catalogo"][edit_idx] if is_editing else {}

    form_titulo = "✏️ Alterar Dados do Produto" if is_editing else "➕ Cadastrar Novo Produto no Catálogo"
    st.markdown(f"### {form_titulo}")
    
    cat_atual = produto_em_edicao.get("categoria", categorias_produtos_lista[0])
    cat_idx = categorias_produtos_lista.index(cat_atual) if cat_atual in categorias_produtos_lista else 0
    categoria_prod = st.selectbox("Categoria", categorias_produtos_lista, index=cat_idx, key="select_cat_cadastro")
    
    if is_editing:
        codigo_automatico = produto_em_edicao.get("codigo", "SKU-001")
    else:
        prefixo = obter_prefixo_categoria(categoria_prod)
        prods_mesma_cat = [p for p in st.session_state["catalogo"] if obter_prefixo_categoria(p.get("categoria")) == prefixo]
        proximo_num = len(prods_mesma_cat) + 1
        codigo_automatico = f"{prefixo}-{proximo_num:03d}"

    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        nome_prod = st.text_input("Nome do Produto", value=produto_em_edicao.get("nome", ""), placeholder="Ex: Chaveiro Personalizado")
        st.text_input("Código Automático", value=codigo_automatico, disabled=True)
        gramas_pla = st.number_input("Gramas de PLA utilizadas", min_value=0.0, value=float(produto_em_edicao.get("gramas_pla", 30.0)), step=1.0)
        horas_imp = st.number_input("Horas de Impressão", min_value=0.0, value=float(produto_em_edicao.get("horas_imp", 2.0)), step=0.5)

    with col_cad2:
        st.markdown("##### 🔌 Extras / Componentes Opcionais")
        extras_atuais = produto_em_edicao.get("extras", "")
        
        usa_nfc = st.checkbox("Tag NFC", value="NFC:" in extras_atuais or "NTAG" in extras_atuais)
        desc_nfc = st.text_input("Detalhe Tag NFC", value="NTAG216") if usa_nfc else ""
        custo_nfc = st.number_input("Custo unitário NFC (€)", min_value=0.0, value=0.30) if usa_nfc else 0.0

        usa_argola = st.checkbox("Argola", value="Argola:" in extras_atuais or "mm" in extras_atuais)
        desc_argola = st.text_input("Detalhe Argola", value="12mm") if usa_argola else ""
        custo_argola = st.number_input("Custo unitário Argola (€)", min_value=0.0, value=0.10) if usa_argola else 0.0

        usa_outros = st.checkbox("Outros Extras", value="Outros:" in extras_atuais)
        desc_outros = st.text_input("Descrição de Outros", value="Extra") if usa_outros else ""
        custo_outros = st.number_input("Custo Outros (€)", min_value=0.0, value=0.0) if usa_outros else 0.0

        margem_lucro = st.number_input("Margem de Lucro Desejada (%)", min_value=0.0, value=100.0, step=10.0)

        st.markdown("##### 📸 Foto do Produto")
        foto_upload = st.file_uploader("Fazer Upload da Imagem", type=["jpg", "jpeg", "png"])

    c_pla_preview = gramas_pla * custo_g_pla_global
    c_horas_preview = horas_imp * custo_h_imp_global
    c_extras_preview = (custo_nfc if usa_nfc else 0.0) + (custo_argola if usa_argola else 0.0) + (custo_outros if usa_outros else 0.0)
    custo_total_preview = c_pla_preview + c_horas_preview + c_extras_preview
    preco_final_preview = custo_total_preview * (1 + (margem_lucro / 100))

    st.markdown("---")
    st.markdown("### 🏷️ Resumo de Valores em Tempo Real")
    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="⚙️ Custo de Produção", value=f"€ {custo_total_preview:.2f}")
    with m2:
        st.metric(label=f"💰 Preço de Venda (Com {margem_lucro:.0f}% de Lucro)", value=f"€ {preco_final_preview:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    botao_texto = "💾 Salvar Alterações" if is_editing else "💾 Salvar Novo Produto no Catálogo"
    
    if st.button(botao_texto, use_container_width=True, type="primary"):
        if not nome_prod:
            st.error("Por favor, preencha o Nome do Produto.")
        else:
            caminho_foto = produto_em_edicao.get("foto", "")
            if foto_upload is not None:
                os.makedirs(PASTA_IMAGENS, exist_ok=True)
                ext = foto_upload.name.split(".")[-1]
                caminho_foto = os.path.join(PASTA_IMAGENS, f"{codigo_automatico}.{ext}")
                with open(caminho_foto, "wb") as f:
                    f.write(foto_upload.getbuffer())

            desc_nfc_txt = desc_nfc if usa_nfc else "Não usa"
            desc_argola_txt = desc_argola if usa_argola else "Não usa"
            desc_outros_txt = desc_outros if usa_outros else "Não usa"

            novo_item = {
                "codigo": codigo_automatico,
                "nome": nome_prod,
                "categoria": categoria_prod,
                "gramas_pla": gramas_pla,
                "horas_imp": horas_imp,
                "extras": f"NFC: {desc_nfc_txt} (€{custo_nfc}) | Argola: {desc_argola_txt} (€{custo_argola}) | Outros: {desc_outros_txt} (€{custo_outros})",
                "preco_calculado": round(preco_final_preview, 2),
                "foto": caminho_foto
            }

            if is_editing:
                st.session_state["catalogo"][edit_idx] = novo_item
                st.session_state["edit_idx_catalogo"] = None
                msg = f"Produto '{nome_prod}' atualizado com sucesso!"
            else:
                st.session_state["catalogo"].append(novo_item)
                msg = f"Produto '{nome_prod}' cadastrado com sucesso no catálogo!"

            salvar_dados_catalogo(st.session_state["catalogo"])
            st.success(msg)
            st.rerun()

    if is_editing:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_catalogo"] = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 📂 Produtos Cadastrados por Categoria")
    
    if not st.session_state["catalogo"]:
        st.info("Nenhum produto cadastrado no catálogo ainda.")
    else:
        for cat in categorias_produtos_lista:
            prods_filtrados = [p for p in st.session_state["catalogo"] if normalizar_categoria(p.get("categoria")) == cat]
            
            if prods_filtrados:
                with st.expander(f"📁 **{cat}** ({len(prods_filtrados)} produtos)"):
                    for i, prod in enumerate(prods_filtrados):
                        g_prod = float(prod.get("gramas_pla", 0.0))
                        h_prod = float(prod.get("horas_imp", 0.0))
                        
                        c_pla_val = g_prod * custo_g_pla_global
                        c_hora_val = h_prod * custo_h_imp_global
                        
                        extras_str = str(prod.get("extras", ""))
                        extra_val = 0.0
                        if "€" in extras_str:
                            import re
                            valores_extras = re.findall(r"€([0-9.]+)", extras_str)
                            extra_val = sum([float(v) for v in valores_extras])
                        
                        custo_total_prod = c_pla_val + c_hora_val + extra_val
                        preco_venda_atual = custo_total_prod * 2.0

                        st.markdown(f"**🏷️ [{prod.get('codigo')}] {prod.get('nome')}**")
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.write(f"• **PLA:** {g_prod}g | **Tempo:** {h_prod}h")
                            st.write(f"• **Extras:** {extras_str if extras_str else 'Nenhum'}")
                            st.markdown(f"• **Custo de Produção:** € {custo_total_prod:.2f}")
                            st.markdown(f"• **Preço de Venda (100%):** **€ {preco_venda_atual:.2f}**")
                        with c2:
                            foto_p = str(prod.get("foto", ""))
                            if foto_p and os.path.exists(foto_p):
                                st.image(foto_p, use_container_width=True)
                            else:
                                st.caption("No image")
                        
                        real_idx = st.session_state["catalogo"].index(prod)
                        
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if st.button("✏️ Editar", key=f"edit_cat_{cat}_{i}"):
                                st.session_state["edit_idx_catalogo"] = real_idx
                                st.rerun()
                        with col_b2:
                            if st.button("🗑️ Excluir", key=f"del_cat_{cat}_{i}"):
                                st.session_state["catalogo"].remove(prod)
                                salvar_dados_catalogo(st.session_state["catalogo"])
                                st.success("Produto removido!")
                                st.rerun()
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
        
    st.info(f"⚙️ **Custos Base Atuais:** PLA = € {st.session_state['global_preco_kg_pla']:.2f} / KG | Hora = € {custo_h_imp_global:.2f} / h")
    st.markdown("---")
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        gramas = st.number_input("Gramas de PLA usadas", min_value=0.0, value=50.0, step=1.0)
        horas = st.number_input("Horas de Impressão", min_value=0.0, value=3.0, step=0.5)
        margem = st.number_input("Margem de Lucro (%)", min_value=0.0, value=100.0, step=10.0)

    custo_pla = gramas * custo_g_pla_global
    custo_horas = horas * custo_h_imp_global
    custo_total = custo_pla + custo_horas
    preco_venda = custo_total * (1 + (margem / 100))
    
    st.markdown("---")
    r1, r2 = st.columns(2)
    with r1:
        st.metric(label="Custo Total", value=f"€ {custo_total:.2f}")
    with r2:
        st.metric(label="Preço Sugerido", value=f"€ {preco_venda:.2f}")

# ==========================================
# 4. COMPRAS E 5. PRODUÇÃO
# ==========================================
elif st.session_state["pagina"] == "Compras":
    st.markdown("## 🛒 Cadastro de Compras de Insumos")
    if st.button("⬅️ Voltar"):
        st.session_state["pagina"] = "Início"
        st.rerun()
    st.info("Módulo de compras ativo.")

elif st.session_state["pagina"] == "Produção":
    st.markdown("## ⚙️ Registro de Produção de Lotes")
    if st.button("⬅️ Voltar"):
        st.session_state["pagina"] = "Início"
        st.rerun()
    st.info("Módulo de produção ativo.")