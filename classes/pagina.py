class Pagina:
    def __init__(self, numero_pagina: int):
        self.numero_pagina = numero_pagina  # id da página
        self.tuplas = []        # lista de tuplas nesta página
        self.tamanho_atual = 0  # tamanho da página para comparação

    def adicionar_tupla(self, tupla: Tupla) -> None:
        """ adiciona uma tupla à página e atualiza o tamanho total. """
        self.tuplas.append(tupla)
        self.tamanho_atual += tupla.tamanho_em_bytes()

    def esta_cheia(self, tamanho_maximo: int) -> bool:
        """ verifica se a página atingiu a capacidade máxima """
        return self.tamanho_atual >= tamanho_maximo

    def __str__(self) -> str:
        """ representação da página para prints """
        return f"Página {self.numero_pagina} com {len(self.tuplas)} tuplas ({self.tamanho_atual} bytes)"