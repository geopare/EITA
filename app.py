import streamlit as st
import pandas as pd
import os

# Configuração da página do aplicativo
st.set_page_config(page_title="Gestão Eita", layout="wide")

# Nome do arquivo onde os dados serão salvos no seu computador
ARQUIVO_DADOS = "produtos_3d.csv"

# Função para carregar os produtos salvos no arquivo CSV
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            df = pd.read_csv(ARQUIVO_DADOS)
            return df.to_dict("records")
        except Exception:
            return []
    return []

# Função para salvar a lista de produtos atualizada no arquivo CSV
def salvar_dados(produtos_lista):
    if len(produtos_lista) > 0:
        df = pd.DataFrame(produtos_lista)
        df.to_csv(ARQUIVO_DADOS, index=False)
    else:
        if os.path.exists(ARQUIVO_DADOS):
            os.remove(ARQUIVO_DADOS)

# Inicialização dos estados na sessão
if "produtos" not in st.session_state:
    st.session_state["produtos"] = carregar_dados()

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# Controle de navegação (Página atual)
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Início"

categorias_lista = [
    "Decoração", 
    "Laços", 
    "Utilidades",   
    "Acessórios", 
    "Organização", 
    "Natal",
    "Religiosos",
    "Outros",
    
]

# --- BARRA LATERAL: Configurações Globais e Menu Rápido ---
st.sidebar.header("⚙️ Parâmetros de Custos")
custo_filamento_kg = st.sidebar.number_input("Custo do Filamento por KG (€)", value=14.00, step=0.50)
custo_hora_maquina = st.sidebar.number_input("Custo de Energia/Hora da Máquina (€)", value=0.20, step=0.05)
custo_filamento_g = custo_filamento_kg / 1000.0

st.sidebar.divider()
st.sidebar.subheader("📌 Menu de Navegação")
if st.sidebar.button("🏠 Início"):
    st.session_state["pagina_atual"] = "Início"
    st.rerun()
if st.sidebar.button("📦 Cadastrar Produtos"):
    st.session_state["pagina_atual"] = "Cadastrar"
    st.rerun()
if st.sidebar.button("📋 Produtos (Catálogo)"):
    st.session_state["pagina_atual"] = "Produtos"
    st.rerun()
if st.sidebar.button("🧾 Orçamento"):
    st.session_state["pagina_atual"] = "Orçamento"
    st.rerun()

# ==========================================
# PÁGINA 1: INÍCIO (LOGO E BOTÕES PRINCIPAIS)
# ==========================================
if st.session_state["pagina_atual"] == "Início":
    # Centralizando a logo e os botões na tela inicial
    col_centro1, col_centro2, col_centro3 = st.columns([1, 2, 1])
    
    with col_centro2:
        # Exibindo a Logo (Certifique-se de colocar o arquivo 'logo.png' na pasta do projeto)
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center;'>🖨️ 3D Print Manager</h1>", unsafe_allow_html=True)
            st.info("💡 Dica: Coloque uma imagem chamada `logo.png` na pasta do projeto para exibir sua logo aqui.")
            
        st.markdown("<h3 style='text-align: center; color: gray;'>Sistema de Gestão e Precificação 3D</h3>", unsafe_allow_html=True)
        st.write("")
        st.write("")
        
        # Três botões principais grandes na tela inicial
        if st.button("📦 Cadastrar Produtos", use_container_width=True):
            st.session_state["pagina_atual"] = "Cadastrar"
            st.rerun()
            
        if st.button("📋 Produtos (Catálogo)", use_container_width=True):
            st.session_state["pagina_atual"] = "Produtos"
            st.rerun()
            
        if st.button("🧾 Orçamento", use_container_width=True):
            st.session_state["pagina_atual"] = "Orçamento"
            st.rerun()

# ==========================================
# PÁGINA 2: CADASTRAR / EDITAR PRODUTOS
# ==========================================
elif st.session_state["pagina_atual"] == "Cadastrar":
    if st.button("⬅️ Voltar para o Início"):
        st.session_state["pagina_atual"] = "Início"
        st.rerun()
        
    is_editing = st.session_state["edit_index"] is not None
    
    if is_editing:
        st.subheader(f"✏️ Editando Produto: {st.session_state['produtos'][st.session_state['edit_index']]['nome']}")
        prod_edit = st.session_state["produtos"][st.session_state["edit_index"]]
    else:
        st.subheader("➕ Novo Cadastro de Produto")
        prod_edit = {
            "codigo": "",
            "nome": "",
            "categoria": "Decoração",
            "tempo": 0.0,
            "material": 0.0,
            "margem": 100.0,
            "imagem": None
        }

    # Definimos os prefixos das categorias
    prefixos_categorias = {
        "Decoração": "DEC",
        "Utilitários": "UTI",
        "Miniaturas": "MIN",
        "Laços": "LAC",
        "Acessórios": "ACE",
        "Organização": "ORG",
        "Natal": "NAT",
        "Religiao": "REL",
        "Outros": "OUT",
    }

    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        cat_atual = str(prod_edit.get("categoria", "Decoração"))
        cat_index = categorias_lista.index(cat_atual) if cat_atual in categorias_lista else 0
        categoria = st.selectbox("Categoria", categorias_lista, index=cat_index)
        
        # Lógica do SKU Automático baseada na categoria selecionada
        if not is_editing:
            prefixo_atual = prefixos_categorias.get(categoria, "PRD")
            produtos_mesma_cat = [p for p in st.session_state["produtos"] if p.get("categoria") == categoria]
            proximo_num = len(produtos_mesma_cat) + 1
            codigo_sugerido = f"{prefixo_atual}-{proximo_num:03d}"
        else:
            codigo_sugerido = str(prod_edit.get("codigo", ""))

        codigo = st.text_input("Código do Produto (SKU Automático)", value=codigo_sugerido, disabled=True)
        nome = st.text_input("Nome do Produto", value=str(prod_edit.get("nome", "")))
        
    with col_f2:
        tempo_impressao = st.number_input("Tempo de Impressão (em horas)", min_value=0.0, step=0.5, value=float(prod_edit.get("tempo", 0.0)))
        material_uso = st.number_input("Material Usado (em gramas)", min_value=0.0, step=1.0, value=float(prod_edit.get("material", 0.0)))
        margem_desejada = st.number_input("Margem de Lucro Desejada (%)", min_value=0.0, step=10.0, value=float(prod_edit.get("margem", 100.0)))

    st.markdown("---")
    foto_produto = st.file_uploader("📸 Tirar foto ou carregar imagem do produto", type=["jpg", "jpeg", "png"])

    st.markdown("")
    btn_texto = "Salvar Alterações" if is_editing else "Cadastrar Produto"
    
    if st.button(btn_texto, type="primary"):
        if not nome:
            st.error("Por favor, preencha pelo menos o Nome do produto.")
        else:
            try:
                custo_material = material_uso * custo_filamento_g
                custo_tempo = tempo_impressao * custo_hora_maquina
                preco_producao = custo_material + custo_tempo
                
                valor_lucro = preco_producao * (margem_desejada / 100)
                preco_venda = preco_producao + valor_lucro
                
                # Tratamento seguro da imagem
                imagem_salva = prod_edit.get("imagem", None)
                if 'foto_produto' in locals() and foto_produto is not None:
                    imagem_salva = foto_produto.name

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
                    "imagem": imagem_salva
                }
                
                if is_editing:
                    st.session_state["produtos"][st.session_state["edit_index"]] = produto_dados
                    st.session_state["edit_index"] = None
                else:
                    st.session_state["produtos"].append(produto_dados)
                
                salvar_dados(st.session_state["produtos"])
                
                st.success("Produto guardado com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro detalhado ao cadastrar: {e}")

    if is_editing:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_index"] = None
            st.rerun()


# ==========================================
# PÁGINA 3: PRODUTOS (CATÁLOGO)
# ==========================================
elif st.session_state["pagina_atual"] == "Produtos":
    if st.button("⬅️ Voltar para o Início"):
        st.session_state["pagina_atual"] = "Início"
        st.rerun()
        
    st.subheader("📋 Lista de Produtos Cadastrados")
    
    if len(st.session_state["produtos"]) == 0:
        st.info("Nenhum produto cadastrado ainda. Use a opção 'Cadastrar Produtos' para começar.")
    else:
        filtro_categoria = st.selectbox("Filtrar por Categoria", ["Todas"] + categorias_lista)
        st.divider()
        
        for index, p in enumerate(st.session_state["produtos"]):
            if filtro_categoria != "Todas" and p['categoria'] != filtro_categoria:
                continue
                
            col_c1, col_c2, col_c3 = st.columns([2, 2, 1])
            
            with col_c1:
                st.markdown(f"### {p['nome']}")
                st.write(f"**Código:** `{p['codigo']}` | **Categoria:** {p['categoria']}")
                st.write(f"⏱️ Tempo: {p['tempo']}h | 🧵 Material: {p['material']}g")
            
            with col_c2:
                st.metric(label="Preço de Venda", value=f"{float(p['venda']):.2f} €")
                st.write(f"Custo: {float(p['producao']):.2f} € | Lucro: {float(p['lucro']):.2f} € ({p['margem']}%)")
                
            with col_c3:
                st.write("")
                if st.button("✏️ Editar", key=f"cat_edit_{index}"):
                    st.session_state["edit_index"] = index
                    st.session_state["pagina_atual"] = "Cadastrar"
                    st.rerun()
                
                if st.button("🗑️ Excluir", key=f"cat_del_{index}"):
                    st.session_state["produtos"].pop(index)
                    if st.session_state["edit_index"] == index:
                        st.session_state["edit_index"] = None
                    salvar_dados(st.session_state["produtos"])
                    st.rerun()
            
            st.divider()

# ==========================================
# PÁGINA 4: ORÇAMENTO
# ==========================================
elif st.session_state["pagina_atual"] == "Orçamento":
    if st.button("⬅️ Voltar para o Início"):
        st.session_state["pagina_atual"] = "Início"
        st.rerun()
        
    st.subheader("🧾 Gerador de Orçamento para Clientes")
    st.markdown("Selecione os produtos desejados e informe a quantidade para calcular o valor final da venda.")
    
    if len(st.session_state["produtos"]) == 0:
        st.info("Cadastre alguns produtos primeiro para poder gerar orçamentos.")
    else:
        itens_selecionados = []
        st.write("### Selecione os produtos e quantidades:")
        
        for index, p in enumerate(st.session_state["produtos"]):
            col_o1, col_o2, col_o3 = st.columns([3, 1, 2])
            with col_o1:
                st.markdown(f"**{p['nome']}** (`{p['codigo']}`)")
                st.write(f"Preço Unitário: **{float(p['venda']):.2f} €**")
            with col_o2:
                qtd = st.number_input(f"Qtd", min_value=0, step=1, value=0, key=f"orc_qtd_{index}")
            with col_o3:
                if qtd > 0:
                    subtotal = qtd * float(p['venda'])
                    st.markdown(f"**Subtotal:** `{subtotal:.2f} €`")
                else:
                    st.write("-")
            
            if qtd > 0:
                itens_selecionados.append({
                    "nome": p['nome'],
                    "codigo": p['codigo'],
                    "quantidade": qtd,
                    "unitario": float(p['venda']),
                    "subtotal": qtd * float(p['venda'])
                })
            
            st.divider()
            
        if len(itens_selecionados) > 0:
            st.subheader("📊 Resumo do Orçamento")
            total_geral = sum(item["subtotal"] for item in itens_selecionados)
            
            df_orcamento = pd.DataFrame(itens_selecionados)
            df_orcamento.columns = ["Produto", "Código", "Quantidade", "Preço Unitário (€)", "Subtotal (€)"]
            st.dataframe(df_orcamento, hide_index=True, use_container_width=True)
            
            st.markdown(f"### 💶 Valor Total da Venda: **{total_geral:.2f} €**")
        else:
            st.info("Insira a quantidade de pelo menos um produto acima para calcular o orçamento.")
