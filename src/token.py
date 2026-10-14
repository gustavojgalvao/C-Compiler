class Token:
    def __init__(self,tipo,lexema,linha,coluna):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna
        self.valor = lexema
    def __repr__(self):
        return f"Token({self.tipo}, {self.lexema}, {self.linha}, {self.coluna})"
