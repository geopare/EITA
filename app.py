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

os.makedirs(PASTA_IMAGENS, exist_ok=True)
categorias_produtos_lista = ["Decoração", "Natal", "Acessórios", "Utilitários", "Utilidades", "Brinquedos", "Outros"]

# ==========================================
# GERENCIAMENTO DE ESTADO E CARREGAMENTO
# ==========================================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Início"

if "mostrar_tabela_compras" not in st.session_state:
    st.session_state["mostrar_tabela_compras"] = True

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
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
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
                    for idx, prod in prods:
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
# 3. CALCULADORA (CUSTOMIZÁVEL)
# ==========================================
elif st.session_state["pagina"] == "Calcular":
    st.markdown("## 💰 Calculadora de Precificação")
    st.markdown("---")
    
    if st.button("⬅️ Voltar para a Página Inicial"):
        st.session_state["pagina"] = "Início"
        st.rerun()
        
    st.markdown("### ⚙️ Custos Base por Unidade")
    col_base1, col_base2 = st.columns(2)
    with col_base1:
        custo_g_pla = st.number_input("Custo por Grama de PLA (€/g)", min_value=0.000, value=0.025, format="%.3f")
    with col_base2:
        custo_h_imp = st.number_input("Custo por Hora de Impressão (€/h)", min_value=0.00, value=0.50, format="%.2f")
        
    st.markdown("---")
    st.markdown("### 🖨️ Dados do Projeto / Impressão")
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        gramas = st.number_input("Gramas de PLA usadas", min_value=0.0, value=50.0, step=1.0)
        horas = st.number_input("Horas de Impressão", min_value=0.0, value=3.0, step=0.5)
        
        st.markdown("##### 🔌 Componentes Opcionais")
        usa_nfc = st.checkbox("Incluir Tag NFC")
        qtd_nfc = st.number_input("Qtd. Tags NFC", min_value=1, value=1) if usa_nfc else 0
        custo_unit_nfc = st.number_input("Custo unitário da NFC (€)", min_value=0.0, value=0.30) if usa_nfc else 0.0
        
    with col_calc2:
        usa_argola = st.checkbox("Incluir Argola")
        qtd_argola = st.number_input("Qtd. Argolas", min_value=1, value=1) if usa_argola else 0
        custo_unit_argola = st.number_input("Custo unitário da Argola (€)", min_value=0.0, value=0.10) if usa_argola else 0.0
        
        outros_custos = st.number_input("Outros Custos Extras (€)", min_value=0.0, value=0.0, step=0.50)
        margem = st.number_input("Margem de Lucro Desejada (%)", min_value=0.0, value=100.0, step=10.0)

    # Cálculos
    custo_pla = gramas * custo_g_pla
    custo_horas = horas * custo_h_imp
    custo_nfc_total = qtd_nfc * custo_unit_nfc
    custo_argola_total = qtd_argola * custo_unit_argola
    
    custo_total = custo_pla + custo_horas + custo_nfc_total + custo_argola_total + outros_custos
    preco_venda = custo_total * (1 + (margem / 100))
    
    st.markdown("---")
    st.markdown("### 📊 Resultado da Precificação")
    res1, res2 = st.columns(2)
    with res1:
        st.metric(label="Custo Total de Produção", value=f"€ {custo_total:.2f}")
    with res2:
        st.metric(label="Preço de Venda Sugerido", value=f"€ {preco_venda:.2f}")

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
            identificacao_nota = st.text_input("Identificação da Nota (NF / Fatura)", placeholder="Ex: NF-12345 ou Fatura 2026/04")
            
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
        st.markdown("### 📦 Histórico de Compras Registradas")
        if not st.session_state["compras"]:
            st.info("Nenhuma compra registrada até o momento.")
        else:
            df_compras = pd.DataFrame(st.session_state["compras"])
            st.dataframe(df_compras, use_container_width=True)
            
            if st.button("🗑️ Apagar Última Compra Adicionada"):
                st.session_state["compras"].pop()
                salvar_dados(ARQUIVO_COMPRAS, st.session_state["compras"])
                st.success("Última compra removida!")
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