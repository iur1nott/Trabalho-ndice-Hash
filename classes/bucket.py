from typing import List, Optional
from .tupla import Tupla

class Bucket:
    def __init__(self, capacidade: int, numero_bucket: int):
        """
        Inicializa um bucket com capacidade máxima de entradas.
        Cada entrada é uma tupla (chave, numero_pagina).
        """
        self.capacidade = capacidade
        self.numero_bucket = numero_bucket
        self.entradas = []  # Lista de tuplas (chave, numero_pagina)
        self.overflow = None  # Pode apontar para outro bucket de overflow (encadeamento)

    def adicionar_entrada(self, chave: str, numero_pagina: int) -> bool:
        """
        Adiciona uma entrada (chave, numero_pagina) ao bucket.
        Retorna True se conseguiu adicionar, False se houve overflow.
        Em caso de overflow, tenta adicionar no bucket de overflow encadeado.
        """
        if len(self.entradas) < self.capacidade:
            self.entradas.append((chave, numero_pagina))
            return True
        else:
            # Tenta adicionar no bucket de overflow
            if self.overflow is None:
                self.overflow = Bucket(self.capacidade, self.numero_bucket)  # mesmo "número lógico"
            return self.overflow.adicionar_entrada(chave, numero_pagina)

    def buscar_chave(self, chave: str) -> Optional[int]:
        """
        Busca a chave no bucket e retorna o número da página onde está armazenada.
        Se não encontrar, busca no bucket de overflow (se existir).
        Retorna None se não encontrar em nenhum.
        """
        for k, pagina in self.entradas:
            if k == chave:
                return pagina
        if self.overflow:
            return self.overflow.buscar_chave(chave)
        return None

    def contar_colisoes(self) -> int:
        """
        Conta quantas colisões ocorreram neste bucket e seus overflows.
        Colisão = número de chaves inseridas após a primeira no bucket (principal ou overflow).
        """
        # No bucket atual: se tem N entradas, houve max(0, N - 1) colisões
        colisoes = max(0, len(self.entradas) - 1)
        if self.overflow:
            colisoes += self.overflow.contar_colisoes()
        return colisoes

    def contar_overflows(self) -> int:
        """
        Conta quantos buckets de overflow foram criados a partir deste.
        """
        if self.overflow is None:
            return 0
        else:
            return 1 + self.overflow.contar_overflows()

    def __str__(self) -> str:
        s = f"Bucket {self.numero_bucket}: {len(self.entradas)} entradas"
        if self.overflow:
            s += f" + {self.contar_overflows()} overflow(s)"
        return s