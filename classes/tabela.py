from typing import List, Dict, Optional
from .pagina import Pagina
from .tupla import Tupla
from .bucket import Bucket
from .funcaohash import FuncaoHash
import os

class Tabela:
    def __init__(self, caminho_arquivo: str, tamanho_pagina_bytes: int, fator_carga: int):
        """
        Inicializa a tabela carregando dados do arquivo, dividindo em páginas,
        e preparando a estrutura para construção do índice hash.
        """
        self.caminho_arquivo = caminho_arquivo
        self.tamanho_pagina_bytes = tamanho_pagina_bytes
        self.fator_carga = fator_carga  # FR: número máximo de tuplas por bucket

        # Estruturas principais
        self.tuplas: List[Tupla] = []
        self.paginas: List[Pagina] = []
        self.buckets: List[Bucket] = []
        self.funcao_hash: Optional[FuncaoHash] = None
        self.indice_construido = False

        # Estatísticas
        self.total_colisoes = 0
        self.total_overflows = 0

        # Carrega e inicializa
        self._carregar_dados()
        self._dividir_em_paginas()

    def _carregar_dados(self):
        """Carrega todas as linhas do arquivo como tuplas."""
        if not os.path.exists(self.caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho_arquivo}")

        with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                palavra = linha.strip()
                if palavra:  # ignora linhas vazias
                    self.tuplas.append(Tupla(palavra))

    def _dividir_em_paginas(self):
        """Divide as tuplas em páginas de acordo com o tamanho máximo."""
        numero_pagina = 1
        pagina_atual = Pagina(numero_pagina)

        for tupla in self.tuplas:
            if pagina_atual.esta_cheia(self.tamanho_pagina_bytes):
                self.paginas.append(pagina_atual)
                numero_pagina += 1
                pagina_atual = Pagina(numero_pagina)
            pagina_atual.adicionar_tupla(tupla)

        # Adiciona a última página, mesmo que não esteja cheia
        if pagina_atual.tuplas:
            self.paginas.append(pagina_atual)

    def construir_indice_hash(self):
        """
        Constrói o índice hash:
        - Calcula número de buckets (NB)
        - Cria buckets
        - Aplica função hash em cada tupla e mapeia chave -> página
        """
        self.funcao_hash = FuncaoHash(len(self.tuplas), self.fator_carga)
        nb = self.funcao_hash.numero_buckets

        # Inicializa buckets
        self.buckets = [Bucket(self.fator_carga, i) for i in range(nb)]

        # Para cada tupla, descobre em qual página ela está e adiciona ao bucket
        for pagina in self.paginas:
            for tupla in pagina.tuplas:
                indice_bucket = self.funcao_hash.hash(tupla.chave)
                bucket = self.buckets[indice_bucket]
                bucket.adicionar_entrada(tupla.chave, pagina.numero_pagina)

        self.indice_construido = True
        self._calcular_estatisticas()

    def _calcular_estatisticas(self):
        total_colisoes = 0
        total_overflows = 0

        for bucket in self.buckets:
            total_colisoes += bucket.contar_colisoes()
            total_overflows += bucket.contar_overflows()

        self.total_colisoes = total_colisoes
        self.total_overflows = total_overflows

    def buscar_com_indice(self, chave: str) -> tuple[Optional[Tupla], int]:
        """
        Busca uma tupla usando o índice hash.
        Retorna (tupla_encontrada, custo_total_em_paginas_lidas).

        Modelo de custo:
        - +1 por cada bucket/overflow visitado (acesso ao índice).
        - +1 se precisar ler a página de dados (se a chave existir).
        """
        if not self.indice_construido:
            raise RuntimeError("Índice hash não foi construído. Chame construir_indice_hash() primeiro.")

        indice_bucket = self.funcao_hash.hash(chave)
        bucket = self.buckets[indice_bucket]

        # custo no índice (buckets lidos)
        numero_pagina, buckets_lidos = bucket.buscar_chave_com_custo(chave)

        if numero_pagina is None:
            # não achou: custo = só o que gastou no índice
            return None, buckets_lidos

        # achou a página: +1 I/O de dados
        custo_total = buckets_lidos + 1

        # valida dentro da página
        pagina = self._obter_pagina_por_numero(numero_pagina)
        if pagina:
            for tupla in pagina.tuplas:
                if tupla.chave == chave:
                    return tupla, custo_total

        # chave não está na página esperada (inconsistência): conta I/O mesmo assim
        return None, custo_total


    def table_scan(self, chave: str) -> tuple[Optional[Tupla], List[Tupla], int]:
        """
        Realiza um table scan: lê página por página até encontrar a chave.
        Retorna:
        - tupla encontrada (ou None)
        - lista de tuplas lidas até encontrar (inclusive)
        - número de páginas lidas
        """
        custo = 0
        tuplas_lidas = []

        for pagina in self.paginas:
            custo += 1
            for tupla in pagina.tuplas:
                tuplas_lidas.append(tupla)  # acumula todas lidas
                if tupla.chave == chave:
                    return tupla, tuplas_lidas, custo
        return None, tuplas_lidas, custo


    def _obter_pagina_por_numero(self, numero: int) -> Optional[Pagina]:
        """Retorna a página com o número especificado."""
        for pagina in self.paginas:
            if pagina.numero_pagina == numero:
                return pagina
        return None

    @property
    def taxa_colisoes(self) -> float:
        """Taxa de colisões: número de colisões / número total de inserções."""
        if len(self.tuplas) == 0:
            return 0.0
        return self.total_colisoes / len(self.tuplas)

    @property
    def taxa_overflows(self) -> float:
        """Taxa de overflows: número de buckets com overflow / número total de buckets."""
        if len(self.buckets) == 0:
            return 0.0
        buckets_com_overflow = sum(1 for b in self.buckets if b.overflow is not None)
        return buckets_com_overflow / len(self.buckets)

    def __str__(self) -> str:
        return (
            f"Tabela com {len(self.tuplas)} tuplas, "
            f"{len(self.paginas)} páginas, "
            f"{len(self.buckets)} buckets. "
            f"Colisões: {self.total_colisoes}, "
            f"Overflows: {self.total_overflows}"
        )