"""
Definição de nós da Árvore de Sintaxe Abstrata (AST) para o compilador de C.
"""
from dataclasses import dataclass
from typing import List, Optional

class ASTNode:
    """Classe base para todos os nós da AST."""
    pass

# --- Expressões ---

@dataclass
class ExprNode(ASTNode):
    pass

@dataclass
class IntLiteralNode(ExprNode):
    value: int

@dataclass
class StringLiteralNode(ExprNode):
    value: str

@dataclass
class IdentifierNode(ExprNode):
    name: str

@dataclass
class BinaryOpNode(ExprNode):
    op: str
    left: ExprNode
    right: ExprNode

@dataclass
class UnaryOpNode(ExprNode):
    op: str
    operand: ExprNode

@dataclass
class AssignNode(ExprNode):
    target: ExprNode
    value: ExprNode

@dataclass
class FunctionCallNode(ExprNode):
    callee: str
    arguments: List[ExprNode]

@dataclass
class AddressOfNode(ExprNode):
    operand: ExprNode

@dataclass
class DerefNode(ExprNode):
    operand: ExprNode


# --- Instruções / Statements ---

@dataclass
class StmtNode(ASTNode):
    pass

@dataclass
class ExprStmtNode(StmtNode):
    expr: ExprNode

@dataclass
class ReturnStmtNode(StmtNode):
    expr: Optional[ExprNode]

@dataclass
class BlockStmtNode(StmtNode):
    statements: List[StmtNode]

@dataclass
class IfStmtNode(StmtNode):
    condition: ExprNode
    then_branch: StmtNode
    else_branch: Optional[StmtNode] = None

@dataclass
class WhileStmtNode(StmtNode):
    condition: ExprNode
    body: StmtNode

@dataclass
class ForStmtNode(StmtNode):
    init: Optional[StmtNode]
    condition: Optional[ExprNode]
    post: Optional[ExprNode]
    body: StmtNode

@dataclass
class VarDeclStmtNode(StmtNode):
    type_name: str
    name: str
    init_expr: Optional[ExprNode] = None


# --- Declarações de Alto Nível ---

@dataclass
class ParamNode(ASTNode):
    type_name: str
    name: str

@dataclass
class FunctionDefNode(ASTNode):
    return_type: str
    name: str
    params: List[ParamNode]
    body: BlockStmtNode

@dataclass
class ProgramNode(ASTNode):
    functions: List[FunctionDefNode]
