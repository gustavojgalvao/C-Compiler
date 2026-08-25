"""
Analisador Sintático (Parser) recursivo descendente para C.
"""
from typing import List, Optional
from src.lexer.token import Token, TokenType
from src.parser.ast_nodes import (
    ProgramNode, FunctionDefNode, ParamNode, BlockStmtNode,
    StmtNode, ReturnStmtNode, VarDeclStmtNode, IfStmtNode,
    WhileStmtNode, ForStmtNode, ExprStmtNode, ExprNode,
    BinaryOpNode, UnaryOpNode, AssignNode, FunctionCallNode,
    IdentifierNode, IntLiteralNode, AddressOfNode, DerefNode
)
from src.utils.errors import ParserError

class Parser:
    """Parser com suporte a declarações de funções, blocos, ponteiros e expressões."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _match(self, *types: TokenType) -> bool:
        if self._current().type in types:
            self._advance()
            return True
        return False

    def _consume(self, token_type: TokenType, err_msg: str) -> Token:
        tok = self._current()
        if tok.type == token_type:
            self._advance()
            return tok
        raise ParserError(f"{err_msg}. Encontrado: {tok.type.name} ({tok.value!r})", tok.line, tok.column)

    def _advance(self) -> Token:
        tok = self._current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def parse(self) -> ProgramNode:
        functions: List[FunctionDefNode] = []
        while self._current().type != TokenType.EOF:
            functions.append(self._parse_function_def())
        return ProgramNode(functions=functions)

    def _parse_function_def(self) -> FunctionDefNode:
        return_type = self._consume(TokenType.INT, "Esperado tipo de retorno 'int'").value
        name = self._consume(TokenType.IDENTIFIER, "Esperado nome da função").value
        self._consume(TokenType.LPAREN, "Esperado '(' após nome da função")

        params: List[ParamNode] = []
        if self._current().type != TokenType.RPAREN and self._current().type != TokenType.VOID:
            while True:
                p_type = self._consume(TokenType.INT, "Esperado tipo do parâmetro").value
                p_name = self._consume(TokenType.IDENTIFIER, "Esperado nome do parâmetro").value
                params.append(ParamNode(type_name=p_type, name=p_name))
                if not self._match(TokenType.COMMA):
                    break
        elif self._current().type == TokenType.VOID:
            self._advance()

        self._consume(TokenType.RPAREN, "Esperado ')' após lista de parâmetros")
        body = self._parse_block()
        return FunctionDefNode(return_type=return_type, name=name, params=params, body=body)

    def _parse_block(self) -> BlockStmtNode:
        self._consume(TokenType.LBRACE, "Esperado '{' no início do bloco")
        stmts: List[StmtNode] = []
        while self._current().type != TokenType.RBRACE and self._current().type != TokenType.EOF:
            stmts.append(self._parse_statement())
        self._consume(TokenType.RBRACE, "Esperado '}' no final do bloco")
        return BlockStmtNode(statements=stmts)

    def _parse_statement(self) -> StmtNode:
        tok = self._current()

        if tok.type == TokenType.RETURN:
            self._advance()
            expr = None
            if self._current().type != TokenType.SEMICOLON:
                expr = self._parse_expression()
            self._consume(TokenType.SEMICOLON, "Esperado ';' após retorno")
            return ReturnStmtNode(expr=expr)

        if tok.type == TokenType.INT:
            self._advance()
            is_ptr = self._match(TokenType.STAR)
            type_name = "int*" if is_ptr else "int"
            name = self._consume(TokenType.IDENTIFIER, "Esperado nome da variável").value
            init_expr = None
            if self._match(TokenType.ASSIGN):
                init_expr = self._parse_expression()
            self._consume(TokenType.SEMICOLON, "Esperado ';' após declaração de variável")
            return VarDeclStmtNode(type_name=type_name, name=name, init_expr=init_expr)

        if tok.type == TokenType.IF:
            self._advance()
            self._consume(TokenType.LPAREN, "Esperado '(' após if")
            cond = self._parse_expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após condição do if")
            then_branch = self._parse_statement()
            else_branch = None
            if self._match(TokenType.ELSE):
                else_branch = self._parse_statement()
            return IfStmtNode(condition=cond, then_branch=then_branch, else_branch=else_branch)

        if tok.type == TokenType.WHILE:
            self._advance()
            self._consume(TokenType.LPAREN, "Esperado '(' após while")
            cond = self._parse_expression()
            self._consume(TokenType.RPAREN, "Esperado ')' após condição do while")
            body = self._parse_statement()
            return WhileStmtNode(condition=cond, body=body)

        if tok.type == TokenType.LBRACE:
            return self._parse_block()

        expr = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Esperado ';' após instrução")
        return ExprStmtNode(expr=expr)

    def _parse_expression(self) -> ExprNode:
        return self._parse_assignment()

    def _parse_assignment(self) -> ExprNode:
        expr = self._parse_logical_or()
        if self._match(TokenType.ASSIGN):
            value = self._parse_assignment()
            return AssignNode(target=expr, value=value)
        return expr

    def _parse_logical_or(self) -> ExprNode:
        expr = self._parse_logical_and()
        while self._match(TokenType.OR_OR):
            right = self._parse_logical_and()
            expr = BinaryOpNode(op="||", left=expr, right=right)
        return expr

    def _parse_logical_and(self) -> ExprNode:
        expr = self._parse_equality()
        while self._match(TokenType.AND_AND):
            right = self._parse_equality()
            expr = BinaryOpNode(op="&&", left=expr, right=right)
        return expr

    def _parse_equality(self) -> ExprNode:
        expr = self._parse_relational()
        while self._current().type in (TokenType.EQ_EQ, TokenType.BANG_EQ):
            op = self._advance().value
            right = self._parse_relational()
            expr = BinaryOpNode(op=op, left=expr, right=right)
        return expr

    def _parse_relational(self) -> ExprNode:
        expr = self._parse_additive()
        while self._current().type in (TokenType.LESS, TokenType.LESS_EQ, TokenType.GREATER, TokenType.GREATER_EQ):
            op = self._advance().value
            right = self._parse_additive()
            expr = BinaryOpNode(op=op, left=expr, right=right)
        return expr

    def _parse_additive(self) -> ExprNode:
        expr = self._parse_multiplicative()
        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            expr = BinaryOpNode(op=op, left=expr, right=right)
        return expr

    def _parse_multiplicative(self) -> ExprNode:
        expr = self._parse_unary()
        while self._current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance().value
            right = self._parse_unary()
            expr = BinaryOpNode(op=op, left=expr, right=right)
        return expr

    def _parse_unary(self) -> ExprNode:
        if self._current().type in (TokenType.MINUS, TokenType.TILDE, TokenType.BANG):
            op = self._advance().value
            return UnaryOpNode(op=op, operand=self._parse_unary())
        if self._match(TokenType.AMPERSAND):
            return AddressOfNode(operand=self._parse_unary())
        if self._match(TokenType.STAR):
            return DerefNode(operand=self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> ExprNode:
        tok = self._current()

        if self._match(TokenType.INT_LITERAL):
            return IntLiteralNode(value=int(tok.value, 0))

        if self._match(TokenType.IDENTIFIER):
            if self._match(TokenType.LPAREN):
                args: List[ExprNode] = []
                if self._current().type != TokenType.RPAREN:
                    while True:
                        args.append(self._parse_expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RPAREN, "Esperado ')' ao fechar argumentos de função")
                return FunctionCallNode(callee=tok.value, arguments=args)
            return IdentifierNode(name=tok.value)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Esperado ')' para fechar parênteses")
            return expr

        raise ParserError(f"Expressão inesperada iniciada por '{tok.value}' ({tok.type.name})", tok.line, tok.column)
