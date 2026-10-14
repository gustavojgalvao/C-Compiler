from src.token import Token

class Lexer:
    def __init__(self, code):
        self.codigo = code
        self.cursor = 0
        self.tamanho = len(code)
        self.linha = 1
        self.coluna = 1
    
    def caractere_atual(self):
        if self.cursor < self.tamanho:
            return self.codigo[self.cursor]
        return None

    def avancar(self):
        char = self.caractere_atual()
        
        if char is None:
            return

        self.cursor += 1

        if char == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1

    def pular_espacos(self):
        while self.caractere_atual()  is not None and self.caractere_atual() in " \t\n\r":
            self.avancar()

#Método para tokens de um caractere
    def criar_token_simples(self, tipo):
        lexema = self.caractere_atual()
        linha_inicio = self.linha
        coluna_inicio = self.coluna

        self.avancar()

        return Token(
            tipo,
            lexema,
            linha_inicio,
            coluna_inicio
        )

    def proximo_token(self):
        self.pular_espacos()

        char = self.caractere_atual()
        
        if char is None:
            return Token("FIM", "", self.linha, self.coluna)

        if char.isdigit():
            return self.ler_numero()
        
        if char.isalpha() or char == "_":
            return self.ler_palavra()

        if char == "+":
            return self.criar_token_simples("MAIS")

        if char == "-":
            return self.criar_token_simples("MENOS")

        if char == "*":
            return self.criar_token_simples("MUL")

        if char == "/":
            return self.criar_token_simples("DIV")

        if char == "(":
            return self.criar_token_simples("PAREN_ESQ")

        if char == ")":
            return self.criar_token_simples("PAREN_DIR")

        if char == ";":
            return self.criar_token_simples("PONTO_VIRGULA")

        if char == "{":
            return self.criar_token_simples("CHAVE_ESQ")

        if char == "}":
            return self.criar_token_simples("CHAVE_DIR")

        if char == "=":
            return self.criar_token_simples("IGUAL")

        if char == "!":
            return self.criar_token_simples("NAO")

        if char == "<":
            return self.criar_token_simples("MENOR")

        if char == ">":
            return self.criar_token_simples("MAIOR")

        if char == "&":
            return self.criar_token_simples("E")

        if char == "|":
            return self.criar_token_simples("OU")

        if char == "^":
            return self.criar_token_simples("XOR")

        if char == "%":
            return self.criar_token_simples("MOD")

        if char == ".":
            return self.criar_token_simples("PONTO")

        if char == ",":
            return self.criar_token_simples("VIRGULA")

        if char == "'":
            return self.criar_token_simples("ASPAS_SIMPLES")

        if char == '"':
            return self.criar_token_simples("ASPAS_DUPLAS")

        if char == "#":
            return self.criar_token_simples("CERQUILHA")

        if char == "@":
            return self.criar_token_simples("ARROBA")

        if char == "\\":
            return self.criar_token_simples("BARRA_INV")
        
        raise Exception(
            f"Caractere inválido na linha {self.linha}, "
            f"coluna {self.coluna}: {char!r}"
        )

    def ler_numero(self):
        numero = ""

        linha_inicio = self.linha
        coluna_inicio = self.coluna

        while (
            self.caractere_atual() is not None
            and self.caractere_atual().isdigit()
        ):
            numero += self.caractere_atual()
            self.avancar()

        return Token(
            "NUMERO",
            numero,
            linha_inicio,
            coluna_inicio
        )

    def ler_palavra(self):
        palavra = ""

        linha_inicio = self.linha
        coluna_inicio = self.coluna

        while (
            self.caractere_atual() is not None
            and (
                self.caractere_atual().isalnum()
                or self.caractere_atual() == "_"
            )
        ):
            palavra += self.caractere_atual()
            self.avancar()

        palavras_reservadas = {
            "int": "INT",
            "float": "FLOAT",
            "char": "CHAR",
            "void": "VOID",
            "if": "IF",
            "else": "ELSE",
            "while": "WHILE",
            "for": "FOR",
            "return": "RETURN",
            "do": "DO",
            "switch": "SWITCH",
            "case": "CASE",
            "default": "DEFAULT",
            "break": "BREAK",
            "continue": "CONTINUE",
            "sizeof": "SIZEOF",
            "struct": "STRUCT",
            "const": "CONST",
        }

        tipo = palavras_reservadas.get(
            palavra,
            "IDENTIFICADOR"
        )

        return Token(tipo, palavra, linha_inicio, coluna_inicio)

    def tokenizar(self):
        tokens = []

        while True:
            token = self.proximo_token()
            tokens.append(token)

            if token.tipo == "FIM":
                break

        return tokens