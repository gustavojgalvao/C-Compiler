from src.arvore_sintatica import (
    Programa,
    Declaracao,
    Numero,
    NumeroReal,
    Caractere,
    Texto,
    Identificador,
    OperacaoBinaria,
    Atribuicao,
    Retorno
)

class ErroSintatico(Exception):
    def __init__(self, mensagem, token):
        self.linha = token.linha
        self.coluna = token.coluna

        texto = (
            f"{mensagem} "
            f"na linha {self.linha}, "
            f"coluna {self.coluna}"
        )

        super().__init__(texto)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0

    def token_atual(self):
        return self.tokens[self.posicao]

    def avancar(self):
        token = self.token_atual()

        if token.tipo != "FIM":
            self.posicao += 1
        return token

    def verificar (self, tipo):
        return self.token_atual().tipo == tipo

    def consumir(self, tipo, mensagem):
        token = self.token_atual()

        if token.tipo != tipo:
            raise ErroSintatico(mensagem, token)

        self.avancar()
        return token

    def analisar(self):
        programa = Programa()

        while not self.verificar("FIM"):
            comando = self.ler_comando()
            programa.adicionar(comando)

        return programa

    def ler_comando(self):
        tipo = self.token_atual().tipo

        if tipo in {"INT", "FLOAT", "CHAR"}:
            return self.ler_declaracao()

        if tipo == "IDENTIFICADOR":
            return self.ler_atribuicao()

        if tipo == "RETURN":
            return self.ler_retorno()

        raise ErroSintatico(
            "Comando inválido",
            self.token_atual()
        )

    def ler_declaracao(self):
        token_tipo = self.token_atual()

        tipos_permitidos = {
            "INT",
            "CHAR",
            "FLOAT"
        }

        if token_tipo.tipo not in tipos_permitidos:
            raise ErroSintatico(
                "Esperando uma declaração de variável",
                token_tipo
            )
        
        self.avancar()

        token_nome = self.consumir(
            "IDENTIFICADOR",
            "Esperando nome de variável"
        )

        inicializador = None

        if self.verificar("IGUAL"):
            self.avancar()
            inicializador = self.ler_expressao()
        
        self.consumir(
            "PONTO_VIRGULA", 
            "Esperado ';' ao final da declaração")

        return Declaracao(
            token_tipo.lexema,
            token_nome.lexema,
            inicializador,
            token_tipo.linha
        )

    def ler_atribuicao(self):
        token_nome = self.consumir(
            "IDENTIFICADOR",
            "Esperado o nome da variável"
        )

        self.consumir(
            "IGUAL",
            "Esperado '=' após o identificador"
        )

        valor = self.ler_expressao()

        self.consumir(
            "PONTO_VIRGULA",
            "Esperado ';' após a atribuição"
        )

        return Atribuicao(
            token_nome.lexema,
            valor,
            token_nome.linha
        )

    def ler_retorno(self):
        token_return = self.consumir(
            "RETURN",
            "Esperado 'return'"
        )

        valor = self.ler_expressao()

        self.consumir(
            "PONTO_VIRGULA",
            "Esperado ';' após o retorno"
        )

        return Retorno(
            valor,
            token_return.linha
        )

    def ler_expressao(self):
        esquerda = self.ler_termo()

        while (
            self.verificar("MAIS")
            or self.verificar("MENOS")
        ):
            operador = self.avancar()
            direita = self.ler_termo()

            esquerda = OperacaoBinaria(
                esquerda,
                operador.lexema,
                direita,
                operador.linha
            )

        return esquerda

    def ler_termo(self):
        esquerda = self.ler_fator()

        while (
            self.verificar("MUL")
            or self.verificar("DIV")
            or self.verificar("MOD")
        ):
            operador = self.avancar()
            direita = self.ler_fator()

            esquerda = OperacaoBinaria(
                esquerda,
                operador.lexema,
                direita,
                operador.linha
            )

        return esquerda

    def ler_fator(self):
        token = self.token_atual()

        if token.tipo == "NUMERO":
            self.avancar()

            return Numero(
                token.lexema,
                token.linha
            )

        if token.tipo == "NUMERO_REAL":
            self.avancar()

            return NumeroReal(
                token.lexema,
                token.linha
            )

        if token.tipo == "CARACTERE":
            self.avancar()

            return Caractere(
                token.lexema,
                token.linha
            )

        if token.tipo == "TEXTO":
            self.avancar()

            return Texto(
                token.lexema,
                token.linha
            )

        if token.tipo == "IDENTIFICADOR":
            self.avancar()

            return Identificador(
                token.lexema,
                token.linha
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
