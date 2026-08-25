"""
Definições de exceções personalizadas para cada etapa do compilador.
"""

class CompilerError(Exception):
    """Exceção base para todos os erros do compilador."""
    def __init__(self, message: str, line: int = 1, column: int = 1):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"Erro [Linha {self.line}, Coluna {self.column}]: {self.message}"


class LexerError(CompilerError):
    """Erro emitido durante a análise léxica."""
    pass


class ParserError(CompilerError):
    """Erro emitido durante a análise sintática."""
    pass


class SemanticError(CompilerError):
    """Erro emitido durante a análise semântica."""
    pass


class CodeGenError(CompilerError):
    """Erro emitido durante a geração de código."""
    pass
