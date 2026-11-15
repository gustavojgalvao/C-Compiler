from src.token import Token
from src.erros import ErroLexico


PALAVRAS_RESERVADAS = {
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

TOKENS_SIMPLES = {
    "+": "MAIS",
    "-": "MENOS",
    "*": "MUL",
    "/": "DIV",
    "(": "PAREN_ESQ",
    ")": "PAREN_DIR",
    ";": "PONTO_VIRGULA",
    "{": "CHAVE_ESQ",
    "}": "CHAVE_DIR",
    "=": "IGUAL",
    "!": "NAO",
    "<": "MENOR",
    ">": "MAIOR",
    "&": "E",
    "|": "OU",
    "^": "XOR",
    "%": "MOD",
    ".": "PONTO",
    ",": "VIRGULA",
    "#": "CERQUILHA",
    "@": "ARROBA",
    "\\": "BARRA_INV",
}


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

    def espiar(self, distancia=1):
        indice = self.cursor + distancia

        if indice < self.tamanho:
            return self.codigo[indice]
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
        """Ignora espaços em branco e comentários (// e /* */)."""
        while self.caractere_atual() is not None:
            char = self.caractere_atual()

            if char in " \t\n\r":
                self.avancar()
                continue

            if char == "/" and self.espiar() == "/":
                while (
                    self.caractere_atual() is not None
                    and self.caractere_atual() != "\n"
                ):
                    self.avancar()
                continue

            if char == "/" and self.espiar() == "*":
                linha_inicio = self.linha
                coluna_inicio = self.coluna

                self.avancar()
                self.avancar()

                while not (
                    self.caractere_atual() == "*"
                    and self.espiar() == "/"
                ):
                    if self.caractere_atual() is None:
                        raise ErroLexico(
                            "Comentário de bloco não finalizado",
                            linha_inicio,
                            coluna_inicio
                        )
                    self.avancar()

                self.avancar()
                self.avancar()
                continue

            break

    # Método para tokens de um caractere
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

        if char == "'":
            return self.ler_caractere()

        if char == '"':
            return self.ler_texto()

        if char in TOKENS_SIMPLES:
            return self.criar_token_simples(TOKENS_SIMPLES[char])

        raise ErroLexico(
            f"Caractere inválido {char!r}",
            self.linha,
            self.coluna
        )

    def ler_numero(self):
        numero = ""
        possui_ponto = False

        linha_inicio = self.linha
        coluna_inicio = self.coluna

        while self.caractere_atual() is not None:
            char = self.caractere_atual()

            if char.isdigit():
                numero += char
                self.avancar()
                continue

            if (
                char == "."
                and not possui_ponto
                and self.espiar() is not None
                and self.espiar().isdigit()
            ):
                possui_ponto = True
                numero += char
                self.avancar()
                continue

            break

        atual = self.caractere_atual()

        if atual is not None and (atual.isalpha() or atual == "_"):
            raise ErroLexico(
                f"Número malformado '{numero}{atual}'",
                linha_inicio,
                coluna_inicio
            )

        tipo = "NUMERO_REAL" if possui_ponto else "NUMERO"

        return Token(
            tipo,
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

        tipo = PALAVRAS_RESERVADAS.get(
            palavra,
            "IDENTIFICADOR"
        )

        return Token(tipo, palavra, linha_inicio, coluna_inicio)

    def ler_caractere(self):
        linha_inicio = self.linha
        coluna_inicio = self.coluna

        self.avancar()

        char = self.caractere_atual()

        if char is None or char == "\n" or char == "'":
            raise ErroLexico(
                "Literal de caractere inválido",
                linha_inicio,
                coluna_inicio
            )

        valor = char
        self.avancar()

        if self.caractere_atual() != "'":
            raise ErroLexico(
                "Esperada aspas simples de fechamento",
                self.linha,
                self.coluna
            )

        self.avancar()

        return Token(
            "CARACTERE",
            valor,
            linha_inicio,
            coluna_inicio
        )

    def ler_texto(self):
        texto = ""

        linha_inicio = self.linha
        coluna_inicio = self.coluna

        self.avancar()

        while (
            self.caractere_atual() is not None
            and self.caractere_atual() != '"'
        ):
            if self.caractere_atual() == "\n":
                raise ErroLexico(
                    "Texto não finalizado",
                    linha_inicio,
                    coluna_inicio
                )

            texto += self.caractere_atual()
            self.avancar()

        if self.caractere_atual() is None:
            raise ErroLexico(
                "Texto não finalizado",
                linha_inicio,
                coluna_inicio
            )

        self.avancar()

        return Token(
            "TEXTO",
            texto,
            linha_inicio,
            coluna_inicio
        )

    def tokenizar(self):
        tokens = []

        while True:
            token = self.proximo_token()
            tokens.append(token)

            if token.tipo == "FIM":
                break

        return tokens
