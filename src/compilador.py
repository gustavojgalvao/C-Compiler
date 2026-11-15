"""Pipeline completo do front-end: léxico -> símbolos -> sintático -> semântico."""

from src.lexer import Lexer
from src.tabela_simbolos import TabelaSimbolos
from src.parser import Parser
from src.analisador_semantico import AnalisadorSemantico


class ResultadoCompilacao:
    def __init__(self, tokens, tabela, arvore, semantico):
        self.tokens = tokens
        self.tabela = tabela
        self.arvore = arvore
        self.semantico = semantico

    @property
    def sucesso(self):
        return self.semantico.sucesso


def compilar(codigo):
    """
    Executa todas as etapas sobre o código-fonte.

    Erros léxicos e sintáticos interrompem a compilação (ErroLexico /
    ErroSintatico). Problemas semânticos são acumulados em
    resultado.semantico.diagnosticos.
    """
    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()

    tabela = TabelaSimbolos()
    tabela.construir(tokens)

    arvore = Parser(tokens).analisar()

    semantico = AnalisadorSemantico(lexer.inclusoes).analisar(arvore)

    return ResultadoCompilacao(tokens, tabela, arvore, semantico)
