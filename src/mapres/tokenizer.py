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
                # ident == None means _read_ident already emitted IDENT and nested tokens
                if ident is None:
                    # nested call already emitted; expect closing '}}'
                    if self.match('}}'):
                        self.advance(2)
                        self.emit(TokenType.BRACE_CLOSE)
                        continue
                    # fallback to literal
                    self.i = start
                    buf.append(self.peek())
                    self.advance()
                    continue
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
                if ident is None:
                    # nested call already emitted; expect closing '}'
                    if self.peek() == '}':
                        self.advance()
                        self.emit(TokenType.DOLLAR_CLOSE)
                        continue
                    self.i = start
                    buf.append(self.peek())
                    self.advance()
                    continue
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
                if ident is None:
                    # nested call already emitted; expect closing '>'
                    if self.peek() == '>':
                        self.advance()
                        self.emit(TokenType.ANGLE_CLOSE)
                        continue
                    self.i = start
                    buf.append(self.peek())
                    self.advance()
                    continue
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
                if ident is None:
                    # nested call already emitted; expect closing '|'
                    if self.peek() == '|':
                        self.advance()
                        self.emit(TokenType.PIPE_CLOSE)
                        continue
                    self.i = start
                    buf.append(self.peek())
                    self.advance()
                    continue
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
                if ident is None:
                    # nested call already emitted; expect closing '%'
                    if self.peek() == '%':
                        self.advance()
                        self.emit(TokenType.PERCENT_CLOSE)
                        continue
                    self.i = start
                    buf.append(self.peek())
                    self.advance()
                    continue
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
                if ident is None:
                    # nested call already emitted; expect closing ':'
                    if self.peek() == ':':
                        self.advance()
                        self.emit(TokenType.COLON_CLOSE)
                        continue
                    self.i = start
                    buf.append(self.peek())
                    self.advance()
                    continue
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

        # unified nested-call support: if '(' immediately follows the ident,
        # emit IDENT + LPAREN + nested TEXT + RPAREN and return None.
        if self.peek() == '(':
            # emit IDENT token
            self.emit(TokenType.IDENT, ident)

            # consume '(' and emit LPAREN
            self.advance()
            self.emit(TokenType.LPAREN)

            # capture nested content as TEXT until the next ')'
            nested_start = self.i
            while self.peek() not in (')', ''):
                self.advance()
            nested_text = self.text[nested_start:self.i]
            if nested_text:
                self.emit(TokenType.TEXT, nested_text)

            # consume ')' and emit RPAREN if present
            if self.peek() == ')':
                self.advance()
                self.emit(TokenType.RPAREN)

            # signal to caller that tokens were emitted already
            return None

        # no nested call; return the identifier string
        return ident
