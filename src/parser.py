from src.arvore_sintatica import (
    Programa,
    Declaracao,
    Numero,
    Identificador,
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
            declaracao = self.ler_declaracao()
            programa.adicionar(declaracao)

        return programa

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
            inicializador = self.ler_valor()
        
        self.consumir(
            "PONTO_VIRGULA", 
            "Esperado ';' ao final da declaração")

        return Declaracao(
            token_tipo.lexema,
            token_nome.lexema,
            inicializador,
            token_tipo.linha
        )

    def ler_valor(self):
        token = self.token_atual()

        if token.tipo == "NUMERO":
            self.avancar()

            return Numero(
                token.lexema,
                token.linha
            )

        if token.tipo == "IDENTIFICADOR":
            self.avancar()

            return Identificador(
                token.lexema,
                token.linha
            )

        raise ErroSintatico(
            "Esperado um número ou identificador",token
        )
