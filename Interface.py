import streamlit as st
from classes import Tabela  

st.set_page_config(page_title="Índice Hash - Demo", layout="wide")

st.title("Índice Hash")

#Entrada lateral
with st.sidebar:
    st.header("Parâmetros")
    tamanho_pagina = st.number_input(
        "Tamanho da página (bytes)",
        min_value=1, value=20, step=1, help="Limite de bytes por página"
    )
    texto = st.text_area(
        "Palavras (uma por linha)",
        value="Hello\nHappiness\nCat\nDog\nTime\nYes\nSmile\nWater\n",
        height=200
    )

#Processamento
linhas = [l.strip() for l in texto.splitlines() if l.strip()]
tabela = Tabela(nome="palavras", tamanho_pagina_bytes=tamanho_pagina)
tabela.carregar_de_iterable(linhas)
tabela.paginar()

#Resumo
col1, col2, col3 = st.columns(3)
col1.metric("Tuplas", len(tabela.tuplas))
col2.metric("Páginas", tabela.numero_paginas())
col3.metric("Tamanho da página (bytes)", tamanho_pagina)

st.divider()

#Busca
chave = st.text_input("Buscar chave (table scan)", value="Water")
if chave:
    p, i, custo = tabela.localizar_por_chave_table_scan(chave)
    if p is not None:
        st.success(f"'{chave}' encontrada na página {p}, posição {i} (custo: {custo} página(s) lida(s))")
    else:
        st.warning(f"'{chave}' não encontrada (custo: {custo} página(s) lida(s))")

st.divider()

#Listagem de páginas/tuplas
for idx, pagina in enumerate(tabela.paginas):
    with st.expander(f"Página {idx} — {len(pagina.tuplas)} tupla(s) — {pagina.tamanho_atual} bytes", expanded=(idx == 0)):
        for t in pagina.tuplas:
            st.write(f"- {t}")
