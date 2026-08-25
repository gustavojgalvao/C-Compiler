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

    def pular_espacos(self):
        while self.caractere_atual()  is not None and self.caractere_atual() in " \t\n\r":
            self.avancar()

    def proximo_token(self):
        self.pular_espacos()

        char = self.caractere_atual()
        
        if char is None:
            return Token("FIM", "")

        if char.isdigit():
            return self.ler_numero()
        
        if char.isalpha() or char == "_":
            return self.ler_palavra()

        if char == "+":
            self.avancar()
            return Token("MAIS", "+")

        if char == "-":
            self.avancar()
            return Token("MENOS", "-")
            
        if char == "*":
            self.avancar()
            return Token("MUL", "*")
            
        if char == "/":
            self.avancar()
            return Token("DIV", "/")
            
        if char == "(":
            self.avancar()
            return Token("PAREN_ESQ", "(")
            
        if char == ")":
            self.avancar()
            return Token("PAREN_DIR", ")")

        if char == ";":
            self.avancar()
            return Token("PONTO_VIRGULA", ";")

        if char == "{":
            self.avancar()
            return Token("CHAVE_ESQ", "{")
            
        if char == "}":
            self.avancar()
            return Token("CHAVE_DIR", "}")
        
        if char == "=":
            self.avancar()
            return Token("IGUAL", "=")
        
        if char == "!":
            self.avancar()
            return Token("NAO", "!")
        
        if char == "<":
            self.avancar()
            return Token("MENOR", "<")
        
        if char == ">":
            self.avancar()
            return Token("MAIOR", ">")
        
        if char == "&":
            self.avancar()
            return Token("E", "&")
        
        if char == "|":
            self.avancar()
            return Token("OU", "|")
        
        if char == "^":
            self.avancar()
            return Token("XOR", "^")
        
        if char == "%":
            self.avancar()
            return Token("MOD", "%")
        
        if char == ".":
            self.avancar()
            return Token("PONTO", ".")
        
        if char == ",":
            self.avancar()
            return Token("VIRGULA", ",")
        
        if char == "'":
            self.avancar()
            return Token("ASPAS_SIMPLES", "'")
        
        if char == '"':
            self.avancar()
            return Token("ASPAS_DUPLAS", '"')
        
        if char == "#":
            self.avancar()
            return Token("CERQUILHA", "#")
        
        if char == "@":
            self.avancar()
            return Token("arroba", "@")
        
        if char == "\\":
            self.avancar()
            return Token("BARRA_INV", "\\")

        raise Exception(f"Caractere inválido: {char}")

    def ler_numero(self):
        numero = ""
        while self.caractere_atual() is not None and self.caractere_atual().isdigit():
            numero += self.caractere_atual()
            self.avancar()
        return Token("NUMERO", int(numero))

    def ler_palavra(self):
        palavra = ""
        while self.caractere_atual() is not None and (self.caractere_atual().isalnum() or
        self.caractere_atual() == "_"):
            palavra += self.caractere_atual()
            self.avancar()


    
    