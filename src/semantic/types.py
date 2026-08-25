"""
Sistema de tipos estáticos da linguagem C.
"""
from dataclasses import dataclass

class CType:
    """Classe base para tipos de dados em C."""
    def size(self) -> int:
        raise NotImplementedError

    def is_pointer(self) -> bool:
        return False

    def is_integer(self) -> bool:
        return False


class IntType(CType):
    def size(self) -> int:
        return 4

    def is_integer(self) -> bool:
        return True

    def __repr__(self) -> str:
        return "int"


class CharType(CType):
    def size(self) -> int:
        return 1

    def is_integer(self) -> bool:
        return True

    def __repr__(self) -> str:
        return "char"


class VoidType(CType):
    def size(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "void"


@dataclass
class PointerType(CType):
    base_type: CType

    def size(self) -> int:
        return 8

    def is_pointer(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"{self.base_type}*"
