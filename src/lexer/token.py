"""
Definição dos tipos de tokens e da estrutura Token do Lexer de C.
"""
from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    # Fim de arquivo
    EOF = auto()

    # Literais e Identificadores
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    CHAR_LITERAL = auto()
    STRING_LITERAL = auto()

    # Palavras-chave C
    INT = auto()
    CHAR = auto()
    VOID = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    STRUCT = auto()
    SIZEOF = auto()

    # Operadores Aritméticos e Unários
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    PERCENT = auto()        # %
    AMPERSAND = auto()      # &
    TILDE = auto()          # ~
    BANG = auto()           # !
    INCREMENT = auto()      # ++
    DECREMENT = auto()      # --

    # Operadores de Comparação e Lógicos
    EQ_EQ = auto()          # ==
    BANG_EQ = auto()        # !=
    LESS = auto()           # <
    LESS_EQ = auto()        # <=
    GREATER = auto()        # >
    GREATER_EQ = auto()     # >=
    AND_AND = auto()        # &&
    OR_OR = auto()          # ||

    # Operadores de Atribuição
    ASSIGN = auto()         # =
    PLUS_ASSIGN = auto()    # +=
    MINUS_ASSIGN = auto()   # -=

    # Pontuação e Delimitadores
    SEMICOLON = auto()      # ;
    COMMA = auto()          # ,
    DOT = auto()            # .
    ARROW = auto()          # ->
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]


KEYWORDS = {
    "int": TokenType.INT,
    "char": TokenType.CHAR,
    "void": TokenType.VOID,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "struct": TokenType.STRUCT,
    "sizeof": TokenType.SIZEOF,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, value={self.value!r}, line={self.line}, col={self.column})"
