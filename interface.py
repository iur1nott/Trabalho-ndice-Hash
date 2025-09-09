# app.py
import streamlit as st
from io import StringIO
from classes.tabela import Tabela
from classes.funcaohash import FuncaoHash
from classes.bucket import Bucket, Ponteiro

st.set_page_config(page_title="Índice Hash + Paginação", layout="wide")
st.title("Índice Hash + Paginação (demo simples)")

if "tabela" not in st.session_state:
    st.session_state.tabela = None
    st.session_state.funcao = None
    st.session_state.buckets = None
    st.session_state.fr = None
    st.session_state.construido = False
    st.session_state.stats = {}

with st.sidebar:
    st.header("Configurações")
    tam_pag = st.number_input("Tamanho da página (bytes)", min_value=1, value=64, step=1)
    fr = st.number_input("FR (máx. tuplas por bucket)", min_value=1, value=4, step=1)
    arquivo = st.file_uploader("Carregar .txt (1 linha = 1 chave)", type=["txt"])
    texto = st.text_area("Ou cole as linhas aqui", value="ana\nbruno\ncarla\ndiego\nelaine\nfabio\ngabriela\nhenrique\nivan\njulia", height=150)
    btn_construir = st.button("Construir índice")

def construir_indice(linhas, tam_pag, fr):
    tabela = Tabela("demo", tam_pag)
    tabela.carregar_de_iterable(linhas)
    tabela.paginar()
    func = FuncaoHash(numero_tuplas=len(tabela.tuplas), fator_carga=fr)
    buckets = [Bucket() for _ in range(func.numero_buckets)]
    total = len(tabela.tuplas)
    colisoes = 0

    for i_pag, pag in enumerate(tabela.paginas):
        for i_t, t in enumerate(pag.tuplas):
            i_b = func.hash(t.chave)
            antes = len(buckets[i_b])
            buckets[i_b].inserir(Ponteiro(i_pag, i_t))
            depois = len(buckets[i_b])
            if depois > 1 and depois > antes:
                colisoes += 1

    overflows_abs = sum(max(0, len(b.listar()) - fr) for b in buckets)
    taxa_col = (colisoes / total) if total else 0.0
    taxa_ovf = (overflows_abs / total) if total else 0.0
    stats = {
        "NR": total,
        "NB": func.numero_buckets,
        "FR": fr,
        "colisoes": colisoes,
        "taxa_colisoes": taxa_col,
        "overflows": overflows_abs,
        "taxa_overflows": taxa_ovf,
        "paginas": tabela.numero_paginas(),
    }
    return tabela, func, buckets, stats

if btn_construir:
    if arquivo is not None:
        conteudo = StringIO(arquivo.getvalue().decode("utf-8")).read()
        linhas = [l for l in conteudo.splitlines() if l.strip()]
    else:
        linhas = [l for l in texto.splitlines() if l.strip()]
    tabela, func, buckets, stats = construir_indice(linhas, tam_pag, fr)
    st.session_state.tabela = tabela
    st.session_state.funcao = func
    st.session_state.buckets = buckets
    st.session_state.fr = fr
    st.session_state.stats = stats
    st.session_state.construido = True

st.subheader("Estatísticas")
if st.session_state.construido:
    s = st.session_state.stats
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("NR (tuplas)", s["NR"])
    c2.metric("NB (buckets)", s["NB"])
    c3.metric("FR máx/bucket", s["FR"])
    c4.metric("Colisões", s["colisoes"])
    c5.metric("Taxa colisões", f"{s['taxa_colisoes']:.2%}")
    c6.metric("Overflows", s["overflows"])
    st.caption(f"Taxa de overflows: {s['taxa_overflows']:.2%} • Páginas de dados: {s['paginas']}")
else:
    st.info("Carregue dados e clique em **Construir índice**.")

st.subheader("Busca")
chave = st.text_input("Chave de busca")
col_a, col_b = st.columns(2)
btn_indice = col_a.button("Buscar (índice)")
btn_scan = col_b.button("Table Scan")

def buscar_por_indice(chave):
    tabela = st.session_state.tabela
    func = st.session_state.funcao
    buckets = st.session_state.buckets
    i_b = func.hash(chave)
    bucket = buckets[i_b]
    paginas_lidas = set()
    pos = None
    for p in bucket.listar():
        paginas_lidas.add(p.numero_pagina)
        t = tabela.paginas[p.numero_pagina].tuplas[p.indice_tupla]
        if t and t.chave == chave:
            pos = (p.numero_pagina, p.indice_tupla, t)
            break
    custo = len(paginas_lidas)
    return i_b, len(bucket), pos, custo

def table_scan(chave):
    tabela = st.session_state.tabela
    registros = []
    paginas_lidas = 0
    achou = None
    for i_pag, pag in enumerate(tabela.paginas):
        paginas_lidas += 1
        for i_t, t in enumerate(pag.tuplas):
            registros.append({"página": i_pag, "tupla_idx": i_t, "chave": t.chave})
            if t.chave == chave and achou is None:
                achou = (i_pag, i_t, t)
                return registros, achou, paginas_lidas
    return registros, achou, paginas_lidas

if btn_indice and st.session_state.construido and chave:
    i_b, tam_b, pos, custo = buscar_por_indice(chave)
    st.write(f"Bucket da chave: **{i_b}** (tamanho do bucket: {tam_b})")
    if pos:
        st.success(f"Encontrada na página **{pos[0]}**, tupla **{pos[1]}**. Custo estimado: **{custo} página(s) lida(s)**.")
        st.write(f"Tupla: chave='{pos[2].chave}', dados='{pos[2].dados}'")
    else:
        st.warning(f"Chave não encontrada. Custo estimado: **{custo} página(s) lida(s)**.")

if btn_scan and st.session_state.construido and chave:
    regs, achou, custo = table_scan(chave)
    st.write("Registros lidos até encontrar a chave:")
    try:
        import pandas as pd
        st.dataframe(pd.DataFrame(regs))
    except Exception:
        for r in regs:
            st.write(r)
    if achou:
        st.success(f"Encontrada na página **{achou[0]}**, tupla **{achou[1]}**. Custo (table scan): **{custo} página(s)**.")
    else:
        st.warning(f"Chave não encontrada. Custo (table scan): **{custo} página(s)**.")
