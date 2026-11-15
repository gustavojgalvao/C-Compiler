from src.token import Token
from src.erros import ErroLexico


PALAVRAS_RESERVADAS = {
    "int": "INT",
    "float": "FLOAT",
    "double": "DOUBLE",
    "char": "CHAR",
    "void": "VOID",
    "long": "LONG",
    "short": "SHORT",
    "unsigned": "UNSIGNED",
    "signed": "SIGNED",
    "const": "CONST",
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
    "typedef": "TYPEDEF",
}

# Operadores de três caracteres (verificados antes dos de dois).
TOKENS_TRIPLOS = {
    "<<=": "DESLOC_ESQ_IGUAL",
    ">>=": "DESLOC_DIR_IGUAL",
    "...": "RETICENCIAS",
}

# Operadores de dois caracteres (verificados antes dos de um caractere).
TOKENS_DUPLOS = {
    "==": "IGUAL_IGUAL",
    "!=": "DIFERENTE",
    "<=": "MENOR_IGUAL",
    ">=": "MAIOR_IGUAL",
    "&&": "E_LOGICO",
    "||": "OU_LOGICO",
    "++": "INCREMENTO",
    "--": "DECREMENTO",
    "+=": "MAIS_IGUAL",
    "-=": "MENOS_IGUAL",
    "*=": "MUL_IGUAL",
    "/=": "DIV_IGUAL",
    "%=": "MOD_IGUAL",
    "&=": "E_IGUAL",
    "|=": "OU_IGUAL",
    "^=": "XOR_IGUAL",
    "<<": "DESLOC_ESQ",
    ">>": "DESLOC_DIR",
    "->": "SETA",
}

TOKENS_SIMPLES = {
    "+": "MAIS",
    "-": "MENOS",
    "*": "MUL",
    "/": "DIV",
    "(": "PAREN_ESQ",
    ")": "PAREN_DIR",
    "[": "COLCHETE_ESQ",
    "]": "COLCHETE_DIR",
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
    "~": "TIL",
    "%": "MOD",
    "?": "INTERROGACAO",
    ":": "DOIS_PONTOS",
    ".": "PONTO",
    ",": "VIRGULA",
}

ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "0": "\0",
    "\\": "\\", "'": "'", '"': '"', "a": "\a", "b": "\b", "f": "\f", "v": "\v",
}

MAX_EXPANSAO_MACRO = 32


class Lexer:
    def __init__(self, code):
        # Arquivos salvos como "UTF-8 com BOM" começam com um caractere invisível.
        if code.startswith("\ufeff"):
            code = code[1:]

        self.codigo = code
        self.cursor = 0
        self.tamanho = len(code)
        self.linha = 1
        self.coluna = 1
        # #define NOME valor  ->  {"NOME": [tokens do valor]}
        self.macros = {}
        # Nomes vindos de #include <...> (apenas informativo).
        self.inclusoes = []

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

    def no_inicio_da_linha(self):
        """Verdadeiro se só há espaços entre o início da linha e o cursor."""
        inicio = self.codigo.rfind("\n", 0, self.cursor) + 1
        return self.codigo[inicio:self.cursor].strip() == ""

    def pular_espacos(self):
        """Ignora espaços, comentários (// e /* */) e diretivas (#...)."""
        while self.caractere_atual() is not None:
            char = self.caractere_atual()

            if char in " \t\n\r\f\v":
                self.avancar()
                continue

            if char == "#" and self.no_inicio_da_linha():
                self.ler_diretiva()
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

    def ler_diretiva(self):
        """
        Lê uma linha do pré-processador (aceita continuação com '\\').
        #define NOME valor  -> registra uma macro simples
        #include <arquivo>   -> apenas anotado; demais diretivas são ignoradas
        """
        linha_inicio = self.linha
        texto = ""

        self.avancar()  # '#'

        while self.caractere_atual() is not None and self.caractere_atual() != "\n":
            if self.caractere_atual() == "\\" and self.espiar() == "\n":
                self.avancar()
                self.avancar()
                texto += " "
                continue
            texto += self.caractere_atual()
            self.avancar()

        partes = texto.strip().split(None, 1)

        if not partes:
            return

        diretiva = partes[0]
        resto = partes[1] if len(partes) > 1 else ""

        if diretiva == "include":
            self.inclusoes.append(resto.strip("<>\" "))

        elif diretiva == "define" and resto:
            nome = ""
            i = 0
            while i < len(resto) and (resto[i].isalnum() or resto[i] == "_"):
                nome += resto[i]
                i += 1

            # Macros com parâmetros, como #define MAX(a,b), não são suportadas.
            if not nome or (i < len(resto) and resto[i] == "("):
                return

            corpo = resto[i:]
            try:
                tokens = Lexer(corpo).tokenizar()[:-1]
            except ErroLexico as erro:
                raise ErroLexico(
                    f"Valor inválido no #define {nome}: {erro.mensagem}",
                    linha_inicio,
                    1
                )
            self.macros[nome] = tokens

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

        if char.isdigit() or (char == "." and (self.espiar() or "").isdigit()):
            return self.ler_numero()

        if char.isalpha() or char == "_":
            return self.ler_palavra()

        if char == "'":
            return self.ler_caractere()

        if char == '"':
            return self.ler_texto()

        trio = char + (self.espiar() or "") + (self.espiar(2) or "")

        if trio in TOKENS_TRIPLOS:
            token = Token(TOKENS_TRIPLOS[trio], trio, self.linha, self.coluna)
            for _ in range(3):
                self.avancar()
            return token

        par = trio[:2]

        if par in TOKENS_DUPLOS:
            token = Token(TOKENS_DUPLOS[par], par, self.linha, self.coluna)
            self.avancar()
            self.avancar()
            return token

        if char in TOKENS_SIMPLES:
            return self.criar_token_simples(TOKENS_SIMPLES[char])

        raise ErroLexico(
            f"Caractere inválido {char!r}",
            self.linha,
            self.coluna
        )

    def ler_numero(self):
        if self.caractere_atual() == "0" and (self.espiar() or "") in "xX":
            return self.ler_hexadecimal()

        numero = ""
        possui_ponto = False
        possui_expoente = False

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
                and not possui_expoente
            ):
                possui_ponto = True
                numero += char
                self.avancar()
                continue

            # Notação científica: 1e5, 2.5E-3
            if char in "eE" and not possui_expoente:
                proximo = self.espiar() or ""
                depois = self.espiar(2) or ""
                if proximo.isdigit() or (proximo in "+-" and depois.isdigit()):
                    possui_expoente = True
                    numero += char
                    self.avancar()
                    if proximo in "+-":
                        numero += proximo
                        self.avancar()
                    continue

            break

        # Sufixos: 1.5f, 10L, 3u
        sufixo = ""
        while (
            self.caractere_atual() is not None
            and self.caractere_atual() in "fFlLuU"
        ):
            sufixo += self.caractere_atual()
            self.avancar()

        atual = self.caractere_atual()

        if atual is not None and (atual.isalnum() or atual == "_"):
            raise ErroLexico(
                f"Número malformado '{numero}{sufixo}{atual}'",
                linha_inicio,
                coluna_inicio
            )

        real = possui_ponto or possui_expoente or (
            "f" in sufixo.lower() and "." in numero
        )
        tipo = "NUMERO_REAL" if real else "NUMERO"

        return Token(
            tipo,
            numero + sufixo,
            linha_inicio,
            coluna_inicio
        )

    def ler_hexadecimal(self):
        linha_inicio = self.linha
        coluna_inicio = self.coluna
        numero = "0" + self.espiar()

        self.avancar()
        self.avancar()

        while (
            self.caractere_atual() is not None
            and self.caractere_atual() in "0123456789abcdefABCDEF"
        ):
            numero += self.caractere_atual()
            self.avancar()

        while (
            self.caractere_atual() is not None
            and self.caractere_atual() in "lLuU"
        ):
            numero += self.caractere_atual()
            self.avancar()

        atual = self.caractere_atual()

        if len(numero.rstrip("lLuU")) == 2 or (
            atual is not None and (atual.isalnum() or atual == "_")
        ):
            raise ErroLexico(
                f"Número hexadecimal malformado '{numero}{atual or ''}'",
                linha_inicio,
                coluna_inicio
            )

        return Token("NUMERO", numero, linha_inicio, coluna_inicio)

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

    def ler_escape(self):
        """Lê uma sequência de escape (o cursor está na barra) e devolve o texto original."""
        self.avancar()  # '\'
        char = self.caractere_atual()

        if char is None or char not in ESCAPES:
            raise ErroLexico(
                f"Sequência de escape inválida '\\{char or ''}'",
                self.linha,
                self.coluna - 1
            )

        self.avancar()
        return "\\" + char

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

        if char == "\\":
            valor = self.ler_escape()
        else:
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

            if self.caractere_atual() == "\\":
                texto += self.ler_escape()
                continue

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

    def expandir_macro(self, token, profundidade=0):
        """Substitui um identificador definido por #define pelos tokens do seu valor."""
        if profundidade > MAX_EXPANSAO_MACRO:
            raise ErroLexico(
                f"Macro '{token.lexema}' se expande infinitamente",
                token.linha,
                token.coluna
            )

        resultado = []

        for original in self.macros[token.lexema]:
            copia = Token(original.tipo, original.lexema, token.linha, token.coluna)

            if copia.tipo == "IDENTIFICADOR" and copia.lexema in self.macros:
                resultado.extend(self.expandir_macro(copia, profundidade + 1))
            else:
                resultado.append(copia)

        return resultado

    def tokenizar(self):
        tokens = []

        while True:
            token = self.proximo_token()

            if token.tipo == "IDENTIFICADOR" and token.lexema in self.macros:
                tokens.extend(self.expandir_macro(token))
                continue

            tokens.append(token)

            if token.tipo == "FIM":
                break

        return tokens
