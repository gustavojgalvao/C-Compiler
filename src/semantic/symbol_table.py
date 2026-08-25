"""
Gerenciamento de Tabela de Símbolos e Escopos aninhados.
"""
from dataclasses import dataclass
from typing import Dict, Optional, List
from src.semantic.types import CType

@dataclass
class Symbol:
    name: str
    type: CType
    is_function: bool = False
    param_types: Optional[List[CType]] = None
    stack_offset: int = 0


class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None


class SymbolTable:
    def __init__(self):
        self.global_scope = Scope()
        self.current_scope = self.global_scope

    def enter_scope(self) -> None:
        self.current_scope = Scope(parent=self.current_scope)

    def exit_scope(self) -> None:
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define(self, symbol: Symbol) -> bool:
        return self.current_scope.define(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup(name)
