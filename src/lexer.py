from src.token import Token

class Lexer:
    def __init__(self, code):
        self.codigo = code
        self.cursor = 0
        self.tamanho = len(code)
    
    def caractere_atual(self):
        if self.cursor < self.tamanho:
            return self.codigo[self.cursor]
        return None

    def avancar(self):
        self.cursor += 1