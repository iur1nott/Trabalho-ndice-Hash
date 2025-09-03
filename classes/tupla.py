class Tupla:
    def __init__(self, chave: str, dados: str = None):
        """
        construtor da classe
        quando não tiver dados, usa a chave como dados (como é o caso do projeto).
        """
        self.chave = chave
        self.dados = dados if dados is not None else chave

    def serializar(self) -> str:
        """
        retorna representação serializada da tupla
        serialização é necessária pra padronizar armazenamento
        """
        return f"{self.chave}|{self.dados}"
    
    def tamanho_em_bytes(self) -> int:
        """
        calcula o tamanho total da tupla em bytes quando serializada
        usando utf-8 para caso de caracteres especiais
        """
        return len(self.serializar().encode('utf-8'))
    
    @classmethod
    def desserializar(cls, string_serializada: str):
        """
        cria a tupla a partir de uma string serializada
        """
        partes = string_serializada.split('|', 1)
        return cls(partes[0], partes[1])
    
    def __str__(self):
        """
        representação legível se precisar printar a classe
        """
        return f"Tupla(chave='{self.chave}', dados='{self.dados}')"