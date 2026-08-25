"""
Testes unitários para o Analisador Sintático (Parser).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.parser.ast_nodes import ProgramNode, ReturnStmtNode, BinaryOpNode

class TestParser(unittest.TestCase):
    def test_parse_simple_program(self):
        code = "int main() { return 5 + 3 * 2; }"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(len(ast.functions), 1)

        func = ast.functions[0]
        self.assertEqual(func.name, "main")
        self.assertEqual(len(func.body.statements), 1)

        ret_stmt = func.body.statements[0]
        self.assertIsInstance(ret_stmt, ReturnStmtNode)
        self.assertIsInstance(ret_stmt.expr, BinaryOpNode)
        self.assertEqual(ret_stmt.expr.op, "+")

if __name__ == "__main__":
    unittest.main()
