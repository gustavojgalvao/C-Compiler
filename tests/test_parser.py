"""Testes unitários para o Analisador Sintático (Parser)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lexer import Lexer
from src.parser import Parser, ErroSintatico
from src.arvore_sintatica import (
    Programa,
    Declaracao,
    Atribuicao,
    Retorno,
    OperacaoBinaria,
    OperacaoUnaria,
    Numero,
    Identificador,
)


def analisar(codigo):
    return Parser(Lexer(codigo).tokenizar()).analisar()


class TestParser(unittest.TestCase):
    def test_programa_com_tres_comandos(self):
        arvore = analisar("int x = 1; x = x + 1; return x;")
        self.assertIsInstance(arvore, Programa)
        self.assertEqual(
            [type(c) for c in arvore.comandos],
            [Declaracao, Atribuicao, Retorno],
        )

    def test_declaracao_sem_inicializador(self):
        decl = analisar("float y;").comandos[0]
        self.assertEqual((decl.tipo, decl.nome, decl.inicializador), ("float", "y", None))

    def test_precedencia(self):
        expr = analisar("return 5 + 3 * 2;").comandos[0].valor
        self.assertIsInstance(expr, OperacaoBinaria)
        self.assertEqual(expr.operador, "+")
        self.assertIsInstance(expr.esquerda, Numero)
        self.assertEqual(expr.direita.operador, "*")

    def test_associatividade_a_esquerda(self):
        expr = analisar("return 10 - 4 - 3;").comandos[0].valor
        self.assertEqual(expr.operador, "-")
        self.assertEqual(expr.esquerda.operador, "-")
        self.assertEqual(expr.direita.valor, "3")

    def test_parenteses(self):
        expr = analisar("return (1 + 2) * 3;").comandos[0].valor
        self.assertEqual(expr.operador, "*")
        self.assertEqual(expr.esquerda.operador, "+")

    def test_menos_unario(self):
        expr = analisar("int a = -b * 2;").comandos[0].inicializador
        self.assertEqual(expr.operador, "*")
        self.assertIsInstance(expr.esquerda, OperacaoUnaria)
        self.assertIsInstance(expr.esquerda.operando, Identificador)

    def test_formatar(self):
        texto = analisar("int a = 1 + 2;").formatar()
        self.assertEqual(
            texto,
            "Programa\n"
            "  Declaracao (tipo=int, nome=a)\n"
            "    OperacaoBinaria (+)\n"
            "      Numero (1)\n"
            "      Numero (2)",
        )

    def test_falta_ponto_e_virgula(self):
        with self.assertRaises(ErroSintatico) as ctx:
            analisar("int a = 1\nint b;")
        self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (2, 1))

    def test_comando_invalido(self):
        with self.assertRaises(ErroSintatico):
            analisar("else return 1;")

    def test_parentese_nao_fechado(self):
        with self.assertRaises(ErroSintatico):
            analisar("return (1 + 2;")


if __name__ == "__main__":
    unittest.main()
