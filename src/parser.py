from src.arvore_sintatica import (
    Programa, Funcao, Parametro, Declaracao, DefinicaoStruct, ListaInicializadora,
    Bloco, Se, Enquanto, FacaEnquanto, Para, Escolha, Caso, Pare, Continue,
    ComandoVazio, Retorno,
    Numero, NumeroReal, Caractere, Texto, Identificador,
    OperacaoUnaria, IncrementoDecremento, OperacaoBinaria, Atribuicao,
    Condicional, Chamada, Indexacao, Conversao, Tamanho, Acesso, Sequencia,
)
from src.erros import ErroSintatico

__all__ = ["Parser", "ErroSintatico"]


# Palavras que podem iniciar um tipo: "unsigned long int", "const char", ...
TOKENS_DE_TIPO = {
    "INT", "FLOAT", "DOUBLE", "CHAR", "VOID",
    "LONG", "SHORT", "UNSIGNED", "SIGNED", "CONST",
}

# Nomes de tipo das bibliotecas padrão, tratados como apelidos (typedef).
APELIDOS_PADRAO = {
    "bool": "int",
    "_Bool": "int",
    "size_t": "int",
    "FILE": "void",
}

OPERADORES_ATRIBUICAO = {
    "IGUAL", "MAIS_IGUAL", "MENOS_IGUAL", "MUL_IGUAL", "DIV_IGUAL", "MOD_IGUAL",
    "E_IGUAL", "OU_IGUAL", "XOR_IGUAL", "DESLOC_ESQ_IGUAL", "DESLOC_DIR_IGUAL",
}


class Parser:
    """
    Parser descendente recursivo para um subconjunto de C.

        programa     -> externo* FIM
        externo      -> funcao | declaracao | typedef | comando
        funcao       -> tipo IDENT "(" parametros ")" (bloco | ";")
        declaracao   -> tipo (declarador ("," declarador)*)? ";"
        declarador   -> "*"* IDENT ("[" expressao? "]")* ("=" (atribuicao | lista))?
        tipo         -> palavras de tipo | "struct" IDENT? ("{" campos "}")? | apelido
        comando      -> bloco | if | while | do-while | for | switch
                      | break ";" | continue ";" | return expressao? ";"
                      | declaracao | expressao ";" | ";"

        expressao    -> atribuicao ("," atribuicao)*
        atribuicao   -> condicional (op_atribuicao atribuicao)?
        condicional  -> ou ("?" expressao ":" condicional)?
        ou -> e -> bit_ou -> bit_xor -> bit_e -> igualdade -> relacional
           -> deslocamento -> soma -> termo          (do mais fraco ao mais forte)
        unario       -> ("-" | "+" | "!" | "~" | "&" | "*" | "++" | "--") unario
                      | "(" tipo ")" unario | "sizeof" ... | posfixo
        posfixo      -> primario ("(" argumentos ")" | "[" expressao "]"
                                  | "." IDENT | "->" IDENT | "++" | "--")*
        primario     -> NUMERO | NUMERO_REAL | CARACTERE | TEXTO | IDENT | "(" expressao ")"

    Comandos soltos fora de funções também são aceitos: nesse caso o
    arquivo é tratado como o corpo de "int main()".
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0
        self.apelidos = dict(APELIDOS_PADRAO)   # nomes criados por typedef
        self.structs_pendentes = []             # definições achadas dentro de um tipo
        self.contador_anonimas = 0

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------

    def token_atual(self):
        return self.tokens[self.posicao]

    def espiar(self, distancia=1):
        indice = min(self.posicao + distancia, len(self.tokens) - 1)
        return self.tokens[indice]

    def avancar(self):
        token = self.token_atual()

        if token.tipo != "FIM":
            self.posicao += 1
        return token

    def verificar(self, *tipos):
        return self.token_atual().tipo in tipos

    def consumir(self, tipo, mensagem):
        token = self.token_atual()

        if token.tipo != tipo:
            raise ErroSintatico(mensagem, token)

        self.avancar()
        return token

    def inicia_tipo(self, token=None):
        token = token or self.token_atual()
        return (
            token.tipo in TOKENS_DE_TIPO
            or token.tipo == "STRUCT"
            or (token.tipo == "IDENTIFICADOR" and token.lexema in self.apelidos)
        )

    def com_pendentes(self, itens):
        """Põe na frente as structs definidas dentro de um tipo já lido."""
        pendentes = self.structs_pendentes
        self.structs_pendentes = []
        return pendentes + itens

    # ------------------------------------------------------------------
    # Programa e funções
    # ------------------------------------------------------------------

    def analisar(self):
        programa = Programa()

        while not self.verificar("FIM"):
            for item in self.ler_externo():
                programa.adicionar(item)

        return programa

    def ler_externo(self):
        """Lê uma função, uma declaração global, um typedef ou um comando solto."""
        if self.verificar("TYPEDEF"):
            return self.ler_typedef()

        if not self.inicia_tipo():
            return self.ler_comando()

        tipo_base, token_tipo = self.ler_tipo_base()

        if self.verificar("PONTO_VIRGULA"):        # "struct Aluno { ... };"
            self.avancar()
            return self.com_pendentes([])

        estrelas = self.ler_ponteiros()
        token_nome = self.consumir("IDENTIFICADOR", "Esperando nome de variável ou função")

        if self.verificar("PAREN_ESQ"):
            funcao = self.ler_funcao(tipo_base + estrelas, token_nome, token_tipo)
            return self.com_pendentes([funcao])

        declaracoes = self.ler_declaradores(tipo_base, token_tipo, (estrelas, token_nome))
        return self.com_pendentes(declaracoes)

    def ler_tipo_base(self):
        """Lê 'unsigned long int', 'struct Aluno' ou um apelido e devolve o tipo."""
        primeiro = self.token_atual()
        palavras = set()
        especial = None

        while True:
            token = self.token_atual()
            sem_palavras = not (palavras - {"CONST"})

            if token.tipo in TOKENS_DE_TIPO:
                palavras.add(self.avancar().tipo)
            elif token.tipo == "STRUCT" and especial is None and sem_palavras:
                especial = self.ler_struct()
            elif (
                token.tipo == "IDENTIFICADOR"
                and token.lexema in self.apelidos
                and especial is None
                and sem_palavras
            ):
                self.avancar()
                especial = self.apelidos[token.lexema]
            else:
                break

        palavras.discard("CONST")

        if especial is not None:
            if palavras:
                raise ErroSintatico("Combinação de tipos inválida", primeiro)
            return especial, primeiro

        if not palavras:
            raise ErroSintatico("Esperado um tipo", self.token_atual())

        if "VOID" in palavras:
            tipo = "void"
        elif "DOUBLE" in palavras:
            tipo = "double"
        elif "FLOAT" in palavras:
            tipo = "float"
        elif "CHAR" in palavras:
            tipo = "char"
        else:
            tipo = "int"        # int, long, short, unsigned, signed

        return tipo, primeiro

    def ler_struct(self):
        """Lê 'struct Nome' ou 'struct Nome { campos }' e devolve 'struct Nome'."""
        token_struct = self.consumir("STRUCT", "Esperado 'struct'")
        nome = None

        if self.verificar("IDENTIFICADOR"):
            nome = self.avancar().lexema

        if not self.verificar("CHAVE_ESQ"):
            if nome is None:
                raise ErroSintatico("Esperado o nome da struct", self.token_atual())
            return f"struct {nome}"

        if nome is None:
            self.contador_anonimas += 1
            nome = f"__anonima{self.contador_anonimas}"

        self.avancar()  # '{'
        campos = []

        while not self.verificar("CHAVE_DIR"):
            if self.verificar("FIM"):
                raise ErroSintatico(
                    f"Esperado '}}' para fechar a struct '{nome}'", self.token_atual()
                )
            if not self.inicia_tipo():
                raise ErroSintatico("Esperado o tipo de um campo da struct", self.token_atual())

            tipo_base, token_tipo = self.ler_tipo_base()
            campos.extend(self.ler_declaradores(tipo_base, token_tipo, permitir_valor=False))

        self.avancar()  # '}'

        self.structs_pendentes.append(
            DefinicaoStruct(nome, campos, token_struct.linha, token_struct.coluna)
        )
        return f"struct {nome}"

    def ler_typedef(self):
        """typedef <tipo> Nome;  — registra Nome como apelido do tipo."""
        self.consumir("TYPEDEF", "Esperado 'typedef'")
        tipo_base, _ = self.ler_tipo_base()

        while True:
            estrelas = self.ler_ponteiros()
            token_nome = self.consumir("IDENTIFICADOR", "Esperado o nome do novo tipo")

            # "typedef struct { ... } Aluno;": a struct anônima ganha o nome Aluno.
            if tipo_base.startswith("struct __anonima"):
                anonima = tipo_base[len("struct "):]
                for definicao in self.structs_pendentes:
                    if definicao.nome == anonima:
                        definicao.nome = token_nome.lexema
                tipo_base = f"struct {token_nome.lexema}"

            self.apelidos[token_nome.lexema] = tipo_base + estrelas

            if not self.verificar("VIRGULA"):
                break
            self.avancar()

        self.consumir("PONTO_VIRGULA", "Esperado ';' ao final do typedef")

        return self.com_pendentes([])

    def ler_ponteiros(self):
        estrelas = ""

        while self.verificar("MUL"):
            self.avancar()
            estrelas += "*"
            while self.verificar("CONST"):
                self.avancar()

        return estrelas

    def ler_nome_tipo(self):
        tipo, _ = self.ler_tipo_base()
        return tipo + self.ler_ponteiros()

    def ler_funcao(self, tipo_retorno, token_nome, token_tipo):
        self.consumir("PAREN_ESQ", "Esperado '('")

        parametros = []
        variadica = False

        if self.verificar("VOID") and self.espiar().tipo == "PAREN_DIR":
            self.avancar()
        elif not self.verificar("PAREN_DIR"):
            while True:
                if self.verificar("RETICENCIAS"):
                    self.avancar()
                    variadica = True
                    break

                parametros.append(self.ler_parametro())

                if not self.verificar("VIRGULA"):
                    break
                self.avancar()

        self.consumir("PAREN_DIR", "Esperado ')' ao final dos parâmetros")

        corpo = None

        if self.verificar("PONTO_VIRGULA"):
            self.avancar()
        elif self.verificar("CHAVE_ESQ"):
            corpo = self.ler_bloco()
        else:
            raise ErroSintatico(
                "Esperado '{' ou ';' após a declaração da função",
                self.token_atual()
            )

        return Funcao(
            tipo_retorno, token_nome.lexema, parametros, corpo,
            token_tipo.linha, token_nome.coluna, variadica
        )

    def ler_parametro(self):
        if not self.inicia_tipo():
            raise ErroSintatico("Esperado o tipo do parâmetro", self.token_atual())

        token_tipo = self.token_atual()
        tipo = self.ler_nome_tipo()
        nome = None
        coluna = token_tipo.coluna

        if self.verificar("IDENTIFICADOR"):
            token_nome = self.avancar()
            nome = token_nome.lexema
            coluna = token_nome.coluna

        dimensoes = 0
        while self.verificar("COLCHETE_ESQ"):
            self.avancar()
            if not self.verificar("COLCHETE_DIR"):
                self.ler_expressao()
            self.consumir("COLCHETE_DIR", "Esperado ']'")
            dimensoes += 1

        return Parametro(tipo, nome, token_tipo.linha, coluna, dimensoes=dimensoes)

    # ------------------------------------------------------------------
    # Declarações
    # ------------------------------------------------------------------

    def ler_declaracao(self):
        """Lê 'int a = 1, *p, v[10];' e devolve uma lista de Declaracao."""
        tipo_base, token_tipo = self.ler_tipo_base()

        if self.verificar("PONTO_VIRGULA"):        # "struct Aluno { ... };"
            self.avancar()
            return self.com_pendentes([])

        return self.com_pendentes(self.ler_declaradores(tipo_base, token_tipo))

    def ler_declaradores(self, tipo_base, token_tipo, primeiro=None, permitir_valor=True):
        declaracoes = []

        while True:
            if primeiro is not None:
                estrelas, token_nome = primeiro
                primeiro = None
            else:
                estrelas = self.ler_ponteiros()
                token_nome = self.consumir("IDENTIFICADOR", "Esperando nome de variável")

            dimensoes = []

            while self.verificar("COLCHETE_ESQ"):
                self.avancar()
                tamanho = None
                if not self.verificar("COLCHETE_DIR"):
                    tamanho = self.ler_expressao()
                self.consumir("COLCHETE_DIR", "Esperado ']' após o tamanho do array")
                dimensoes.append(tamanho)

            inicializador = None

            if self.verificar("IGUAL"):
                if not permitir_valor:
                    raise ErroSintatico(
                        "Campos de struct não podem ter valor inicial",
                        self.token_atual()
                    )
                self.avancar()
                if self.verificar("CHAVE_ESQ"):
                    inicializador = self.ler_lista_inicializadora()
                else:
                    inicializador = self.ler_atribuicao()

            declaracoes.append(Declaracao(
                tipo_base + estrelas,
                token_nome.lexema,
                inicializador,
                token_tipo.linha,
                token_nome.coluna,
                dimensoes=dimensoes
            ))

            if not self.verificar("VIRGULA"):
                break
            self.avancar()

        self.consumir("PONTO_VIRGULA", "Esperado ';' ao final da declaração")

        return declaracoes

    def ler_lista_inicializadora(self):
        token = self.consumir("CHAVE_ESQ", "Esperado '{'")
        elementos = []

        while not self.verificar("CHAVE_DIR"):
            if self.verificar("CHAVE_ESQ"):
                elementos.append(self.ler_lista_inicializadora())
            else:
                elementos.append(self.ler_atribuicao())

            if not self.verificar("VIRGULA"):
                break
            self.avancar()

        self.consumir("CHAVE_DIR", "Esperado '}' ao final da lista de valores")

        return ListaInicializadora(elementos, token.linha, token.coluna)

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    def ler_comando(self):
        """Lê um comando. Devolve uma lista (declarações podem gerar várias)."""
        token = self.token_atual()
        tipo = token.tipo

        if tipo == "TYPEDEF":
            return self.ler_typedef()

        if self.inicia_tipo():
            return self.ler_declaracao()

        if tipo == "CHAVE_ESQ":
            return [self.ler_bloco()]

        if tipo == "IF":
            return [self.ler_se()]

        if tipo == "WHILE":
            return [self.ler_enquanto()]

        if tipo == "DO":
            return [self.ler_faca_enquanto()]

        if tipo == "FOR":
            return [self.ler_para()]

        if tipo == "SWITCH":
            return [self.ler_escolha()]

        if tipo == "RETURN":
            return [self.ler_retorno()]

        if tipo in {"BREAK", "CONTINUE"}:
            self.avancar()
            palavra = token.lexema
            self.consumir("PONTO_VIRGULA", f"Esperado ';' após '{palavra}'")
            classe = Pare if tipo == "BREAK" else Continue
            return [classe(token.linha, token.coluna)]

        if tipo == "PONTO_VIRGULA":
            self.avancar()
            return [ComandoVazio(token.linha, token.coluna)]

        if tipo == "ELSE":
            raise ErroSintatico("'else' sem um 'if' correspondente", token)

        if tipo in {"CASE", "DEFAULT"}:
            raise ErroSintatico(f"'{token.lexema}' fora de um switch", token)

        if tipo == "CHAVE_DIR":
            raise ErroSintatico("'}' sem um '{' correspondente", token)

        expressao = self.ler_expressao()

        self.consumir("PONTO_VIRGULA", "Esperado ';' após a expressão")

        return [expressao]

    def ler_comando_unico(self):
        """Corpo de if/while/for: um único comando, que não pode ser declaração."""
        if self.inicia_tipo() or self.verificar("TYPEDEF"):
            raise ErroSintatico(
                "Declaração não permitida aqui; use um bloco { }",
                self.token_atual()
            )

        return self.ler_comando()[0]

    def ler_bloco(self):
        token = self.consumir("CHAVE_ESQ", "Esperado '{'")
        comandos = []

        while not self.verificar("CHAVE_DIR"):
            if self.verificar("FIM"):
                raise ErroSintatico(
                    f"Esperado '}}' para fechar o bloco aberto na linha {token.linha}",
                    self.token_atual()
                )
            comandos.extend(self.ler_comando())

        self.avancar()

        return Bloco(comandos, token.linha, token.coluna)

    def ler_condicao_entre_parenteses(self, palavra):
        self.consumir("PAREN_ESQ", f"Esperado '(' após '{palavra}'")
        condicao = self.ler_expressao()
        self.consumir("PAREN_DIR", f"Esperado ')' após a condição do '{palavra}'")
        return condicao

    def ler_se(self):
        token = self.avancar()
        condicao = self.ler_condicao_entre_parenteses("if")
        entao = self.ler_comando_unico()
        senao = None

        if self.verificar("ELSE"):
            self.avancar()
            senao = self.ler_comando_unico()

        return Se(condicao, entao, senao, token.linha, token.coluna)

    def ler_enquanto(self):
        token = self.avancar()
        condicao = self.ler_condicao_entre_parenteses("while")
        corpo = self.ler_comando_unico()
        return Enquanto(condicao, corpo, token.linha, token.coluna)

    def ler_faca_enquanto(self):
        token = self.avancar()
        corpo = self.ler_comando_unico()
        self.consumir("WHILE", "Esperado 'while' após o corpo do 'do'")
        condicao = self.ler_condicao_entre_parenteses("while")
        self.consumir("PONTO_VIRGULA", "Esperado ';' após o 'do-while'")
        return FacaEnquanto(corpo, condicao, token.linha, token.coluna)

    def ler_para(self):
        token = self.avancar()
        self.consumir("PAREN_ESQ", "Esperado '(' após 'for'")

        if self.verificar("PONTO_VIRGULA"):
            self.avancar()
            inicio = []
        elif self.inicia_tipo():
            inicio = self.ler_declaracao()
        else:
            inicio = [self.ler_expressao()]
            self.consumir("PONTO_VIRGULA", "Esperado ';' após a inicialização do 'for'")

        condicao = None
        if not self.verificar("PONTO_VIRGULA"):
            condicao = self.ler_expressao()
        self.consumir("PONTO_VIRGULA", "Esperado ';' após a condição do 'for'")

        incremento = None
        if not self.verificar("PAREN_DIR"):
            incremento = self.ler_expressao()
        self.consumir("PAREN_DIR", "Esperado ')' ao final do 'for'")

        corpo = self.ler_comando_unico()

        return Para(inicio, condicao, incremento, corpo, token.linha, token.coluna)

    def ler_escolha(self):
        token = self.avancar()
        expressao = self.ler_condicao_entre_parenteses("switch")
        self.consumir("CHAVE_ESQ", "Esperado '{' após o 'switch'")

        casos = []

        while not self.verificar("CHAVE_DIR"):
            atual = self.token_atual()

            if atual.tipo == "CASE":
                self.avancar()
                valor = self.ler_condicional()
            elif atual.tipo == "DEFAULT":
                self.avancar()
                valor = None
            else:
                raise ErroSintatico(
                    "Esperado 'case' ou 'default' dentro do switch",
                    atual
                )

            self.consumir("DOIS_PONTOS", f"Esperado ':' após '{atual.lexema}'")

            comandos = []
            while not self.verificar("CASE", "DEFAULT", "CHAVE_DIR", "FIM"):
                comandos.extend(self.ler_comando())

            casos.append(Caso(valor, comandos, atual.linha, atual.coluna))

        self.consumir("CHAVE_DIR", "Esperado '}' ao final do switch")

        return Escolha(expressao, casos, token.linha, token.coluna)

    def ler_retorno(self):
        token_return = self.consumir("RETURN", "Esperado 'return'")

        valor = None
        if not self.verificar("PONTO_VIRGULA"):
            valor = self.ler_expressao()

        self.consumir(
            "PONTO_VIRGULA",
            "Esperado ';' após o retorno"
        )

        return Retorno(valor, token_return.linha, token_return.coluna)

    # ------------------------------------------------------------------
    # Expressões
    # ------------------------------------------------------------------

    def ler_expressao(self):
        """Expressão completa, incluindo o operador vírgula: 'i++, j--'."""
        primeira = self.ler_atribuicao()

        if not self.verificar("VIRGULA"):
            return primeira

        expressoes = [primeira]
        while self.verificar("VIRGULA"):
            self.avancar()
            expressoes.append(self.ler_atribuicao())

        return Sequencia(expressoes, primeira.linha, primeira.coluna)

    def ler_atribuicao(self):
        alvo = self.ler_condicional()

        if self.verificar(*OPERADORES_ATRIBUICAO):
            operador = self.avancar()
            valor = self.ler_atribuicao()      # associativa à direita: a = b = 0
            return Atribuicao(alvo, operador.lexema, valor, alvo.linha, alvo.coluna)

        return alvo

    def ler_condicional(self):
        condicao = self.ler_binaria(0)

        if self.verificar("INTERROGACAO"):
            token = self.avancar()
            se_verdadeiro = self.ler_expressao()
            self.consumir("DOIS_PONTOS", "Esperado ':' no operador '?:'")
            se_falso = self.ler_condicional()
            return Condicional(condicao, se_verdadeiro, se_falso, token.linha, token.coluna)

        return condicao

    # Níveis de precedência dos operadores binários, do mais fraco ao mais forte.
    NIVEIS_BINARIOS = [
        {"OU_LOGICO"},
        {"E_LOGICO"},
        {"OU"},
        {"XOR"},
        {"E"},
        {"IGUAL_IGUAL", "DIFERENTE"},
        {"MENOR", "MAIOR", "MENOR_IGUAL", "MAIOR_IGUAL"},
        {"DESLOC_ESQ", "DESLOC_DIR"},
        {"MAIS", "MENOS"},
        {"MUL", "DIV", "MOD"},
    ]

    def ler_binaria(self, nivel):
        """Lê operadores binários associativos à esquerda, por nível de precedência."""
        if nivel == len(self.NIVEIS_BINARIOS):
            return self.ler_unario()

        esquerda = self.ler_binaria(nivel + 1)

        while self.verificar(*self.NIVEIS_BINARIOS[nivel]):
            operador = self.avancar()
            direita = self.ler_binaria(nivel + 1)

            esquerda = OperacaoBinaria(
                esquerda,
                operador.lexema,
                direita,
                operador.linha,
                operador.coluna
            )

        return esquerda

    def ler_termo(self):
        """Expressão multiplicativa (atalho mantido por compatibilidade)."""
        return self.ler_binaria(len(self.NIVEIS_BINARIOS) - 1)

    def ler_unario(self):
        token = self.token_atual()

        if token.tipo in {"MAIS", "MENOS", "NAO", "TIL", "E", "MUL"}:
            self.avancar()
            operando = self.ler_unario()
            return OperacaoUnaria(token.lexema, operando, token.linha, token.coluna)

        if token.tipo in {"INCREMENTO", "DECREMENTO"}:
            self.avancar()
            operando = self.ler_unario()
            return IncrementoDecremento(
                token.lexema, operando, True, token.linha, token.coluna
            )

        if token.tipo == "SIZEOF":
            self.avancar()
            if self.verificar("PAREN_ESQ") and self.inicia_tipo(self.espiar()):
                self.avancar()
                tipo = self.ler_nome_tipo()
                self.consumir("PAREN_DIR", "Esperado ')' após o tipo")
                return Tamanho(tipo, None, token.linha, token.coluna)
            return Tamanho(None, self.ler_unario(), token.linha, token.coluna)

        # Conversão explícita: (int) x
        if token.tipo == "PAREN_ESQ" and self.inicia_tipo(self.espiar()):
            self.avancar()
            tipo = self.ler_nome_tipo()
            self.consumir("PAREN_DIR", "Esperado ')' após o tipo da conversão")
            expressao = self.ler_unario()
            return Conversao(tipo, expressao, token.linha, token.coluna)

        return self.ler_posfixo()

    def ler_posfixo(self):
        expressao = self.ler_primario()

        while True:
            token = self.token_atual()

            if token.tipo == "PAREN_ESQ":
                if not isinstance(expressao, Identificador):
                    raise ErroSintatico("Somente funções podem ser chamadas", token)

                self.avancar()
                argumentos = []

                if not self.verificar("PAREN_DIR"):
                    while True:
                        argumentos.append(self.ler_atribuicao())
                        if not self.verificar("VIRGULA"):
                            break
                        self.avancar()

                self.consumir("PAREN_DIR", "Esperado ')' ao final dos argumentos")

                expressao = Chamada(
                    expressao.nome, argumentos, expressao.linha, expressao.coluna
                )

            elif token.tipo == "COLCHETE_ESQ":
                self.avancar()
                indice = self.ler_expressao()
                self.consumir("COLCHETE_DIR", "Esperado ']' após o índice")
                expressao = Indexacao(expressao, indice, expressao.linha, expressao.coluna)

            elif token.tipo in {"PONTO", "SETA"}:
                self.avancar()
                campo = self.consumir(
                    "IDENTIFICADOR", f"Esperado o nome do campo após '{token.lexema}'"
                )
                expressao = Acesso(
                    expressao, campo.lexema, token.tipo == "SETA",
                    expressao.linha, expressao.coluna
                )

            elif token.tipo in {"INCREMENTO", "DECREMENTO"}:
                self.avancar()
                expressao = IncrementoDecremento(
                    token.lexema, expressao, False, expressao.linha, expressao.coluna
                )

            else:
                return expressao

    def ler_primario(self):
        token = self.token_atual()

        literais = {
            "NUMERO": Numero,
            "NUMERO_REAL": NumeroReal,
            "CARACTERE": Caractere,
            "TEXTO": Texto,
            "IDENTIFICADOR": Identificador,
        }

        if token.tipo in literais:
            self.avancar()

            # "abc" "def" em sequência formam um único texto, como em C.
            if token.tipo == "TEXTO":
                valor = token.lexema
                while self.verificar("TEXTO"):
                    valor += self.avancar().lexema
                return Texto(valor, token.linha, token.coluna)

            return literais[token.tipo](
                token.lexema,
                token.linha,
                token.coluna
            )

        if token.tipo == "PAREN_ESQ":
            self.avancar()

            expressao = self.ler_expressao()

            self.consumir(
                "PAREN_DIR",
                "Esperado ')' após a expressão"
            )

            return expressao

        raise ErroSintatico(
            "Esperado um número, identificador ou '('",
            token
        )
