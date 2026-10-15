import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Gestão Impressão 3D", page_icon="🖨️", layout="wide")

ARQUIVO_DADOS = "produtos_3d.csv"
PASTA_IMAGENS = "imagens"

# Garante que a pasta de imagens existe
if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)

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

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Início"

# Custos padrão
if "custo_filamento_g" not in st.session_state:
    st.session_state["custo_filamento_g"] = 0.10
if "custo_hora_maquina" not in st.session_state:
    st.session_state["custo_hora_maquina"] = 5.00

custo_filamento_g = st.session_state["custo_filamento_g"]
custo_hora_maquina = st.session_state["custo_hora_maquina"]

categorias_lista = [
    "Decoração", "Utilitários", "Miniaturas", "Laços", 
    "Acessórios", "Organização", "Natal", "Religiao", "Outros"
]

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

# ==========================================
# BARRA LATERAL (MENU E CONFIGURAÇÕES)
# ==========================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    elif os.path.exists("imagens/logo.png"):
        st.image("imagens/logo.png", use_container_width=True)
    
    st.title("🖨️ Menu Principal")
    
    if st.button("🏠 Início / Painel", use_container_width=True):
        st.session_state["pagina_atual"] = "Início"
        st.session_state["edit_index"] = None
        st.rerun()
        
    if st.button("➕ Cadastrar Novo Produto", use_container_width=True):
        st.session_state["edit_index"] = None
        st.session_state["pagina_atual"] = "Cadastrar"
        st.rerun()
        
    if st.button("📑 Gerar Orçamento", use_container_width=True):
        st.session_state["pagina_atual"] = "Orcamento"
        st.rerun()

    st.markdown("---")
    st.header("⚙️ Custos Base")
    st.session_state["custo_filamento_g"] = st.number_input("Custo Filamento (R$/g)", min_value=0.0, value=custo_filamento_g, step=0.01)
    st.session_state["custo_hora_maquina"] = st.number_input("Custo Hora Máquina (R$/h)", min_value=0.0, value=custo_hora_maquina, step=0.5)

# ==========================================
# PÁGINA 1: INÍCIO (PAINEL PRINCIPAL COM LOGO E BOTÕES)
# ==========================================
if st.session_state["pagina_atual"] == "Início":
    # Exibe a logo principal em destaque no topo da página (se existir)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=250)
    elif os.path.exists("imagens/logo.png"):
        st.image("imagens/logo.png", width=250)

    st.title("🖨️ Gestão de Produção - Impressão 3D")
    st.markdown("Bem-vindo ao seu sistema móvel de controlo de custos, catálogo de produtos e orçamentos.")
    
    st.markdown("### Acesso Rápido")
    col_bt1, col_bt2 = st.columns(2)
    with col_bt1:
        if st.button("➕ Cadastrar Novo Produto", type="primary", use_container_width=True):
            st.session_state["edit_index"] = None
            st.session_state["pagina_atual"] = "Cadastrar"
            st.rerun()
    with col_bt2:
        if st.button("📑 Ir para Orçamentos", use_container_width=True):
            st.session_state["pagina_atual"] = "Orcamento"
            st.rerun()
            
    st.markdown("---")
    st.subheader("📦 Catálogo de Produtos Cadastrados")
    
    produtos = st.session_state["produtos"]
    
    if not produtos:
        st.info("Ainda não há produtos cadastrados. Clique no botão de cadastro acima para começar!")
    else:
        for i, p in enumerate(produtos):
            with st.expander(f"{p.get('codigo', 'SKU')} - {p.get('nome', 'Sem nome')} ({p.get('categoria', 'Outros')})"):
                col_img, col_info1, col_info2, col_info3 = st.columns([1.5, 1.5, 1.5, 1.5])
                
                with col_img:
                    caminho_img = p.get("imagem")
                    if caminho_img and isinstance(caminho_img, str) and os.path.exists(caminho_img):
                        st.image(caminho_img, width=120)
                    else:
                        st.info("Sem foto")

                with col_info1:
                    st.write(f"**Categoria:** {p.get('categoria')}")
                    st.write(f"**Tempo:** {p.get('tempo')}h")
                    st.write(f"**Material:** {p.get('material')}g")
                with col_info2:
                    st.write(f"**Custo Produção:** R$ {p.get('producao', 0):.2f}")
                    st.write(f"**Margem:** {p.get('margem')}%")
                    st.write(f"**Lucro:** R$ {p.get('lucro', 0):.2f}")
                with col_info3:
                    st.markdown(f"### **Venda: R$ {p.get('venda', 0):.2f}**")
                        
                col_A, col_B = st.columns(2)
                with col_A:
                    if st.button("✏️ Editar", key=f"edit_{i}"):
                        st.session_state["edit_index"] = i
                        st.session_state["pagina_atual"] = "Cadastrar"
                        st.rerun()
                with col_B:
                    if st.button("🗑️ Excluir", key=f"del_{i}"):
                        img_path = p.get("imagem")
                        if img_path and isinstance(img_path, str) and os.path.exists(img_path):
                            try:
                                os.remove(img_path)
                            except:
                                pass
                        
                        st.session_state["produtos"].pop(i)
                        salvar_dados(st.session_state["produtos"])
                        st.success("Produto excluído com sucesso!")
                        st.rerun()

# ==========================================
# PÁGINA 2: CADASTRAR / EDITAR PRODUTOS
# ==========================================
elif st.session_state["pagina_atual"] == "Cadastrar":
    if st.button("⬅️ Voltar para o Início"):
        st.session_state["edit_index"] = None
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

    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        cat_atual = str(prod_edit.get("categoria", "Decoração"))
        cat_index = categorias_lista.index(cat_atual) if cat_atual in categorias_lista else 0
        categoria = st.selectbox("Categoria", categorias_lista, index=cat_index)
        
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
    
    img_atual = prod_edit.get("imagem")
    if is_editing and img_atual and isinstance(img_atual, str) and os.path.exists(img_atual):
        st.write("Imagem atual:")
        st.image(img_atual, width=150)

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
                
                caminho_imagem_salva = prod_edit.get("imagem", None)
                if foto_produto is not None:
                    try:
                        nome_limpo = "".join(c for c in foto_produto.name if c.isalnum() or c in ('.', '_', '-'))
                        nome_arquivo = f"{codigo_sugerido.replace('-', '_')}_{nome_limpo}"
                        caminho_imagem_salva = os.path.join(PASTA_IMAGENS, nome_arquivo)
                        
                        with open(caminho_imagem_salva, "wb") as f:
                            f.write(foto_produto.getbuffer())
                    except Exception as img_err:
                        st.warning(f"Aviso: Não foi possível salvar a imagem ({img_err}), mas o produto será salvo.")

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
                
                st.success("Produto guardado com sucesso!")
                st.session_state["pagina_atual"] = "Início"
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro detalhado ao cadastrar: {e}")

    if is_editing:
        if st.button("❌ Cancelar Edição"):
            st.session_state["edit_index"] = None
            st.session_state["pagina_atual"] = "Início"
            st.rerun()

# ==========================================
# PÁGINA 3: ORÇAMENTO
# ==========================================
elif st.session_state["pagina_atual"] == "Orcamento":
    if st.button("⬅️ Voltar para o Início"):
        st.session_state["pagina_atual"] = "Início"
        st.rerun()
        
    st.subheader("📑 Calculadora de Orçamento Rápido")
    
    produtos = st.session_state["produtos"]
    
    if not produtos:
        st.warning("Não existem produtos cadastrados para gerar orçamento. Cadastre um produto primeiro.")
    else:
        nomes_produtos = [f"{p.get('codigo')} - {p.get('nome')}" for p in produtos]
        escolha_prod = st.selectbox("Selecione o Produto", nomes_produtos)
        
        idx_escolhido = nomes_produtos.index(escolha_prod)
        prod_selecionado = produtos[idx_escolhido]
        
        col_orc1, col_orc2 = st.columns(2)
        
        with col_orc1:
            st.markdown("### Detalhes do Item")
            st.write(f"**Categoria:** {prod_selecionado.get('categoria')}")
            st.write(f"**Preço Unitário Base:** R$ {prod_selecionado.get('venda', 0):.2f}")
            quantidade = st.number_input("Quantidade Desejada", min_value=1, value=1, step=1)
            
        with col_orc2:
            st.markdown("### Condições Especiais")
            desconto_perc = st.number_input("Desconto Aplicável (%)", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
            
        st.markdown("---")
        
        preco_unit = float(prod_selecionado.get('venda', 0))
        subtotal = preco_unit * quantidade
        valor_desconto = subtotal * (desconto_perc / 100)
        total_final = subtotal - valor_desconto
        
        st.markdown(f"### 💰 Resumo do Orçamento")
        st.write(f"**Subtotal ({quantidade} un.):** R$ {subtotal:.2f}")
        if desconto_perc > 0:
            st.write(f"**Desconto ({desconto_perc}%):** - R$ {valor_desconto:.2f}")
        st.markdown(f"## **Total do Orçamento: R$ {total_final:.2f}**")
        
        if st.button("🖨️ Imprimir / Copiar Resumo"):
            st.success("Orçamento calculado com sucesso! Pronto para enviar ao cliente.")
