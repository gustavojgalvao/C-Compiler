"""Testes unitários para o Analisador Léxico."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lexer import Lexer
from src.erros import ErroLexico


def tipos(codigo):
    return [t.tipo for t in Lexer(codigo).tokenizar()]


class TestLexer(unittest.TestCase):
    def test_declaracao_simples(self):
        self.assertEqual(
            tipos("int x = 42;"),
            ["INT", "IDENTIFICADOR", "IGUAL", "NUMERO", "PONTO_VIRGULA", "FIM"],
        )

    def test_literais(self):
        tokens = Lexer("3.14 'A' \"oi mundo\" 7").tokenizar()
        self.assertEqual(
            [(t.tipo, t.lexema) for t in tokens[:-1]],
            [
                ("NUMERO_REAL", "3.14"),
                ("CARACTERE", "A"),
                ("TEXTO", "oi mundo"),
                ("NUMERO", "7"),
            ],
        )

    def test_palavras_reservadas(self):
        self.assertEqual(
            tipos("return float char while"),
            ["RETURN", "FLOAT", "CHAR", "WHILE", "FIM"],
        )

    def test_linha_e_coluna(self):
        tokens = Lexer("int a;\n  a = 1;").tokenizar()
        a2 = tokens[3]
        self.assertEqual((a2.lexema, a2.linha, a2.coluna), ("a", 2, 3))

    def test_comentarios_sao_ignorados(self):
        codigo = """
        // comentario de linha
        int x = 10 + 20 * 3; /* bloco
        com varias linhas */ x = x / 2;
        """
        t = tipos(codigo)
        self.assertNotIn("DIV", t[:9])
        self.assertEqual(t.count("DIV"), 1)
        self.assertIn("MAIS", t)
        self.assertIn("MUL", t)

    def test_comentario_de_bloco_nao_fechado(self):
        with self.assertRaises(ErroLexico) as ctx:
            Lexer("int x; /* sem fim").tokenizar()
        self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (1, 8))

    def test_caractere_invalido_informa_posicao(self):
        with self.assertRaises(ErroLexico) as ctx:
            Lexer("int a = 1;\nint b = $;").tokenizar()
        self.assertEqual((ctx.exception.linha, ctx.exception.coluna), (2, 9))

    def test_texto_nao_finalizado(self):
        with self.assertRaises(ErroLexico):
            Lexer('int a = "abc').tokenizar()

    def test_numero_malformado(self):
        with self.assertRaises(ErroLexico):
            Lexer("int a = 12abc;").tokenizar()


if __name__ == "__main__":
    unittest.main()
