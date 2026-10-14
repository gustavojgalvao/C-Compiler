class Simbolo:
    def __init__(self, ordem, lexema, categoria, tipo, linha):
        self.ordem = ordem
        self.lexema = lexema
        self.categoria = categoria
        self.tipo = tipo
        self.linha = linha

    def __repr__(self):
        return (
            f"{self.ordem:<6} "
            f"{self.lexema:<18} "
            f"{self.categoria:<22} "
            f"{self.tipo:<10} "
            f"{self.linha}"
        )

class TabelaSimbolos:
    def __init__(self):
        self.simbolos = []
    
    def buscar(self, lexema):
        for simbolo in self.simbolos:
            if simbolo.lexema == lexema:
                return simbolo
        return None

    def adicionar(self, lexema, categoria, tipo, linha):
        existente = self.buscar(lexema)

        if existente is not None:
            if existente.tipo == "-" and tipo != "-":
                existente.tipo = tipo
                return existente

        ordem = len(self.simbolos) + 1

        simbolo = Simbolo(
            ordem,
            lexema,
            categoria,
            tipo,
            linha
        )

        self.simbolos.append(simbolo)
        return simbolo

    def construir(self, tokens):
        tipos = {
            "INT": "int",
            "FLOAT": "float",
            "CHAR": "char",
            "VOID": "void"
        }

        palavras_reservadas = {
            "IF",
            "ELSE",
            "WHILE",
            "FOR",
            "RETURN",
            "DO",
            "SWITCH",
            "CASE",
            "DEFAULT",
            "BREAK",
            "CONTINUE",
            "SIZEOF",
            "STRUCT",
            "CONST"
        }

        tipo_pendente = None

        for token in tokens:
            if token.tipo == "FIM":
                continue

            if token.tipo in tipos:
                tipo_pendente = tipos[token.tipo]

                self.adicionar(
                    token.lexema,
                    "PALAVRA_RESERVADA",
                    tipo_pendente,
                    token.linha
                )

                continue

            if token.tipo in palavras_reservadas:
                self.adicionar(
                    token.lexema,
                    "PALAVRA_RESERVADA",
                    "-",
                    token.linha
                )

                continue

            if token.tipo == "IDENTIFICADOR":
                tipo = tipo_pendente if tipo_pendente is not None else "-"

                self.adicionar(
                    token.lexema,
                    "IDENTIFICADOR",
                    tipo,
                    token.linha
                )

                tipo_pendente = None

        return self
    
    def exibir(self):
        print("\nTABELA DE SÍMBOLOS")
        print("-" * 70)
        print(
            f"{'ORDEM':<6} "
            f"{'LEXEMA':<18} "
            f"{'CATEGORIA':<22} "
            f"{'TIPO':<10} "
            f"LINHA"
        )
        print("-" * 70)

        for simbolo in self.simbolos:
            print(simbolo)