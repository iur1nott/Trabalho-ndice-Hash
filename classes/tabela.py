from __future__ import annotations
from typing import Iterable, Optional, Tuple
from .tupla import Tupla
from .pagina import Pagina

class Tabela:
    """Representa uma tabela de dados (linhas/tuplas) e
    é responsável por paginar essas tuplas em objetos Pagina. Apenas divide em páginas por tamanho em bytes.
    Depois plugar buckets/índice nesta estrutura."""

    def __init__(self, nome: str, tamanho_pagina_bytes: int):
        if tamanho_pagina_bytes <= 0:
            raise ValueError("tamanho_pagina_bytes deve ser > 0")

        self.nome = nome
        self.tamanho_pagina_bytes = tamanho_pagina_bytes
        self.tuplas: list[Tupla] = []
        self.paginas: list[Pagina] = []

#Carga de dados 
def carregar_de_iterable(self, linhas: Iterable[str]) -> None:
        """Recebe um iterável de strings (ex.: arquivo .txt com 1 palavra por linha).
        Cada linha vira uma Tupla(chave=linha.strip(), dados=linha.strip())."""
        for linha in linhas:
            chave = linha.strip()
            if not chave:
                continue
            self.adicionar_tupla(Tupla(chave))

def adicionar_tupla(self, tupla: Tupla) -> None:
        """Adiciona a tupla à tabela (sem paginar ainda)."""
        self.tuplas.append(tupla)

#Paginação 
def paginar(self) -> None:
        """Reconstrói self.paginas usando self.tuplas e self.tamanho_pagina_bytes.
        Método:
          - varre as tuplas na ordem;
          - cria uma página enquanto couber;
          - quando a próxima tupla não couber, fecha a página e abre outra;
          - se uma tupla sozinha for maior que a página, ela ocupa uma página isolada."""
        self.paginas = []
        pagina_atual = Pagina(numero_pagina=0)

        for t in self.tuplas:
            tam = t.tamanho_em_bytes()

#Caso extremo: tupla maior que a página -> página só pra ela
            if tam > self.tamanho_pagina_bytes:
#Se a página atual tem algo, fecha antes
                if pagina_atual.tuplas:
                    self.paginas.append(pagina_atual)
                    pagina_atual = Pagina(numero_pagina=len(self.paginas))
                pagina_atual.adicionar_tupla(t)
                self.paginas.append(pagina_atual)
                pagina_atual = Pagina(numero_pagina=len(self.paginas))
                continue

#Se não cabe na página atual, fecha e cria outra
            if pagina_atual.tamanho_atual + tam > self.tamanho_pagina_bytes:
                self.paginas.append(pagina_atual)
                pagina_atual = Pagina(numero_pagina=len(self.paginas))

#Adiciona na página atual
            pagina_atual.adicionar_tupla(t)

#Fecha a última página (mesmo se vazia, garantimos pelo menos 1 página)
        if pagina_atual.tuplas or not self.paginas:
            self.paginas.append(pagina_atual)

def numero_paginas(self) -> int:
    return len(self.paginas)

def obter_pagina(self, indice: int) -> Pagina:
    return self.paginas[indice]

def localizar_por_chave_table_scan(self, chave: str) -> Tuple[Optional[int], Optional[int], int]:
        """Busca linear (table scan) pela chave nas páginas já paginadas.
        Retorna (indice_pagina, indice_tupla_na_pagina, custo_em_paginas_lidas).
        Se não achar, retorna (None, None, custo)."""
        custo_paginas_lidas = 0
        for idx_pagina, pagina in enumerate(self.paginas):
            custo_paginas_lidas += 1
            for idx_tupla, tupla in enumerate(pagina.tuplas):
                if tupla.chave == chave:
                    return idx_pagina, idx_tupla, custo_paginas_lidas
        return None, None, custo_paginas_lidas

def __str__(self) -> str:
    return f"Tabela(nome='{self.nome}', tuplas={len(self.tuplas)}, paginas={len(self.paginas)}, tamanho_pagina={self.tamanho_pagina_bytes} bytes)"
