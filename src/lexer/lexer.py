"""
Analisador Léxico (Lexer / Tokenizer) para o subconjunto de C.
"""
from typing import List, Optional
from src.lexer.token import Token, TokenType, KEYWORDS
from src.utils.errors import LexerError

class Lexer:
    """Converte código-fonte C em uma lista ordenada de Tokens."""

    def __init__(self, source: str):
        self.source = source
        self.cursor = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def _peek(self, offset: int = 0) -> Optional[str]:
        pos = self.cursor + offset
        if pos < self.length:
            return self.source[pos]
        return None

    def _advance(self) -> Optional[str]:
        ch = self._peek()
        if ch is not None:
            self.cursor += 1
            if ch == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return ch

    def _skip_whitespace_and_comments(self) -> None:
        while self.cursor < self.length:
            ch = self._peek()
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
            elif ch == '/' and self._peek(1) == '/':
                while self.cursor < self.length and self._peek() != '\n':
                    self._advance()
            elif ch == '/' and self._peek(1) == '*':
                self._advance()
                self._advance()
                while self.cursor < self.length:
                    if self._peek() == '*' and self._peek(1) == '/':
                        self._advance()
                        self._advance()
                        break
                    self._advance()
                else:
                    raise LexerError("Comentário de bloco não finalizado", self.line, self.column)
            else:
                break

    def _read_number(self, start_line: int, start_col: int) -> Token:
        digits = []
        is_hex = False
        if self._peek() == '0' and self._peek(1) in ('x', 'X'):
            digits.append(self._advance())
            digits.append(self._advance())
            is_hex = True

        while self.cursor < self.length:
            ch = self._peek()
            if ch and (ch.isdigit() or (is_hex and ch.lower() in "abcdef")):
                digits.append(self._advance())
            else:
                break
        return Token(TokenType.INT_LITERAL, "".join(digits), start_line, start_col)

    def _read_identifier_or_keyword(self, start_line: int, start_col: int) -> Token:
        chars = []
        while self.cursor < self.length:
            ch = self._peek()
            if ch and (ch.isalnum() or ch == '_'):
                chars.append(self._advance())
            else:
                break
        value = "".join(chars)
        token_type = KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, start_line, start_col)

    def _read_char_literal(self, start_line: int, start_col: int) -> Token:
        self._advance()
        if self._peek() == '\\':
            self._advance()
            escape = self._advance()
            val = "\\" + str(escape)
        else:
            val = self._advance()
        
        if self._peek() != "'":
            raise LexerError("Literal de caractere não finalizado com aspas simples", start_line, start_col)
        self._advance()
        return Token(TokenType.CHAR_LITERAL, str(val), start_line, start_col)

    def _read_string_literal(self, start_line: int, start_col: int) -> Token:
        self._advance()
        chars = []
        while self.cursor < self.length and self._peek() != '"':
            ch = self._advance()
            if ch == '\\':
                chars.append(ch)
                chars.append(self._advance())
            else:
                chars.append(ch)
        if self._peek() != '"':
            raise LexerError("String literal não finalizada com aspas duplas", start_line, start_col)
        self._advance()
        return Token(TokenType.STRING_LITERAL, "".join(chars), start_line, start_col)

    def tokenize(self) -> List[Token]:
        """Varre o código e gera a lista de tokens."""
        tokens = []

        while self.cursor < self.length:
            self._skip_whitespace_and_comments()
            if self.cursor >= self.length:
                break

            start_line = self.line
            start_col = self.column
            ch = self._peek()

            if ch.isdigit():
                tokens.append(self._read_number(start_line, start_col))
            elif ch.isalpha() or ch == '_':
                tokens.append(self._read_identifier_or_keyword(start_line, start_col))
            elif ch == "'":
                tokens.append(self._read_char_literal(start_line, start_col))
            elif ch == '"':
                tokens.append(self._read_string_literal(start_line, start_col))
            elif ch == '+':
                self._advance()
                if self._peek() == '+':
                    self._advance()
                    tokens.append(Token(TokenType.INCREMENT, "++", start_line, start_col))
                elif self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
            elif ch == '-':
                self._advance()
                if self._peek() == '-':
                    self._advance()
                    tokens.append(Token(TokenType.DECREMENT, "--", start_line, start_col))
                elif self._peek() == '>':
                    self._advance()
                    tokens.append(Token(TokenType.ARROW, "->", start_line, start_col))
                elif self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
            elif ch == '*':
                self._advance()
                tokens.append(Token(TokenType.STAR, "*", start_line, start_col))
            elif ch == '/':
                self._advance()
                tokens.append(Token(TokenType.SLASH, "/", start_line, start_col))
            elif ch == '%':
                self._advance()
                tokens.append(Token(TokenType.PERCENT, "%", start_line, start_col))
            elif ch == '=':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.EQ_EQ, "==", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch == '!':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.BANG_EQ, "!=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.BANG, "!", start_line, start_col))
            elif ch == '<':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.LESS_EQ, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LESS, "<", start_line, start_col))
            elif ch == '>':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.GREATER_EQ, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GREATER, ">", start_line, start_col))
            elif ch == '&':
                self._advance()
                if self._peek() == '&':
                    self._advance()
                    tokens.append(Token(TokenType.AND_AND, "&&", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.AMPERSAND, "&", start_line, start_col))
            elif ch == '|':
                self._advance()
                if self._peek() == '|':
                    self._advance()
                    tokens.append(Token(TokenType.OR_OR, "||", start_line, start_col))
                else:
                    raise LexerError(f"Operador binário bit a bit | não suportado", start_line, start_col)
            elif ch == '~':
                self._advance()
                tokens.append(Token(TokenType.TILDE, "~", start_line, start_col))
            elif ch == ';':
                self._advance()
                tokens.append(Token(TokenType.SEMICOLON, ";", start_line, start_col))
            elif ch == ',':
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == '.':
                self._advance()
                tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
            elif ch == '(':
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ')':
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == '{':
                self._advance()
                tokens.append(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == '}':
                self._advance()
                tokens.append(Token(TokenType.RBRACE, "}", start_line, start_col))
            elif ch == '[':
                self._advance()
                tokens.append(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == ']':
                self._advance()
                tokens.append(Token(TokenType.RBRACKET, "]", start_line, start_col))
            else:
                invalid_ch = self._advance()
                raise LexerError(f"Caractere inesperado: {invalid_ch!r}", start_line, start_col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
