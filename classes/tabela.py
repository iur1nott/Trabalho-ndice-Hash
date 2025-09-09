from __future__ import annotations
from typing import Iterable, Optional, Tuple, List, Callable
from .tupla import Tupla
from .pagina import Pagina

class Tabela:
    """Representa uma tabela de dados (linhas/tuplas).
    - paginar(): divide TODAS as tuplas em páginas globais (sem particionamento).
    - particionar(): divide as tuplas em N partições e pagina dentro de cada partição."""

    def __init__(self, nome: str, tamanho_pagina_bytes: int):
        if tamanho_pagina_bytes <= 0:
            raise ValueError("tamanho_pagina_bytes deve ser > 0")

        self.nome = nome
        self.tamanho_pagina_bytes = tamanho_pagina_bytes
        self.tuplas: List[Tupla] = []
        self.paginas: List[Pagina] = []
        self.particoes: List[List[Pagina]] = []

    #Carga de dados 
    def carregar_de_iterable(self, linhas: Iterable[str]) -> None:
        """Cada linha vira Tupla(chave=linha.strip(), dados=linha.strip())."""
        for linha in linhas:
            chave = linha.strip()
            if not chave:
                continue
            self.adicionar_tupla(Tupla(chave))

    def adicionar_tupla(self, tupla: Tupla) -> None:
        """Adiciona a tupla à tabela (sem paginar ainda)."""
        self.tuplas.append(tupla)

    #Paginação global
    def paginar(self) -> None:
        """Reconstrói self.paginas usando self.tuplas e o tamanho da página."""
        self.paginas = []
        pagina_atual = Pagina(numero_pagina=0)

        for t in self.tuplas:
            tam = t.tamanho_em_bytes()

    #Caso extremo: tupla maior que a página -> página só pra ela
            if tam > self.tamanho_pagina_bytes:
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

            pagina_atual.adicionar_tupla(t)

    #fecha a última (garante pelo menos 1)
        if pagina_atual.tuplas or not self.paginas:
            self.paginas.append(pagina_atual)

    #Particionamento + paginação por partição
    def _hash_particao_default(self, chave: str, num_particoes: int) -> int:
        """Hash simples: soma dos códigos dos caracteres mod N (compatível com FuncaoHash)."""
        return sum(ord(c) for c in chave) % num_particoes

    def particionar(
        self,
        num_particoes: int,
        func_hash: Optional[Callable[[str], int]] = None,
    ) -> None:
        """Cria N partições e pagina DENTRO de cada partição."""
        
        if num_particoes <= 0:
            raise ValueError("num_particoes deve ser > 0")

    #Inicializa estrutura: nenhuma página criada ainda
        self.particoes = [[] for _ in range(num_particoes)]
        paginas_atuais: List[Pagina] = [Pagina(numero_pagina=0) for _ in range(num_particoes)]

    #Escolhe função de hash para mapear chave -> partição
        if func_hash is None:
            h = lambda k: self._hash_particao_default(k, num_particoes)
        else:
            h = func_hash  #deve retornar inteiro na faixa [0, num_particoes-1]

        for t in self.tuplas:
            idx = h(t.chave)
            if not (0 <= idx < num_particoes):
    #se a função de hash externa retornar fora do range, normaliza
                idx = idx % num_particoes

            pagina_atual = paginas_atuais[idx]
            tam = t.tamanho_em_bytes()

    #Caso extremo: tupla maior do que o tamanho de página -> só ela na página
            if tam > self.tamanho_pagina_bytes:
    #fecha página atual se tiver algo
                if pagina_atual.tuplas:
                    self.particoes[idx].append(pagina_atual)
                    paginas_atuais[idx] = Pagina(numero_pagina=len(self.particoes[idx]))
                    pagina_atual = paginas_atuais[idx]
                pagina_atual.adicionar_tupla(t)
                self.particoes[idx].append(pagina_atual)
                paginas_atuais[idx] = Pagina(numero_pagina=len(self.particoes[idx]))
                continue

    #se não cabe nesta página da partição, fecha e cria outra
            if pagina_atual.tamanho_atual + tam > self.tamanho_pagina_bytes:
                self.particoes[idx].append(pagina_atual)
                paginas_atuais[idx] = Pagina(numero_pagina=len(self.particoes[idx]))
                pagina_atual = paginas_atuais[idx]

            pagina_atual.adicionar_tupla(t)

    #fecha páginas finais de cada partição (garante pelo menos uma se houve tuplas)
        for i in range(num_particoes):
            pag = paginas_atuais[i]
            if pag.tuplas or not self.particoes[i]:
                self.particoes[i].append(pag)

    def numero_paginas(self) -> int:
        return len(self.paginas)

    def obter_pagina(self, indice: int) -> Pagina:
        return self.paginas[indice]

    def numero_particoes(self) -> int:
        return len(self.particoes)

    def numero_paginas_particao(self, indice_particao: int) -> int:
        return len(self.particoes[indice_particao])

    def obter_pagina_da_particao(self, indice_particao: int, indice_pagina: int) -> Pagina:
        return self.particoes[indice_particao][indice_pagina]

    def particao_da_chave(self, chave: str, num_particoes: Optional[int] = None) -> Optional[int]:
        """Retorna o índice da partição da chave dado o estado atual (se particionado)."""
        if not self.particoes:
            return None
        n = len(self.particoes) if num_particoes is None else num_particoes
        return self._hash_particao_default(chave, n)

    def localizar_por_chave_table_scan(self, chave: str) -> Tuple[Optional[int], Optional[int], int]:
        """Busca linear (table scan) nas páginas globais.
        Retorna (indice_pagina, indice_tupla_na_pagina, custo_em_paginas_lidas)."""
        custo_paginas_lidas = 0
        for idx_pagina, pagina in enumerate(self.paginas):
            custo_paginas_lidas += 1
            for idx_tupla, tupla in enumerate(pagina.tuplas):
                if tupla.chave == chave:
                    return idx_pagina, idx_tupla, custo_paginas_lidas
        return None, None, custo_paginas_lidas

    def __str__(self) -> str:
        return (
            f"Tabela(nome='{self.nome}', tuplas={len(self.tuplas)}, "
            f"paginas={len(self.paginas)}, tamanho_pagina={self.tamanho_pagina_bytes} bytes, "
            f"particoes={len(self.particoes) if self.particoes else 0})"
        )
