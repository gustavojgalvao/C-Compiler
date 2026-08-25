"""
Testes unitários para o Analisador Semântico.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.utils.errors import SemanticError

class TestSemantic(unittest.TestCase):
    def test_undeclared_variable_fails(self):
        code = "int main() { return a + 1; }"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()

        with self.assertRaises(SemanticError):
            analyzer.analyze(ast)

    def test_valid_variable_declaration(self):
        code = "int main() { int x = 10; return x; }"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()

        # Não deve lançar exceção
        analyzer.analyze(ast)

if __name__ == "__main__":
    unittest.main()
