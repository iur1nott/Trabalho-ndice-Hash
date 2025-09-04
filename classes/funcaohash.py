class FuncaoHash:
    def __init__(self, numero_tuplas: int, fator_carga: int):
        """
        inicializa a função hash calculando automaticamente o número de buckets
        com base no número de tuplas (NR) e fator de carga (FR)
        """
        self.numero_tuplas = numero_tuplas
        self.fator_carga = fator_carga
        self.numero_buckets = self._calcular_numero_buckets()
    
    def _calcular_numero_buckets(self) -> int:
        """calcula o número de buckets seguindo a fórmula: NB > NR / FR"""
        return max(1, (self.numero_tuplas // self.fator_carga) + 1)
    
    def hash(self, chave: str) -> int:
        """calcula o índice do bucket para uma dada chave"""
        soma = sum(ord(c) for c in chave)
        return soma % self.numero_buckets