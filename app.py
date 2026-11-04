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

# Lista de categorias padrão
categorias_produtos_lista = ["Decoração", "Natal", "Utilidades", "Brinquedos", "Outros"]

# ==========================================
# FUNÇÕES COM CACHE (Evita lentidão/travamento)
# ==========================================
@st.cache_data
def carregar_dados_antigos():
    if os.path.exists(ARQUIVO_ANTIGO):
        try:
            df_antigo = pd.read_csv(ARQUIVO_ANTIGO)
            produtos_convertidos = []
            for _, row in df_antigo.iterrows():
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
                    "foto": str(row.get("imagem", ""))
                })
            return produtos_convertidos
        except Exception as e:
            return []
    return []

@st.cache_data
def carregar_catalogo_csv():
    if os.path.exists(ARQUIVO_CATALOGO):
        try:
            df = pd.read_csv(ARQUIVO_CATALOGO)
            return df.to_dict("records")
        except:
            return []
    else:
        return carregar_dados_antigos()

def salvar_csv(caminho, dados, mensagem_sucesso):
    try:
        df = pd.DataFrame(dados)
        df.to_csv(caminho, index=False)
        st.cache_data.clear() # Limpa o cache ao salvar para atualizar os dados na hora
    except Exception as e:
        st.error(f"Erro ao salvar arquivo {caminho}: {e}")

# ==========================================
# INICIALIZAÇÃO DO SESSION STATE
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "ProdutosCatalogo"

if "catalogo" not in st.session_state:
    st.session_state["catalogo"] = carregar_catalogo_csv()

if "compras" not in st.session_state:
    st.session_state["compras"] = []

if "mostrar_produtos_catalogo" not in st.session_state:
    st.session_state["mostrar_produtos_catalogo"] = False

if "edit_idx_catalogo" not in st.session_state:
    st.session_state["edit_idx_catalogo"] = None

def renderizar_cabecalho(titulo):
    st.markdown(f"## 🖨️ Sistema EITA - {titulo}")

# ==========================================
# BARRA LATERAL / NAVEGAÇÃO
# ==========================================
st.sidebar.title("Navegação")
opcao_menu = st.sidebar.radio("Ir para:", ["Catálogo de Produtos"], index=0)

if opcao_menu == "Catálogo de Produtos":
    st.session_state["pagina_atual"] = "ProdutosCatalogo"

# ==========================================
# ABA 3: CATÁLOGO DE PRODUTOS
# ==========================================
if st.session_state["pagina_atual"] == "ProdutosCatalogo":
    edit_idx_cat = st.session_state["edit_idx_catalogo"]
    is_edit_cat = edit_idx_cat is not None
    renderizar_cabecalho("EDITAR PRODUTO" if is_edit_cat else "CADASTRO DE PRODUTOS (CATÁLOGO)")
    st.markdown("---")

    item_cat_atual = st.session_state["catalogo"][edit_idx_cat] if is_edit_cat and edit_idx_cat < len(st.session_state["catalogo"]) else {}

    custo_g_pla = 0.025  
    custo_unit_nfc = 0.30  
    custo_unit_argola = 0.10  

    if st.session_state.get("compras"):
        df_comp = pd.DataFrame(st.session_state["compras"])
        pla_comp = df_comp[df_comp["tipo_material"].str.upper() == "PLA"]
        if not pla_comp.empty and pla_comp["quantidade"].sum() > 0:
            total_g = pla_comp.apply(lambda r: r["quantidade"] * 1000 if str(r["unidade"]).upper() == "KG" else r["quantidade"], axis=1).sum()
            if total_g > 0:
                custo_g_pla = pla_comp["custo_total"].sum() / total_g

    with st.form("form_catalogo"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_prod = st.text_input("Nome do Produto", value=item_cat_atual.get("nome", "")).strip()
            
            cat_atual = item_cat_atual.get("categoria", categorias_produtos_lista[0])
            cat_idx = categorias_produtos_lista.index(cat_atual) if cat_atual in categorias_produtos_lista else 0
            categoria_prod = st.selectbox("Categoria", categorias_produtos_lista, index=cat_idx)

            prefixo = categoria_prod[:3].upper()
            prods_cat = [p for p in st.session_state["catalogo"] if p.get("categoria") == categoria_prod]
            proximo_numero = len(prods_cat) + 1 if not is_edit_cat else int(str(item_cat_atual.get("codigo", f"{prefixo}-000")).split("-")[-1])
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
                    os.makedirs(PASTA_IMAGENS, exist_ok=True)
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
                time.sleep(0.5)
                st.rerun()

    if is_edit_cat:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_idx_catalogo"] = None
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

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
                                foto_path = str(prod.get("foto", "")).strip()
                                codigo_prod = str(prod.get("codigo", "")).strip()
                                foto_final = None

                                if foto_path and os.path.exists(foto_path):
                                    foto_final = foto_path
                                else:
                                    if os.path.exists(PASTA_IMAGENS):
                                        for arq in os.listdir(PASTA_IMAGENS):
                                            if arq.lower().startswith(codigo_prod.lower() + "."):
                                                candidato = os.path.join(PASTA_IMAGENS, arq)
                                                if os.path.exists(candidato):
                                                    foto_final = candidato
                                                    break

                                if foto_final:
                                    st.image(foto_final, use_container_width=True)
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