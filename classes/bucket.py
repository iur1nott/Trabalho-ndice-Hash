from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Ponteiro:
    numero_pagina: int
    indice_tupla: int

class Bucket:
    """
    Bucket enxuto para tratar colisões (chaining).
    Guarda somente ponteiros para registros reais na Tabela.
    """
    __slots__ = ("_enderecos",)

    def __init__(self) -> None:
        self._enderecos: List[Ponteiro] = []

    def inserir(self, ponteiro: Ponteiro) -> None:
        if ponteiro not in self._enderecos:
            self._enderecos.append(ponteiro)

    def remover(self, ponteiro: Ponteiro) -> bool:
        try:
            self._enderecos.remove(ponteiro)
            return True
        except ValueError:
            return False

    def listar(self) -> Tuple[Ponteiro, ...]:
        return tuple(self._enderecos)

    def vazio(self) -> bool:
        return not self._enderecos

    def __len__(self) -> int:
        return len(self._enderecos)

    
    def buscar_enderecos_por_chave(self, tabela, chave: str) -> List[Ponteiro]:
        """
        Retorna apenas os ponteiros cujo registro na Tabela tem a 'chave' informada.
        (Confirma a chave real dentro do bucket, por causa de colisões.)
        """
        resultado: List[Ponteiro] = []
        for p in self._enderecos:
            tupla = tabela.paginas[p.numero_pagina].tuplas[p.indice_tupla]
            if tupla and tupla.chave == chave:
                resultado.append(p)
        return resultado
