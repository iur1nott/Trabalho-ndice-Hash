from email.mime import text
import streamlit as st
from io import StringIO
from classes.tabela import Tabela
import os
import pandas as pd

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(page_title="Índice Hash + Paginação", layout="wide")
st.title("Índice Hash + Paginação")

# ---------------------------
# Estado da sessão
# ---------------------------
if "tabela" not in st.session_state:
    st.session_state.tabela = None
    st.session_state.construido = False

# ---------------------------
# Sidebar (Configurações)
# ---------------------------
with st.sidebar:
    st.header("Configurações")
    tam_pag = st.number_input("Tamanho da página (bytes)", min_value=1, value=4096, step=1)
    fr = st.number_input("FR (máx. tuplas por bucket)", min_value=1, value=10, step=1)

    # Upload OU texto colado
    arquivo = st.file_uploader("Carregar .txt (1 linha = 1 chave)", type=["txt"])

    btn_construir = st.button("Construir índice")

# ---------------------------
# Funções auxiliares (UI)
# ---------------------------
def obter_linhas():
    """Obtém linhas do uploader ou do textarea."""
    if arquivo is not None:
        stringio = StringIO(arquivo.getvalue().decode("utf-8"))
        return [linha.strip() for linha in stringio if linha.strip()]
    else:
        return [linha.strip() for linha in text.splitlines() if linha.strip()]

# ---------------------------
# Construção do índice
# ---------------------------
if btn_construir:
    linhas = obter_linhas()
    if not linhas:
        st.error("Nenhuma linha fornecida. Carregue um arquivo ou insira texto.")
    else:
        # Cria arquivo temporário porque Tabela espera caminho de arquivo
        temp_file = "temp_input.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))

        try:
            tabela = Tabela(temp_file, tam_pag, fr)
            tabela.construir_indice_hash()
            st.session_state.tabela = tabela
            st.session_state.construido = True
            st.success("Índice construído com sucesso!")
        except Exception as e:
            st.error(f"Erro ao construir índice: {e}")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# ---------------------------
# Estatísticas
# ---------------------------
st.subheader("Estatísticas")
if st.session_state.construido:
    tabela = st.session_state.tabela
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("NR (tuplas)", len(tabela.tuplas))
    c2.metric("NB (buckets)", len(tabela.buckets))
    c3.metric("FR máx/bucket", tabela.fator_carga)
    c4.metric("Colisões", tabela.total_colisoes)
    c5.metric("Taxa colisões", f"{tabela.taxa_colisoes:.2%}")
    c6.metric("Overflows", tabela.total_overflows)
    st.caption(f"Taxa de overflows: {tabela.taxa_overflows:.2%} • Páginas de dados: {len(tabela.paginas)}")
else:
    st.info("Carregue dados e clique em **Construir índice**.")

# ---------------------------
# Busca
# ---------------------------
st.subheader("Busca")
chave = st.text_input("Chave de busca")
col_a, col_b = st.columns(2)
btn_indice = col_a.button("Buscar (índice)")
btn_scan = col_b.button("Table Scan")

# ---------------------------
# Busca via Índice Hash
# ---------------------------
if btn_indice and st.session_state.construido and chave:
    tabela = st.session_state.tabela
    tupla_encontrada, custo = tabela.buscar_com_indice(chave)

    if tupla_encontrada:
        st.success(f"✅ Encontrada via índice! Custo: {custo} página(s) lida(s).")
        st.write(f"**Chave:** '{tupla_encontrada.chave}' | **Dados:** '{tupla_encontrada.dados}'")

        # Mostra página onde está
        for pagina in tabela.paginas:
            if any(t.chave == chave for t in pagina.tuplas):
                st.write(f"📍 Localizada na **Página {pagina.numero_pagina}**")
                break
    else:
        st.warning(f"❌ Chave não encontrada via índice. Custo: {custo} página(s) lida(s).")


# ---------------------------
# Table Scan (listando registros lidos até encontrar)
# ---------------------------
if btn_scan and st.session_state.construido and chave:
    tabela = st.session_state.tabela

    # Chama o método da classe — ele retorna (tupla, tuplas_lidas, custo)
    tupla_encontrada, tuplas_lidas, custo = tabela.table_scan(chave)
    
    # Transforma as tuplas lidas em dicionários para exibição
    registros = []
    for i, tupla in enumerate(tuplas_lidas):
        # Encontra a página da tupla
        for pagina in tabela.paginas:
            if tupla in pagina.tuplas:
                registros.append({
                    "página": pagina.numero_pagina,
                    "índice": i,
                    "chave": tupla.chave,
                    "dados": tupla.dados
                })
                break

    # Exibe a lista de registros lidos até encontrar
    st.write(f"Registros lidos até encontrar a chave ({len(registros)} tuplas):")
    
    if registros:
        try:
            st.dataframe(pd.DataFrame(registros))
        except Exception:
            for r in registros:
                st.write(r)

    if tupla_encontrada:
        st.success(f"✅ Encontrada via table scan! Custo: {custo} página(s) lida(s).")
        st.write(f"**Chave:** '{tupla_encontrada.chave}' | **Dados:** '{tupla_encontrada.dados}'")
    else:
        st.warning(f"❌ Chave não encontrada via table scan. Custo: {custo} página(s) lida(s).")
