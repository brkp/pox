# coding: utf-8

from .token import Token, TokenType
from result import Ok, Err, Result

class Scanner:
    line = 1
    start = 0
    current = 0

    def __init__(self, source: str):
        self.source = source
        self.eof_token = False

    def __iter__(self):
        return self

    def __next__(self) -> Result[Token, str]:
        self.start = self.current

        if self.eof_token:
            raise StopIteration

        if self.is_at_end():
            self.eof_token = True
            return Ok(Token(TokenType.EOF, "", None, self.line))

        return self.scan_token()

    def scan_token(self) -> Result[Token, str]:
        match c := self.advance():
            case '(': return Ok(self.make_token(TokenType.LEFT_PAREN))
            case ')': return Ok(self.make_token(TokenType.RIGHT_PAREN))
            case '{': return Ok(self.make_token(TokenType.LEFT_BRACE))
            case '}': return Ok(self.make_token(TokenType.RIGHT_BRACE))
            case ',': return Ok(self.make_token(TokenType.COMMA))
            case '.': return Ok(self.make_token(TokenType.DOT))
            case '+': return Ok(self.make_token(TokenType.PLUS))
            case '-': return Ok(self.make_token(TokenType.MINUS))
            case '*': return Ok(self.make_token(TokenType.STAR))
            case '/': return Ok(self.make_token(TokenType.SLASH))

            case _:
                return Err(f'{self.line} | unexpected character: {repr(c)}')

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self) -> str:
        try:
            return self.source[self.current]
        finally:
            self.current += 1

    def make_token(self, type, literal=None) -> Token:
        return Token(type, self.source[self.start:self.current], literal, self.line)
