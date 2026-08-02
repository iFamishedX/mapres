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
    # # LPAREN and RPAREN tokens were deprecated in mapres 3-dev.27 to fix a bug in the parser that caused it to fail on nested calls
    # LPAREN = auto()
    # RPAREN = auto()


class Token:
    def __init__(self, type_, value=None, pos=0):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self):
        if self.value is not None:
            return f'Token({self.type}, {self.value!r}, pos={self.pos})'
        return f'Token({self.type}, pos={self.pos})'


class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)
        self.tokens: list[Token] = []

    def peek(self, k: int = 0) -> str:
        idx = self.i + k
        if idx >= self.n:
            return ''
        return self.text[idx]

    def advance(self, k: int = 1) -> None:
        self.i += k

    def match(self, s: str) -> bool:
        return self.text.startswith(s, self.i)

    def emit(self, type_, value=None) -> None:
        self.tokens.append(Token(type_, value, self.i))

    def tokenize(self) -> list[Token]:
        buf: list[str] = []

        def flush_text():
            if buf:
                self.emit(TokenType.TEXT, ''.join(buf))
                buf.clear()

        while self.i < self.n:
            ch = self.peek()

            # escapes
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

            # --- {{IDENT}} ---
            if self.match('{{'):
                flush_text()
                start = self.i
                self.advance(2)
                ident = self._read_ident()
                if ident is not None and self.match('}}'):
                    self.emit(TokenType.BRACE_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance(2)
                    self.emit(TokenType.BRACE_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # --- ${IDENT} ---
            if self.match('${'):
                flush_text()
                start = self.i
                self.advance(2)
                ident = self._read_ident()
                if ident is not None and self.peek() == '}':
                    self.emit(TokenType.DOLLAR_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance()
                    self.emit(TokenType.DOLLAR_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # --- $(IDENT) ---
            if self.match('$('):
                flush_text()
                start = self.i
                self.advance(2)
                ident = self._read_ident()
                if ident is not None and self.peek() == ')':
                    self.emit(TokenType.DOLLAR_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance()
                    self.emit(TokenType.DOLLAR_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # --- <IDENT> ---
            if ch == '<':
                flush_text()
                start = self.i
                self.advance()
                ident = self._read_ident()
                if ident is not None and self.peek() == '>':
                    self.emit(TokenType.ANGLE_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance()
                    self.emit(TokenType.ANGLE_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # --- |IDENT| ---
            if ch == '|':
                flush_text()
                start = self.i
                self.advance()
                ident = self._read_ident()
                if ident is not None and self.peek() == '|':
                    self.emit(TokenType.PIPE_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance()
                    self.emit(TokenType.PIPE_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # --- %IDENT% ---
            if ch == '%':
                flush_text()
                start = self.i
                self.advance()
                ident = self._read_ident()
                if ident is not None and self.peek() == '%':
                    self.emit(TokenType.PERCENT_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance()
                    self.emit(TokenType.PERCENT_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # --- :IDENT: ---
            if ch == ':':
                flush_text()
                start = self.i
                self.advance()
                ident = self._read_ident()
                if ident is not None and self.peek() == ':':
                    self.emit(TokenType.COLON_OPEN)
                    self.emit(TokenType.IDENT, ident)
                    self.advance()
                    self.emit(TokenType.COLON_CLOSE)
                    continue
                self.i = start
                buf.append(self.peek())
                self.advance()
                continue

            # # --- parens --- (This block was deprecated in mapres 3-dev.27)
            # if ch == '(':
            #     flush_text()
            #     self.emit(TokenType.LPAREN)
            #     self.advance()
            #     continue

            # if ch == ')':
            #     flush_text()
            #     self.emit(TokenType.RPAREN)
            #     self.advance()
            #     continue

            # fallback TEXT
            buf.append(ch)
            self.advance()

        flush_text()
        return self.tokens

    def _read_ident(self) -> str | None:
        start = self.i
        ch = self.peek()
        if not ch or not ch.isalnum():
            return None

        self.advance()
        while True:
            nxt = self.peek()
            if not nxt:
                break
            if nxt.isalnum() or nxt in '._':
                self.advance()
            else:
                break

        ident = self.text[start:self.i]
        if ident.startswith('_') or ident.endswith('_') or '-' in ident:
            return None
        return ident
