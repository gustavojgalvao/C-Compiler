"""
Testes unitários para o Analisador Léxico.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.lexer.lexer import Lexer
from src.lexer.token import TokenType

class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        code = "int main() { return 42; }"
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        expected = [
            TokenType.INT,
            TokenType.IDENTIFIER,
            TokenType.LPAREN,
            TokenType.RPAREN,
            TokenType.LBRACE,
            TokenType.RETURN,
            TokenType.INT_LITERAL,
            TokenType.SEMICOLON,
            TokenType.RBRACE,
            TokenType.EOF
        ]
        self.assertEqual([t.type for t in tokens], expected)
        self.assertEqual(tokens[6].value, "42")

    def test_operators_and_comments(self):
        code = """
        // comentario
        int x = 10 + 20 * 3;
        /* bloco */
        """
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens]
        self.assertIn(TokenType.PLUS, types)
        self.assertIn(TokenType.STAR, types)
        self.assertIn(TokenType.ASSIGN, types)

if __name__ == "__main__":
    unittest.main()
