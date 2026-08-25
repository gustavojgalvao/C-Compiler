"""Módulo de utilitários."""
from .errors import CompilerError, LexerError, ParserError, SemanticError, CodeGenError
from .diagnostics import format_error_snippet

__all__ = [
    "CompilerError",
    "LexerError",
    "ParserError",
    "SemanticError",
    "CodeGenError",
    "format_error_snippet"
]
