"""
Analisador Semântico: verificação de tipos, resolução de escopo e consistência da AST.
"""
from typing import Optional
from src.parser.ast_nodes import (
    ProgramNode, FunctionDefNode, BlockStmtNode, StmtNode,
    ReturnStmtNode, VarDeclStmtNode, IfStmtNode, WhileStmtNode,
    ExprStmtNode, ExprNode, BinaryOpNode, UnaryOpNode,
    AssignNode, FunctionCallNode, IdentifierNode, IntLiteralNode,
    AddressOfNode, DerefNode
)
from src.semantic.types import IntType, VoidType, PointerType, CType
from src.semantic.symbol_table import SymbolTable, Symbol
from src.utils.errors import SemanticError

class SemanticAnalyzer:
    """Valida tipos e consistência de escopos percorrendo os nós da AST."""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function_return_type: Optional[CType] = None

    def analyze(self, program: ProgramNode) -> None:
        for func in program.functions:
            self._register_function(func)

        for func in program.functions:
            self._analyze_function(func)

    def _register_function(self, func: FunctionDefNode) -> None:
        ret_type = IntType() if func.return_type == "int" else VoidType()
        param_types = [IntType() for _ in func.params]
        sym = Symbol(name=func.name, type=ret_type, is_function=True, param_types=param_types)
        if not self.symbol_table.define(sym):
            raise SemanticError(f"Redefinição da função '{func.name}'")

    def _analyze_function(self, func: FunctionDefNode) -> None:
        self.current_function_return_type = IntType() if func.return_type == "int" else VoidType()
        self.symbol_table.enter_scope()

        for param in func.params:
            sym = Symbol(name=param.name, type=IntType())
            if not self.symbol_table.define(sym):
                raise SemanticError(f"Nome de parâmetro duplicado '{param.name}' na função '{func.name}'")

        for stmt in func.body.statements:
            self._analyze_statement(stmt)

        self.symbol_table.exit_scope()

    def _analyze_statement(self, stmt: StmtNode) -> None:
        if isinstance(stmt, ReturnStmtNode):
            if stmt.expr:
                self._analyze_expression(stmt.expr)
                if isinstance(self.current_function_return_type, VoidType):
                    raise SemanticError("Função void não pode retornar valor")
            return

        if isinstance(stmt, VarDeclStmtNode):
            var_type = PointerType(IntType()) if stmt.type_name.endswith("*") else IntType()
            sym = Symbol(name=stmt.name, type=var_type)
            if not self.symbol_table.define(sym):
                raise SemanticError(f"Redeclaração da variável '{stmt.name}' no mesmo escopo")
            if stmt.init_expr:
                self._analyze_expression(stmt.init_expr)
            return

        if isinstance(stmt, IfStmtNode):
            self._analyze_expression(stmt.condition)
            self._analyze_statement(stmt.then_branch)
            if stmt.else_branch:
                self._analyze_statement(stmt.else_branch)
            return

        if isinstance(stmt, WhileStmtNode):
            self._analyze_expression(stmt.condition)
            self._analyze_statement(stmt.body)
            return

        if isinstance(stmt, BlockStmtNode):
            self.symbol_table.enter_scope()
            for s in stmt.statements:
                self._analyze_statement(s)
            self.symbol_table.exit_scope()
            return

        if isinstance(stmt, ExprStmtNode):
            self._analyze_expression(stmt.expr)
            return

    def _analyze_expression(self, expr: ExprNode) -> CType:
        if isinstance(expr, IntLiteralNode):
            return IntType()

        if isinstance(expr, IdentifierNode):
            sym = self.symbol_table.lookup(expr.name)
            if not sym or sym.is_function:
                raise SemanticError(f"Variável não declarada: '{expr.name}'")
            return sym.type

        if isinstance(expr, AddressOfNode):
            inner_type = self._analyze_expression(expr.operand)
            return PointerType(inner_type)

        if isinstance(expr, DerefNode):
            ptr_type = self._analyze_expression(expr.operand)
            if isinstance(ptr_type, PointerType):
                return ptr_type.base_type
            return IntType()

        if isinstance(expr, BinaryOpNode):
            self._analyze_expression(expr.left)
            self._analyze_expression(expr.right)
            return IntType()

        if isinstance(expr, UnaryOpNode):
            return self._analyze_expression(expr.operand)

        if isinstance(expr, AssignNode):
            if not isinstance(expr.target, (IdentifierNode, DerefNode)):
                raise SemanticError("L-Value inválido em atribuição")
            target_type = self._analyze_expression(expr.target)
            self._analyze_expression(expr.value)
            return target_type

        if isinstance(expr, FunctionCallNode):
            sym = self.symbol_table.lookup(expr.callee)
            if not sym or not sym.is_function:
                raise SemanticError(f"Chamada de função não declarada: '{expr.callee}'")
            if sym.param_types and len(expr.arguments) != len(sym.param_types):
                raise SemanticError(
                    f"Função '{expr.callee}' esperava {len(sym.param_types)} argumentos, mas recebeu {len(expr.arguments)}"
                )
            for arg in expr.arguments:
                self._analyze_expression(arg)
            return sym.type

        return IntType()
