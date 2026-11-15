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
            "DOUBLE": "double",
            "CHAR": "char",
            "VOID": "void",
            "LONG": "int",
            "SHORT": "int",
            "UNSIGNED": "int",
            "SIGNED": "int",
        }

        palavras_reservadas = {
            "IF", "ELSE", "WHILE", "FOR", "RETURN", "DO", "SWITCH", "CASE",
            "DEFAULT", "BREAK", "CONTINUE", "SIZEOF", "STRUCT", "CONST", "TYPEDEF",
        }

        # Estado de uma declaração em andamento: "int *a, b = f(x, y);"
        tipo_base = None            # tipo da declaração atual
        profundidade = 0            # nível de parênteses
        profundidade_decl = 0       # nível onde a declaração começou
        aguardando_nome = False     # o próximo identificador é o declarado?
        estrelas = ""

        for i, token in enumerate(tokens):
            if token.tipo == "FIM":
                continue

            if token.tipo in tipos:
                # "unsigned int": a última palavra define o tipo exibido,
                # exceto quando é só um modificador depois do tipo principal.
                if not (aguardando_nome and token.tipo in {"LONG", "SHORT", "UNSIGNED", "SIGNED"}
                        and tipo_base not in (None, "int")):
                    tipo_base = tipos[token.tipo]
                profundidade_decl = profundidade
                aguardando_nome = True
                estrelas = ""

                self.adicionar(token.lexema, "PALAVRA_RESERVADA", tipos[token.tipo], token.linha)
                continue

            if token.tipo in palavras_reservadas:
                self.adicionar(token.lexema, "PALAVRA_RESERVADA", "-", token.linha)
                continue

            if token.tipo == "MUL" and aguardando_nome:
                estrelas += "*"
                continue

            if token.tipo == "PAREN_ESQ":
                profundidade += 1
            elif token.tipo == "PAREN_DIR":
                profundidade -= 1
                if profundidade < profundidade_decl:
                    tipo_base = None
                    aguardando_nome = False
            elif token.tipo in {"PONTO_VIRGULA", "CHAVE_ESQ", "CHAVE_DIR"}:
                tipo_base = None
                aguardando_nome = False
            elif token.tipo == "VIRGULA":
                if tipo_base is not None and profundidade == profundidade_decl:
                    aguardando_nome = True
                    estrelas = ""

            if token.tipo == "IDENTIFICADOR":
                proximo = tokens[i + 1] if i + 1 < len(tokens) else None
                eh_funcao = proximo is not None and proximo.tipo == "PAREN_ESQ"

                if aguardando_nome and tipo_base is not None:
                    tipo = tipo_base + estrelas
                else:
                    tipo = "-"

                self.adicionar(
                    token.lexema,
                    "FUNCAO" if eh_funcao else "IDENTIFICADOR",
                    tipo,
                    token.linha
                )

                aguardando_nome = False

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