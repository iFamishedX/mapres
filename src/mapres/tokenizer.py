from enum import Enum, auto


class TokenType(Enum):
    TEXT = auto()
    IDENT = auto()
    COLON_OPEN = auto()
    COLON_CLOSE = auto()
    BRACE_OPEN = auto()
    BRACE_CLOSE = auto()
    DOLLAR_OPEN = auto()
    DOLLAR_CLOSE = auto()
    ANGLE_OPEN = auto()
    ANGLE_CLOSE = auto()
    PIPE_OPEN = auto()
    PIPE_CLOSE = auto()
    PERCENT_OPEN = auto()
    PERCENT_CLOSE = auto()
    LPAREN = auto()
    RPAREN = auto()


class Token:
    def __init__(self, type_, value=None, pos=0):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self):
        if self.value is not None:
            return f"Token({self.type}, {self.value!r}, pos={self.pos})"
        return f"Token({self.type}, pos={self.pos})"


class Tokenizer:
    def __init__(self, text):
        self.text = text
        self.i = 0
        self.n = len(text)
        self.tokens = []
        self.in_pipe = False
        self.in_percent = False
        self.in_colon = False

    def peek(self, k=0):
        idx = self.i + k
        if idx >= self.n:
            return ''
        return self.text[idx]

    def advance(self, k=1):
        self.i += k

    def match(self, s):
        return self.text.startswith(s, self.i)

    def emit(self, type_, value=None):
        self.tokens.append(Token(type_, value, self.i))

    def tokenize(self):
        buf = []

        def flush_text():
            if buf:
                self.emit(TokenType.TEXT, ''.join(buf))
                buf.clear()

        while self.i < self.n:
            ch = self.peek()

            if self.match(r'\:'):
                buf.append(':'); self.advance(2); continue
            if self.match(r'\<'):
                buf.append('<'); self.advance(2); continue
            if self.match(r'\>'):
                buf.append('>'); self.advance(2); continue
            if self.match(r'\%'):
                buf.append('%'); self.advance(2); continue
            if self.match(r'\$'):
                buf.append('$'); self.advance(2); continue
            if self.match(r'\{'):
                buf.append('{'); self.advance(2); continue
            if self.match(r'\}'):
                buf.append('}'); self.advance(2); continue
            if self.match(r'\|'):
                buf.append('|'); self.advance(2); continue
            if self.match(r'\('):
                buf.append('('); self.advance(2); continue
            if self.match(r'\)'):
                buf.append(')'); self.advance(2); continue

            if self.match("{{"):
                flush_text()
                self.emit(TokenType.BRACE_OPEN)
                self.advance(2)
                continue

            if self.match("}}"):
                flush_text()
                self.emit(TokenType.BRACE_CLOSE)
                self.advance(2)
                continue

            if self.match("${"):
                flush_text()
                self.emit(TokenType.DOLLAR_OPEN)
                self.advance(2)
                continue

            if self.match("}"):
                flush_text()
                self.emit(TokenType.DOLLAR_CLOSE)
                self.advance()
                continue

            if self.match("<"):
                flush_text()
                self.emit(TokenType.ANGLE_OPEN)
                self.advance()
                continue

            if self.match(">"):
                flush_text()
                self.emit(TokenType.ANGLE_CLOSE)
                self.advance()
                continue

            if self.match("|"):
                flush_text()
                if not self.in_pipe:
                    self.emit(TokenType.PIPE_OPEN)
                    self.in_pipe = True
                else:
                    self.emit(TokenType.PIPE_CLOSE)
                    self.in_pipe = False
                self.advance()
                continue

            if self.match("%"):
                flush_text()
                if not self.in_percent:
                    self.emit(TokenType.PERCENT_OPEN)
                    self.in_percent = True
                else:
                    self.emit(TokenType.PERCENT_CLOSE)
                    self.in_percent = False
                self.advance()
                continue

            if self.match(":"):
                flush_text()
                if not self.in_colon:
                    self.emit(TokenType.COLON_OPEN)
                    self.in_colon = True
                else:
                    self.emit(TokenType.COLON_CLOSE)
                    self.in_colon = False
                self.advance()
                continue

            if ch == "(":
                flush_text()
                self.emit(TokenType.LPAREN)
                self.advance()
                continue

            if ch == ")":
                flush_text()
                self.emit(TokenType.RPAREN)
                self.advance()
                continue

            if ch.isalpha():
                flush_text()
                start = self.i
                while self.peek().isalnum() or self.peek() in "._":
                    self.advance()
                ident = self.text[start:self.i]
                self.emit(TokenType.IDENT, ident)
                continue

            buf.append(ch)
            self.advance()

        flush_text()
        return self.tokens
