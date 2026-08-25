"""
Construtor de IR: converte nós da AST em instruções Three-Address Code (TAC).
"""
from typing import List
from src.parser.ast_nodes import (
    ProgramNode, FunctionDefNode, BlockStmtNode, StmtNode,
    ReturnStmtNode, VarDeclStmtNode, IfStmtNode, WhileStmtNode,
    ExprStmtNode, ExprNode, BinaryOpNode, UnaryOpNode,
    AssignNode, FunctionCallNode, IdentifierNode, IntLiteralNode,
    AddressOfNode, DerefNode
)
from src.ir.ir_nodes import (
    IRProgram, IRFunction, IRInstruction, IRConst, IRCopy,
    IRBinary, IRUnary, IRJump, IRJumpIfZero, IRReturn, IRCall, IRLabel,
    IRAddressOf, IRLoad, IRStore
)

class IRBuilder:
    """Traduz a AST em sequência linear de instruções IR."""

    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.current_instructions: List[IRInstruction] = []

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _new_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def _emit(self, instr: IRInstruction) -> None:
        self.current_instructions.append(instr)

    def build(self, ast: ProgramNode) -> IRProgram:
        functions = []
        for func_def in ast.functions:
            functions.append(self._build_function(func_def))
        return IRProgram(functions=functions)

    def _build_function(self, func: FunctionDefNode) -> IRFunction:
        self.current_instructions = []
        params = [p.name for p in func.params]

        for stmt in func.body.statements:
            self._build_statement(stmt)

        if not self.current_instructions or not isinstance(self.current_instructions[-1], IRReturn):
            zero_temp = self._new_temp()
            self._emit(IRConst(dst=zero_temp, value=0))
            self._emit(IRReturn(value=zero_temp))

        return IRFunction(name=func.name, params=params, instructions=list(self.current_instructions))

    def _build_statement(self, stmt: StmtNode) -> None:
        if isinstance(stmt, ReturnStmtNode):
            if stmt.expr:
                res = self._build_expression(stmt.expr)
                self._emit(IRReturn(value=res))
            else:
                self._emit(IRReturn(value=None))
            return

        if isinstance(stmt, VarDeclStmtNode):
            if stmt.init_expr:
                val = self._build_expression(stmt.init_expr)
                self._emit(IRCopy(dst=stmt.name, src=val))
            return

        if isinstance(stmt, ExprStmtNode):
            self._build_expression(stmt.expr)
            return

        if isinstance(stmt, IfStmtNode):
            cond_val = self._build_expression(stmt.condition)
            else_label = self._new_label("else") if stmt.else_branch else None
            end_label = self._new_label("endif")

            if else_label:
                self._emit(IRJumpIfZero(condition=cond_val, target=else_label))
                self._build_statement(stmt.then_branch)
                self._emit(IRJump(target=end_label))
                self._emit(IRLabel(name=else_label))
                if stmt.else_branch:
                    self._build_statement(stmt.else_branch)
                self._emit(IRLabel(name=end_label))
            else:
                self._emit(IRJumpIfZero(condition=cond_val, target=end_label))
                self._build_statement(stmt.then_branch)
                self._emit(IRLabel(name=end_label))
            return

        if isinstance(stmt, WhileStmtNode):
            loop_start = self._new_label("loop_start")
            loop_end = self._new_label("loop_end")

            self._emit(IRLabel(name=loop_start))
            cond_val = self._build_expression(stmt.condition)
            self._emit(IRJumpIfZero(condition=cond_val, target=loop_end))
            self._build_statement(stmt.body)
            self._emit(IRJump(target=loop_start))
            self._emit(IRLabel(name=loop_end))
            return

        if isinstance(stmt, BlockStmtNode):
            for s in stmt.statements:
                self._build_statement(s)
            return

    def _build_expression(self, expr: ExprNode) -> str:
        if isinstance(expr, IntLiteralNode):
            t = self._new_temp()
            self._emit(IRConst(dst=t, value=expr.value))
            return t

        if isinstance(expr, IdentifierNode):
            return expr.name

        if isinstance(expr, AddressOfNode):
            src_name = self._build_expression(expr.operand)
            t = self._new_temp()
            self._emit(IRAddressOf(dst=t, src=src_name))
            return t

        if isinstance(expr, DerefNode):
            ptr = self._build_expression(expr.operand)
            t = self._new_temp()
            self._emit(IRLoad(dst=t, ptr=ptr))
            return t

        if isinstance(expr, AssignNode):
            rhs = self._build_expression(expr.value)
            if isinstance(expr.target, IdentifierNode):
                self._emit(IRCopy(dst=expr.target.name, src=rhs))
                return expr.target.name
            elif isinstance(expr.target, DerefNode):
                ptr = self._build_expression(expr.target.operand)
                self._emit(IRStore(ptr=ptr, src=rhs))
                return rhs
            t = self._new_temp()
            self._emit(IRCopy(dst=t, src=rhs))
            return t

        if isinstance(expr, BinaryOpNode):
            left = self._build_expression(expr.left)
            right = self._build_expression(expr.right)
            t = self._new_temp()
            self._emit(IRBinary(op=expr.op, dst=t, left=left, right=right))
            return t

        if isinstance(expr, UnaryOpNode):
            src = self._build_expression(expr.operand)
            t = self._new_temp()
            self._emit(IRUnary(op=expr.op, dst=t, src=src))
            return t

        if isinstance(expr, FunctionCallNode):
            arg_temps = [self._build_expression(arg) for arg in expr.arguments]
            t = self._new_temp()
            self._emit(IRCall(dst=t, func_name=expr.callee, args=arg_temps))
            return t

        return ""
